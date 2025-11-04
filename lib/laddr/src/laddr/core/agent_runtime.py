"""
Agent runtime core implementation.

Provides Agent base class with planning, execution, tool calling,
delegation, memory, caching, and auto-registration on message bus.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import hashlib
import json
import time
from typing import Any
import uuid
import logging

from .config import AgentConfig, BackendFactory, LaddrConfig
from .tooling import ToolRegistry, discover_tools
import os

# Module logger
logger = logging.getLogger(__name__)


@dataclass
class AgentMemory:
    """Memory interface for agents."""

    agent_name: str
    database: Any  # DatabaseService
    job_id: str | None = None

    def put(self, key: str, value: Any) -> None:
        """Store a memory entry."""
        self.database.memory_put(self.agent_name, key, value, self.job_id)

    def get(self, key: str) -> Any:
        """Retrieve a memory entry."""
        return self.database.memory_get(self.agent_name, key, self.job_id)

    def list(self) -> dict[str, Any]:
        """List all memory entries."""
        return self.database.memory_list(self.agent_name, self.job_id)


class Agent:
    """
    Base Agent class with full runtime capabilities.
    
    Provides:
    - Planning and execution
    - Tool calling with validation and caching
    - Delegation with blocking wait for responses
    - Memory storage
    - Auto-registration on message bus
    - Trace logging to database
    
    Subclasses should override plan() method for custom planning logic,
    or use the default autonomous_run() for intelligent LLM-driven execution.
    """

    # Class-level metadata (set by @actor decorator or subclass)
    ROLE: str = "agent"
    GOAL: str = "Complete assigned tasks"

    def __init__(
        self,
        config: AgentConfig,
        env_config: LaddrConfig | None = None,
        tools: ToolRegistry | list[Any] | None = None,
        *,
        llm: Any | None = None,
        queue: Any | None = None,
        instructions: str | None = None,
        is_coordinator: bool | None = None,
        available_agents: list[str] | None = None,
    ):
        """
        Initialize agent.
        
        Args:
            config: Agent-specific configuration
            env_config: Environment configuration (loaded if None)
            tools: Tool registry (auto-discovered if None)
        """
        self.config = config
        self.env_config = env_config or LaddrConfig()

        # Create backends (allow explicit overrides for llm and queue)
        self.factory = BackendFactory(self.env_config)
        # Queue override
        if queue is not None:
            try:
                # Direct bus instance (RedisBus/MemoryBus)
                if hasattr(queue, "publish_task") and hasattr(queue, "consume_tasks"):
                    self.bus = queue
                # Wrapper with uri attribute (e.g., RedisQueue from laddr.queues)
                elif hasattr(queue, "uri"):
                    from .message_bus import RedisBus
                    self.bus = RedisBus(getattr(queue, "uri"))
                # String shorthand
                elif isinstance(queue, str) and queue.startswith("redis://"):
                    from .message_bus import RedisBus
                    self.bus = RedisBus(queue)
                else:
                    self.bus = self.factory.create_queue_backend()
            except Exception:
                self.bus = self.factory.create_queue_backend()
        else:
            self.bus = self.factory.create_queue_backend()

        self.database = self.factory.create_database_backend()

        # LLM override
        if llm is not None:
            self.llm = llm
        else:
            self.llm = self.factory.create_llm_backend()
        # Default LLM params (temperature, max_tokens, etc.) optionally provided by llm wrapper
        self._llm_params: dict = {}
        try:
            if hasattr(self.llm, "default_params") and isinstance(self.llm.default_params, dict):  # type: ignore[attr-defined]
                self._llm_params = dict(self.llm.default_params)  # type: ignore[attr-defined]
        except Exception:
            self._llm_params = {}
        self.cache_backend = self.factory.create_cache_backend()
        self.storage = self.factory.create_storage_backend()

        # Coordinator support (allow explicit override)
        # Set this BEFORE tool registration so _register_system_tools can check it
        self.is_coordinator = (
            bool(is_coordinator)
            if is_coordinator is not None
            else (getattr(self.env_config, "has_coordinator", False) and (
                self.config.name == getattr(self.env_config, "coordinator_agent", "coordinator")
            ))
        )
        self.coordinator_agent = (
            getattr(self.env_config, "coordinator_agent", "coordinator")
            if getattr(self.env_config, "has_coordinator", False)
            else None
        )
        # Available agents hint for prompts/planning
        self.available_agents_hint: list[str] = list(available_agents or [])
        # Agent-level instruction supplement
        self._extra_instructions: str | None = (instructions or None)

        # Tool registry - start with user tools, then add system tools
        if tools is None:
            self.tools = discover_tools(config.name)
        elif isinstance(tools, ToolRegistry):
            self.tools = tools
        else:
            # Accept list of callables and register
            from .tooling import ToolRegistry as _TR
            tr = _TR()
            for t in (tools or []):
                try:
                    tr.register(t)
                except Exception:
                    continue
            self.tools = tr

        # Add system tools for delegation and artifact storage
        # This is called AFTER is_coordinator is set
        self._register_system_tools()

        # Memory interface
        self.memory: AgentMemory | None = None

        # Current job context
        self.current_job_id: str | None = None

        # Tracing controls (configurable via @actor decorator class attributes)
        self._trace_enabled: bool = bool(getattr(self.__class__, "TRACE_ENABLED", True))
        mask = getattr(self.__class__, "TRACE_MASK", set()) or set()
        try:
            self._trace_mask: set[str] = set(mask)
        except Exception:
            self._trace_mask = set()

        # Heartbeat task
        self._heartbeat_task: asyncio.Task | None = None

    async def _llm_generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Generate with primary LLM.

        If the backend supports generate_with_usage, capture token usage and emit a trace
        event 'llm_usage' with provider/model and token counts for per-job accounting.
        """
        params = {**self._llm_params, **(kwargs or {})}
        
        try:
            # Prefer usage-aware API if available
            if hasattr(self.llm, "generate_with_usage"):
                text, usage = await self.llm.generate_with_usage(prompt, system=system, **params)  # type: ignore[attr-defined]
                # Trace usage if available
                try:
                    if isinstance(usage, dict):
                        payload = {
                            "provider": usage.get("provider"),
                            "model": usage.get("model"),
                            "prompt_tokens": usage.get("prompt_tokens"),
                            "completion_tokens": usage.get("completion_tokens"),
                            "total_tokens": usage.get("total_tokens"),
                            "worker": self.config.name,
                        }
                        self._trace(self.current_job_id or "unknown", self.config.name, "llm_usage", payload)
                except Exception:
                    pass
                return text
            # Fallback to text-only generation
            return await self.llm.generate(prompt, system=system, **params)
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")

    def _discover_tool_overrides(self):
        """
        Auto-discover and load tool override modules from the project.
        
        Searches common locations for tool override files:
        - ./tools/overrides/
        - ./custom_tools/
        - ./agent_tools/overrides/
        
        When override modules are imported, the @override_system_tool
        decorators will automatically register the overrides.
        """
        import importlib.util
        import os
        from pathlib import Path
        
        # Get workspace root (where laddr.yml is located)
        workspace_root = Path.cwd()
        if hasattr(self, 'config') and hasattr(self.config, 'project_root'):
            workspace_root = Path(self.config.project_root)
        
        # Search paths for override modules
        search_paths = [
            workspace_root / "tools" / "overrides",
            workspace_root / "custom_tools",
            workspace_root / "agent_tools" / "overrides",
        ]
        
        for search_path in search_paths:
            if not search_path.exists() or not search_path.is_dir():
                continue
            
            # Find all .py files in this directory
            for py_file in search_path.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue  # Skip __init__.py, etc.
                
                try:
                    # Import the module - this triggers @override_system_tool decorators
                    module_name = f"tool_overrides.{py_file.stem}"
                    spec = importlib.util.spec_from_file_location(module_name, py_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        logger.info(f"✅ Loaded tool override module: {py_file.name}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load tool override module {py_file.name}: {e}")

    def _register_system_tools(self):
        """Register built-in system tools for delegation and artifacts."""
        from .system_tools import create_system_tools
        from .tooling import Tool as _Tool
        
        # First, discover any user-provided tool overrides
        self._discover_tool_overrides()

        # Pass self (agent instance) so system tools can access current_job_id
        system_tools = create_system_tools(self.bus, self.storage, agent=self)

        # Disallow any system tool that could bypass delegation safeguards
        reserved = {"delegate", "publish", "publish_task"}
        
        # Delegation tools - only register for coordinator agents
        delegation_tools = {
            "system_delegate_task",
            "system_delegate_parallel", 
            "delegate_parallel",
            "system_split_document",
            "split_document"
        }

        for name, tool_data in system_tools.items():
            # Skip reserved/unsafe tool names
            if name in reserved:
                continue
            
            # Skip delegation tools for non-coordinator agents
            if name in delegation_tools and not self.is_coordinator:
                continue
            
            # Unpack tool data - can be either (func, aliases) or just func
            if isinstance(tool_data, tuple):
                func, aliases = tool_data
            else:
                func = tool_data
                aliases = []
            
            # Register each system tool with the explicit provided name,
            # not the callable's __name__, so both prefixed and alias names exist.
            if not self.tools.has(name):
                try:
                    desc = (func.__doc__ or "").strip().split("\n")[0]
                    tool = _Tool(name=name, func=func, description=desc)
                    self.tools.register(tool, name=name, aliases=aliases)
                except Exception:
                    # Fallback to direct registration
                    self.tools.register(func, name=name, aliases=aliases)

    async def connect_bus(self) -> None:
        """
        Connect to message bus and register agent.
        
        Starts heartbeat to maintain registration.
        """
        metadata = {
            "role": self.config.role or self.ROLE,
            "goal": self.config.goal or self.GOAL,
            "tools": self.tools.list_names(),
            "status": "active",
            "max_iterations": self.config.max_iterations,
            "allow_delegation": self.config.allow_delegation
        }

        await self.bus.register_agent(self.config.name, metadata)
        self.database.register_agent(self.config.name, metadata)

        # Start heartbeat
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self) -> None:
        """Periodic heartbeat to keep agent registered."""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                metadata = {
                    "role": self.config.role,
                    "goal": self.config.goal,
                    "tools": self.tools.list_names(),
                    "status": "active"
                }
                await self.bus.register_agent(self.config.name, metadata)
            except asyncio.CancelledError:
                break
            except Exception:
                continue

    async def shutdown(self) -> None:
        """Shutdown agent and cleanup."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Update status to inactive
        metadata = {
            "role": self.config.role,
            "goal": self.config.goal,
            "tools": self.tools.list_names(),
            "status": "inactive"
        }
        await self.bus.register_agent(self.config.name, metadata)

    def plan(self, task: dict) -> list[dict]:
        """
        Create execution plan for a task.
        
        Default implementation: simple single-step plan.
        Subclasses should override for custom planning logic.
        
        Args:
            task: Task inputs
        
        Returns:
            List of steps, where each step is a dict with:
            - action: "tool" | "delegate" | "llm" | "custom"
            - Additional fields depending on action type
        """
        # Default: single LLM call step
        return [
            {
                "action": "llm",
                "prompt": f"Task: {json.dumps(task)}",
                "system": f"You are {self.config.role}. Your goal: {self.config.goal}"
            }
        ]

    async def handle(self, task: dict) -> dict:
        """
        Handle a task: plan, execute, return result.
        
        This is the main entry point for task execution.
        
        By default, uses autonomous_run() for intelligent, LLM-driven execution.
        Override plan() method if you need custom hardcoded plans instead.
        
        Args:
            task: Task inputs
        
        Returns:
            Structured result dict with status and output
        """
        # Set up job context (support both job_id and prompt_id for compatibility)
        execution_id = task.get("prompt_id") or task.get("job_id") or str(uuid.uuid4())
        self.current_job_id = execution_id  # Keep internal name for now

        self.memory = AgentMemory(
            agent_name=self.config.name,
            database=self.database,
            job_id=execution_id
        )

        # Trace start (log as prompt_id for new terminology)
        from datetime import datetime as _dt
        task_started_at = _dt.utcnow().isoformat() + "Z"
        
        self._trace(
            execution_id,
            self.config.name,
            "task_start",
            {
                "inputs": task,
                "worker": self.config.name,
                "started_at": task_started_at
            }
        )

        try:
            # Check if plan() was overridden (custom planning logic)
            # If plan() is default implementation, use autonomous_run instead
            plan_method = self.__class__.plan
            base_plan_method = Agent.plan
            
            if plan_method is base_plan_method:
                # Use autonomous agent loop (intelligent, LLM-driven)
                # Extract execution limits from task (if provided by user)
                max_iterations = task.get("max_iterations")
                max_tool_calls = task.get("max_tool_calls")
                # Fall back to instance-level max_tool_calls if set
                if max_tool_calls is None and hasattr(self, "_max_tool_calls"):
                    max_tool_calls = self._max_tool_calls
                result = await self.autonomous_run(
                    task, 
                    max_iterations=max_iterations,
                    max_tool_calls=max_tool_calls
                )
            else:
                # Use custom plan (backward compatibility)
                plan = self.plan(task)
                
                self._trace(
                    execution_id,
                    self.config.name,
                    "plan_created",
                    {"plan": plan}
                )
                
                result = await self.execute_plan(plan, task)

            # Trace completion / final state
            task_ended_at = _dt.utcnow().isoformat() + "Z"
            try:
                self._trace(
                    execution_id,
                    self.config.name,
                    "task_complete",
                    {
                        "result": result,
                        "worker": self.config.name,
                        "ended_at": task_ended_at
                    }
                )
            except Exception:
                pass

            # If the agent returned a structured status, propagate it instead of
            # always returning "success". This preserves error/incomplete
            # semantics from autonomous_run() so the API can handle failures correctly.
            if isinstance(result, dict) and result.get("status"):
                res_status = result.get("status")

                # Auto-route specialist results to coordinator only on final success
                if res_status == "success" and not self.is_coordinator and self.coordinator_agent:
                    try:
                        await self.bus.publish_task(
                            self.coordinator_agent,
                            {
                                "type": "specialist_result",
                                "source_agent": self.config.name,
                                "job_id": execution_id,
                                "result": result
                            }
                        )
                    except Exception:
                        pass

                # Map statuses through
                if res_status == "error":
                    return {
                        "status": "error",
                        "error": result.get("error") or "error",
                        "result": result,
                        "job_id": execution_id,
                        "prompt_id": execution_id
                    }
                if res_status in {"incomplete", "canceled"}:
                    return {
                        "status": res_status,
                        "result": result,
                        "job_id": execution_id,
                        "prompt_id": execution_id
                    }

            # Default: treat as successful completion and return extracted payload
            outputs = result.get("result") if isinstance(result, dict) else result

            # Auto-route result to coordinator if applicable
            if not self.is_coordinator and self.coordinator_agent:
                try:
                    await self.bus.publish_task(
                        self.coordinator_agent,
                        {
                            "type": "specialist_result",
                            "source_agent": self.config.name,
                            "job_id": execution_id,
                            "result": outputs
                        }
                    )
                except Exception:
                    pass

            return {
                "status": "success",
                "result": outputs,
                "job_id": execution_id,
                "prompt_id": execution_id,
            }

        except Exception as e:
            # Trace error
            task_error_at = _dt.utcnow().isoformat() + "Z"
            self._trace(
                execution_id,
                self.config.name,
                "task_error",
                {
                    "error": str(e),
                    "worker": self.config.name,
                    "ended_at": task_error_at
                }
            )

            return {
                "status": "error",
                "error": str(e),
                "job_id": execution_id,
                "prompt_id": execution_id
            }

    async def execute_plan(self, plan: list[dict], task: dict) -> Any:
        """
        Execute a plan.
        
        Iterates through steps and executes each based on action type.
        
        Args:
            plan: List of steps
            task: Original task inputs
        
        Returns:
            Final result (from last step)
        """
        context = {"task": task}
        result = None

        for i, step in enumerate(plan):
            action = step.get("action")

            if action == "tool":
                result = await self._execute_tool_step(step, context)
            elif action == "delegate":
                result = await self._execute_delegate_step(step, context)
            elif action == "llm":
                result = await self._execute_llm_step(step, context)
            # elif action == "custom":
            #     result = await self._execute_custom_step(step, context)
            else:
                result = {"error": f"Unknown action: {action}"}

            context[f"step_{i}"] = result
            context["last"] = result

        return result

    async def _execute_tool_step(self, step: dict, context: dict) -> Any:
        """Execute a tool call step."""
        tool_name = step.get("name")
        params = step.get("params", {})
        use_cache = step.get("use_cache", True)

        return await self.call_tool(tool_name, params, use_cache=use_cache)

    async def _execute_delegate_step(self, step: dict, context: dict) -> Any:
        """
        Execute a delegation step.
        
        This method is for backward compatibility with custom plan() implementations.
        
        For modern autonomous_run() agents, delegation is non-blocking and uses
        pause/resume orchestration automatically.
        
        For legacy custom plans, set wait=True to block until response (old behavior).
        Set wait=False to delegate without waiting (fire-and-forget).
        """
        agent_name = step.get("agent")
        payload = step.get("payload", {})

        task_id = await self.delegate(agent_name, payload)

        # Optionally wait for response (BLOCKING - backward compatibility mode)
        wait = step.get("wait", False)
        if wait:
            timeout = step.get("timeout", 30)
            response = await self.bus.wait_for_response(task_id, timeout)
            return response or {"status": "pending", "task_id": task_id}

        return {"status": "delegated", "task_id": task_id}

    async def _execute_llm_step(self, step: dict, context: dict) -> Any:
        """Execute an LLM call step."""
        prompt = step.get("prompt", "")
        system = step.get("system")

        # Simple string replacement for context variables
        for key, value in context.items():
            try:
                rep = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            except Exception:
                rep = str(value)
            prompt = prompt.replace(f"{{{key}}}", rep)

        response = await self._llm_generate(prompt, system=system)
        return {"llm_response": response}

    # async def _execute_custom_step(self, step: dict, context: dict) -> Any:
    #     """Execute a custom step (override in subclass)."""
    #     return {"error": "Custom step not implemented"}

    async def call_tool(
        self,
        name: str,
        params: dict[str, Any],
        use_cache: bool = True
    ) -> Any:
        """
        Call a tool with validation, guardrails, and caching.
        
        Args:
            name: Tool name
            params: Tool parameters
            use_cache: Whether to use cache
        
        Returns:
            Tool execution result
        """
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        # Cache key
        cache_key = self._tool_cache_key(name, params)

        # Check cache
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached is not None:
                # Respect tool trace masking if tool metadata available
                try:
                    tool_meta = tool
                    if getattr(tool_meta, "trace_enabled", True) and "cache_hit" not in getattr(tool_meta, "trace_mask", set()):
                        self._trace(
                            self.current_job_id or "unknown",
                            self.config.name,
                            "cache_hit",
                            {"tool": name, "params": params}
                        )
                except Exception:
                    pass
                return cached

        # Validate inputs
        try:
            validated_params = tool.validate_inputs(params)
        except Exception as e:
            raise ValueError(f"Tool input validation failed: {e}")

        # Trace tool call if enabled
        from datetime import datetime as _dt
        started_at = _dt.utcnow().isoformat() + "Z"
        
        if getattr(tool, "trace_enabled", True) and "tool_call" not in getattr(tool, "trace_mask", set()):
            self._trace(
                self.current_job_id or "unknown",
                self.config.name,
                "tool_call",
                {
                    "tool": name,
                    "params": validated_params,
                    "worker": self.config.name,
                    "started_at": started_at
                }
            )

        # Execute
        start = time.time()
        try:
            # DEBUG: Check current_job_id before tool execution
            import sys
            print(f"[TOOL EXECUTION] Tool={name}, agent_id={id(self)}, agent_name={self.config.name}, agent.current_job_id={self.current_job_id}", file=sys.stderr, flush=True)
            
            # Inject current_job_id for system delegation tools if not already provided
            if name in ['system_delegate_task', 'system_delegate_parallel'] and 'parent_job_id' not in validated_params:
                validated_params['parent_job_id'] = self.current_job_id
                print(f"[TOOL INJECTION] Injecting parent_job_id={self.current_job_id} into {name}", file=sys.stderr, flush=True)
            
            result = tool.invoke(**validated_params)
            # If tool is async, await its result
            try:
                import inspect as _inspect
                if _inspect.isawaitable(result):
                    result = await result
            except Exception:
                # If inspection fails, proceed with returned value
                pass
            duration_ms = int((time.time() - start) * 1000)
            ended_at = _dt.utcnow().isoformat() + "Z"

            # Trace tool_result if enabled
            if getattr(tool, "trace_enabled", True) and "tool_result" not in getattr(tool, "trace_mask", set()):
                self._trace(
                    self.current_job_id or "unknown",
                    self.config.name,
                    "tool_result",
                    {
                        "tool": name,
                        "worker": self.config.name,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "duration_ms": duration_ms,
                        "status": "success",
                        # Store both a lightweight preview and the full result when reasonable
                        "result_preview": str(result)[:500] if result is not None else None,
                        "result": result
                    }
                )

            # Cache result
            if use_cache:
                await self._put_in_cache(cache_key, result, ttl=300)

            return result

        except Exception as e:
            ended_at = _dt.utcnow().isoformat() + "Z"
            duration_ms = int((time.time() - start) * 1000)
            self._trace(
                self.current_job_id or "unknown",
                self.config.name,
                "tool_error",
                {
                    "tool": name,
                    "worker": self.config.name,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "duration_ms": duration_ms,
                    "error": str(e)
                }
            )
            raise

    async def delegate(self, agent_name: str, payload: dict) -> str:
        """
        Delegate a task to another agent.
        
        Args:
            agent_name: Target agent name
            payload: Task payload
        
        Returns:
            Task ID for tracking
        """
        if not self.config.allow_delegation:
            raise ValueError("Delegation not allowed for this agent")

        # Strict validation: only delegate to active, registered agents
        try:
            # message_bus exposes get_registered_agents() -> dict[name] = metadata
            registry = await self.bus.get_registered_agents()
            active = {name for name, meta in registry.items() if meta.get("status") == "active"}
        except Exception:
            active = set()

        if agent_name not in active:
            raise ValueError(
                f"Delegation target '{agent_name}' is not active or does not exist. "
                f"Available: {sorted(list(active))}"
            )

        # CRITICAL: Propagate job_id to maintain single job context across multi-agent execution
        # This ensures all traces from delegated agents belong to the same job
        if self.current_job_id and "job_id" not in payload:
            payload = {**payload, "job_id": self.current_job_id}

        task_id = await self.bus.publish_task(agent_name, payload)

        self.database.append_trace(
            self.current_job_id or "unknown",
            self.config.name,
            "delegation",
            {
                "target_agent": agent_name,
                "task_id": task_id,
                "payload": payload
            }
        )

        return task_id

    def _tool_cache_key(self, name: str, params: dict) -> str:
        """Generate cache key for tool call."""
        param_str = json.dumps(params, sort_keys=True)
        key_data = f"{name}:{param_str}"
        return f"tool:{hashlib.md5(key_data.encode()).hexdigest()}"

    async def _get_from_cache(self, key: str) -> Any:
        """Get value from cache backend."""
        try:
            if hasattr(self.cache_backend, 'get') and asyncio.iscoroutinefunction(self.cache_backend.get):
                return await self.cache_backend.get(key)
            return self.cache_backend.get(key)
        except Exception:
            return None

    async def _put_in_cache(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Put value in cache backend."""
        try:
            if hasattr(self.cache_backend, 'set') and asyncio.iscoroutinefunction(self.cache_backend.set):
                await self.cache_backend.set(key, value, ttl)
            else:
                self.cache_backend.set(key, value, ttl)
        except Exception:
            pass

    async def autonomous_run(
        self, 
        task: dict, 
        max_iterations: int | None = None,
        max_tool_calls: int | None = None
    ) -> dict:
        """
        Run agent autonomously using ReAct-style loop.
        
        The LLM decides what actions to take (use tools, delegate, or finish).
        This is the simple, intuitive way to create agents - no manual planning needed.
        
        Supports non-blocking delegation: when delegating to another agent, this method
        will save execution state and return with status="paused". The orchestrator
        should call resume_paused_execution() when the delegation completes.
        
        Args:
            task: Task inputs
            max_iterations: Maximum number of think-act cycles (each iteration can be tool/delegate/think)
            max_tool_calls: Maximum number of successful tool calls before stopping (None = unlimited)
        
        Returns:
            Final result dict (may have status="paused" if waiting on delegation)
        """
        max_iter = max_iterations or self.config.max_iterations or 10
        max_tools = max_tool_calls  # None means unlimited
        
        # Start fresh execution
        return await self._autonomous_run_loop(
            task=task,
            history=[],
            start_iteration=0,
            max_iterations=max_iter,
            max_tool_calls=max_tools,
            seen_queries=set(),
            seen_delegations={}
        )
    
    async def _autonomous_run_loop(
        self,
        task: dict,
        history: list[dict],
        start_iteration: int,
        max_iterations: int,
        max_tool_calls: int | None,
        seen_queries: set[str],
        seen_delegations: dict[str, set[str]]
    ) -> dict:
        """
        Internal autonomous execution loop.
        
        Extracted from autonomous_run to support resumption from saved state.
        This method contains the actual ReAct loop logic.
        
        Returns status="paused" if delegation occurs (non-blocking model).
        """
        max_iter = max_iterations
        max_tools = max_tool_calls
        
        # Build context
        task_description = (
            task.get('query')
            or task.get('message')
            or task.get('task')
            or task.get('description')
            or json.dumps(task)
        )
        
        # Available actions
        available_tools = self.tools.list_names()
        
        # Check if delegation is explicitly disabled in task
        task_allow_delegation = task.get('_allow_delegation', True)
        can_delegate = self.config.allow_delegation and task_allow_delegation
        
        # Build available agents list for delegation
        available_agents = []
        if can_delegate:
            try:
                agents_info = await self.bus.list_agents()
                available_agents = [
                    a for a in agents_info 
                    if a.get("name") != self.config.name and a.get("status") == "active"
                ]
            except Exception:
                pass

        for iteration in range(start_iteration, max_iter):
            # Cooperative cancellation: check before each iteration
            try:
                if self.current_job_id and hasattr(self.bus, "is_canceled"):
                    canceled = await self.bus.is_canceled(self.current_job_id)
                    if canceled:
                        self._trace(
                            self.current_job_id or "unknown",
                            self.config.name,
                            "task_cancelled",
                            {"iteration": iteration}
                        )
                        return {
                            "status": "canceled",
                            "result": "Execution canceled by user.",
                            "iterations": iteration,
                            "history": history
                        }
            except Exception:
                # If cancel check fails, continue execution
                pass
            # Build system prompt
            # user doesnt need to specify available tools/agents - we provide them
            system_prompt = self._build_autonomous_system_prompt(
                available_tools, 
                available_agents,
                can_delegate
            )
            
            # Build user prompt with history
            user_prompt = self._build_autonomous_user_prompt(
                task_description,
                history,
                iteration
            )
            
            # Get LLM decision
            from datetime import datetime as _dt
            think_started = _dt.utcnow().isoformat() + "Z"
            think_start_time = time.time()
            
            response = await self._llm_generate(user_prompt, system=system_prompt)
            logger.debug("[%s] LLM response: %s", self.config.name, str(response)[:500])
            
            think_duration_ms = int((time.time() - think_start_time) * 1000)
            think_ended = _dt.utcnow().isoformat() + "Z"
            
            # Trace LLM thinking
            self._trace(
                self.current_job_id or "unknown",
                self.config.name,
                "autonomous_think",
                {
                    "iteration": iteration,
                    "worker": self.config.name,
                    "started_at": think_started,
                    "ended_at": think_ended,
                    "duration_ms": think_duration_ms,
                    "response": response
                }
            )
            
            # Parse action from response
            action = self._parse_autonomous_action(response)
            # Log parsed action for debugging
            logger.info(
                "[%s] iteration %d action=%s details=%s",
                self.config.name,
                iteration,
                action.get("type"),
                {k: v for k, v in action.items() if k != "answer"}
            )
            
            if action["type"] == "finish":
                # Agent is done - check if it's actually a successful completion or an error
                answer = action.get("answer", response)
                
                # Detect if the agent is reporting inability to complete the task
                error_indicators = [
                    "unable to complete",
                    "cannot complete",
                    "missing",
                    "not set",
                    "not functional",
                    "failed due to",
                    "error:",
                    "cannot proceed",
                    "not available"
                ]
                
                answer_lower = str(answer).lower()
                is_error = any(indicator in answer_lower for indicator in error_indicators)
                
                # Also check if all tool calls failed
                tool_calls = [h for h in history if h.get("action") == "tool"]
                all_tools_failed = len(tool_calls) > 0 and all("error" in h for h in tool_calls)
                
                if is_error or all_tools_failed:
                    return {
                        "status": "error",
                        "error": answer,
                        "iterations": iteration + 1,
                        "history": history
                    }
                
                return {
                    "status": "success",
                    "result": answer,
                    "iterations": iteration + 1
                }
            
            elif action["type"] == "tool":
                # Execute tool
                tool_name = action.get("tool")
                tool_params = action.get("params", {})
                
                # Query deduplication: create normalized key from tool+params
                query_key = f"{tool_name}:{json.dumps(tool_params, sort_keys=True)}"
                is_duplicate = False
                
                # For web_search, use aggressive deduplication to catch semantic duplicates
                if tool_name == "web_search" and "query" in tool_params:
                    normalized_query = tool_params["query"].lower().strip()
                    # Remove common filler words to catch semantic similarity
                    filler_words = ["the", "a", "an", "and", "or", "but", "full", "complete", "official", "list"]
                    query_words = set(word for word in normalized_query.split() if word not in filler_words)
                    
                    # Check if we've seen a very similar query before (>70% word overlap)
                    for seen in seen_queries:
                        if seen.startswith("web_search:"):
                            # Extract query from seen key: "web_search:{'query': '...'}"
                            try:
                                seen_params = json.loads(seen.split(":", 1)[1])
                                seen_query = seen_params.get("query", "").lower().strip()
                                seen_words = set(word for word in seen_query.split() if word not in filler_words)
                                
                                # Calculate word overlap
                                if query_words and seen_words:
                                    overlap = len(query_words & seen_words) / len(query_words | seen_words)
                                    if overlap > 0.85:  # 85% similarity threshold (relaxed from 70% to allow more variation)
                                        logger.info(
                                            "[%s] Skipping semantic duplicate search (%.0f%% similar): '%s' vs '%s'", 
                                            self.config.name,
                                            overlap * 100,
                                            tool_params["query"],
                                            seen_query
                                        )
                                        history.append({
                                            "action": "tool",
                                            "tool": tool_name,
                                            "params": tool_params,
                                            "result": f"Skipped: semantically similar to previous query '{seen_query[:50]}...'"
                                        })
                                        is_duplicate = True
                                        break
                            except:
                                pass
                
                if not is_duplicate:
                    seen_queries.add(query_key)
                    
                    try:
                        logger.info("[%s] calling tool=%s params=%s", self.config.name, tool_name, tool_params)
                        tool_result = await self.call_tool(tool_name, tool_params)
                        logger.info("[%s] tool=%s result=%s", self.config.name, tool_name, str(tool_result)[:200])
                        history.append({
                            "action": "tool",
                            "tool": tool_name,
                            "params": tool_params,
                            "result": tool_result
                        })
                    except Exception as e:
                        logger.exception("[%s] tool error for %s: %s", self.config.name, tool_name, e)
                        history.append({
                            "action": "tool",
                            "tool": tool_name,
                            "params": tool_params,
                            "error": str(e)
                        })
            
            elif action["type"] == "delegate":
                # Delegate to another agent
                agent_name = action.get("agent")
                delegate_task = action.get("task", task_description)
                logger.info("[%s] delegating to %s: %s...", self.config.name, agent_name, delegate_task[:120])
                
                # Validate target agent against available agents list
                allowed_agents = {a.get("name") for a in (available_agents or [])}
                if not agent_name or agent_name not in allowed_agents:
                    msg = (
                        f"Invalid delegation target '{agent_name}'. "
                        f"Choose one of: {sorted(list(allowed_agents)) or ['<no active agents>']}"
                    )
                    logger.warning("[%s] %s", self.config.name, msg)
                    history.append({
                        "action": "delegate",
                        "agent": agent_name,
                        "task": delegate_task,
                        "error": msg
                    })
                    # Continue loop to let the LLM choose a valid agent next
                    continue

                # Delegation deduplication: check for semantically similar tasks to same agent
                if agent_name not in seen_delegations:
                    seen_delegations[agent_name] = set()
                
                # Normalize task for comparison (lowercase, remove common words)
                filler_words = {"the", "a", "an", "and", "or", "but", "for", "to", "of", "in", "on", "at", "by"}
                normalized_task = delegate_task.lower().strip()
                task_words = set(word for word in normalized_task.split() if word not in filler_words)
                
                # Check similarity against previous delegations to this agent
                is_duplicate = False
                for seen_task in seen_delegations[agent_name]:
                    seen_words = set(word for word in seen_task.split())
                    if task_words and seen_words:
                        overlap = len(task_words & seen_words) / len(task_words | seen_words)
                        if overlap > 0.85:  # 85% similarity threshold (relaxed from 70% to allow more variation)
                            logger.info(
                                "[%s] Skipping duplicate delegation to %s (%.0f%% similar): '%s' vs previous '%s'",
                                self.config.name,
                                agent_name,
                                overlap * 100,
                                delegate_task[:80],
                                seen_task[:80]
                            )
                            history.append({
                                "action": "delegate",
                                "agent": agent_name,
                                "task": delegate_task,
                                "result": f"Skipped: semantically similar task already delegated to {agent_name}. Use previous result."
                            })
                            is_duplicate = True
                            break
                
                if is_duplicate:
                    continue
                
                # Record this delegation
                seen_delegations[agent_name].add(normalized_task)

                # Simple blocking delegation
                try:
                    delegation_task_payload = {
                        "query": delegate_task,
                        "job_id": self.current_job_id,
                    }

                    # Delegate (delegate() will also ensure job_id propagation if missing)
                    delegation_task_id = await self.delegate(agent_name, delegation_task_payload)

                    # Always block and wait for response
                    timeout = action.get("timeout", 120)
                    logger.info("[%s] delegating task_id=%s to %s, waiting for response (timeout=%ss)...", 
                               self.config.name, delegation_task_id, agent_name, timeout)
                    response = None
                    try:
                        response = await self.bus.wait_for_response(delegation_task_id, timeout)
                    except Exception as e:
                        logger.warning("[%s] error while waiting for delegation response: %s", self.config.name, e)

                    if response is None:
                        # No response within timeout
                        logger.warning("[%s] delegation %s timed out after %ss", self.config.name, delegation_task_id, timeout)
                        history.append({
                            "action": "delegate",
                            "agent": agent_name,
                            "task": delegate_task,
                            "error": f"Delegation timed out after {timeout}s",
                            "task_id": delegation_task_id
                        })
                    else:
                        # Got response: inject into history and continue loop
                        history.append({
                            "action": "delegate",
                            "agent": agent_name,
                            "task": delegate_task,
                            "result": response,
                            "status": response.get("status") if isinstance(response, dict) else "unknown",
                        })
                        logger.info("[%s] delegation %s returned with status=%s", 
                                   self.config.name, delegation_task_id, history[-1].get("status"))

                except Exception as e:
                    logger.exception("[%s] delegation error: %s", self.config.name, e)
                    history.append({
                        "action": "delegate",
                        "agent": agent_name,
                        "task": delegate_task,
                        "error": str(e)
                    })
                    # Delegation failed completely - don't retry
                    return {
                        "status": "error",
                        "error": f"Failed to delegate to {agent_name}: {str(e)}",
                        "iterations": iteration + 1,
                        "history": history
                    }
            
            else:
                # Unknown action - treat as thinking
                history.append({
                    "action": "think",
                    "thought": response
                })
            
            # Check if we've hit max_tool_calls limit
            if max_tools is not None:
                successful_tool_calls = [
                    h for h in history 
                    if h.get("action") == "tool" 
                    and "result" in h 
                    and h["result"] not in [None, ""]
                    and not str(h["result"]).startswith("Skipped:")
                    and "error" not in h
                ]
                
                if len(successful_tool_calls) >= max_tools:
                    logger.warning(
                        "[%s] Maximum tool calls limit reached (%d/%d). Asking LLM to synthesize final answer.",
                        self.config.name,
                        len(successful_tool_calls),
                        max_tools
                    )
                    
                    # Ask LLM to provide final answer based on gathered information
                    synthesis_prompt = f"""You've completed your research/work. Based on all the information gathered, provide a comprehensive final answer.

Task: {task_description}

Information gathered:
{self._format_history_for_synthesis(history)}

Provide a clear, complete final answer based on this information."""
                    
                    try:
                        final_answer = await self._llm_generate(synthesis_prompt)
                        return {
                            "status": "success",
                            "result": final_answer,
                            "iterations": iteration + 1,
                            "history": history,
                            "max_tool_calls_reached": True
                        }
                    except Exception as e:
                        logger.error("[%s] Failed to synthesize final answer: %s", self.config.name, e)
                        return {
                            "status": "success",
                            "result": f"Task completed with {len(successful_tool_calls)} tool calls. Maximum tool call limit ({max_tools}) reached.",
                            "iterations": iteration + 1,
                            "history": history,
                            "max_tool_calls_reached": True
                        }
        
        # Max iterations reached
        return {
            "status": "incomplete",
            "result": "Maximum iterations reached. Unable to complete task.",
            "iterations": max_iter,
            "history": history
        }

    def _trace(self, job_id: str, agent_name: str, event_type: str, payload: dict) -> None:
        """Append a trace if enabled and not masked."""
        if not self._trace_enabled:
            return
        if event_type in self._trace_mask:
            return
        try:
            self.database.append_trace(job_id, agent_name, event_type, payload)
        except Exception:
            # Tracing must never break runtime
            pass
    
    def _build_autonomous_system_prompt(
        self,
        available_tools: list[str],
        available_agents: list[dict],
        can_delegate: bool,
    ) -> str:
        """Build system prompt for autonomous agent."""
        # Optional: legacy prompt.md (kept for backward compatibility) or explicit instructions passed at construction
        custom_prompt = self._extra_instructions
        if not custom_prompt:
            try:
                prompt_path = os.path.join(os.getcwd(), "agents", self.config.name, "prompt.md")
                if os.path.isfile(prompt_path):
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        custom_prompt = f.read().strip()
            except Exception:
                custom_prompt = None

        tool_list = "\n".join([f"- {t}" for t in available_tools]) if available_tools else "None"

        agent_list = "None"
        if can_delegate and available_agents:
            agent_list = "\n".join(
                [
                    f"- {a['name']}: {a.get('role', 'N/A')} - {a.get('goal', 'N/A')}"
                    for a in available_agents
                ]
            )

        header = f"You are {self.config.role}.\nYour goal: {self.config.goal}"

        if custom_prompt:
            header += "\n\nAgent Policy (from prompt.md):\n" + custom_prompt

        system = f"""{header}

You act autonomously to complete the task. Always respond with a SINGLE JSON object only.

CRITICAL: 
- Output ONLY the JSON object, no markdown code fences (no ```json), no explanatory text
- Do NOT add extra fields like "action", "reasoning", or "explanation"
- Follow the EXACT schema below

Schema:
{{
  "type": "tool|delegate|finish",
  "tool": "<tool_name_if_type_tool>",
  "params": {{"param1": "value1"}},
  "agent": "<agent_name_if_type_delegate>",
  "task": "<task_text_if_type_delegate>",
  "timeout": 60,
  "answer": "<final_answer_if_type_finish>"
}}

## Available Tools:
{tool_list}

To use a tool:
{{"type":"tool","tool":"<tool_name>","params":{{"param":"value"}}}}
"""

        if can_delegate:
            system += f"""
## Available Agents (for delegation):
{agent_list}

To delegate a task:
{{"type":"delegate","agent":"<agent_name>","task":"<clear task description>","timeout":90}}

⚠️ CRITICAL DELEGATION RULES:
- ONLY use agent names from the list above - do NOT invent names
- If no listed agent matches your needs, use tools or finish instead
- Each agent has specific expertise (role/goal) - choose the most appropriate one
- Delegation is for complex subtasks that require specialized processing

## Key System Tools:

### Parallel Processing (for independent subtasks):
{{"type":"tool","tool":"system_delegate_parallel","params":{{"agent":"<agent_name>","tasks":["task1","task2","task3"]}}}}
- Use when you have multiple independent subtasks that can run simultaneously
- All tasks execute in parallel and results are aggregated
- Ideal for: processing multiple documents, analyzing multiple data points, gathering info from multiple sources

### Document Splitting (for large content):
{{"type":"tool","tool":"system_split_document","params":{{"document":"<text>","num_chunks":3}}}}
- Use before parallel processing to divide large documents into manageable chunks
- Returns list of chunks that can be passed to system_delegate_parallel

### Artifact Storage (for sharing data):
{{"type":"tool","tool":"system_store_artifact","params":{{"data":"<your_data>","artifact_type":"result","metadata":{{"description":"..."}}}}}}
- Store results, intermediate data, or large outputs for other agents to retrieve
- Use when delegating and the subtask needs access to data you've gathered
- Returns artifact_id which can be used for retrieval

### Artifact Retrieval:
{{"type":"tool","tool":"system_retrieve_artifact","params":{{"artifact_id":"<uuid_from_store>","artifact_type":"result"}}}}
- Retrieve previously stored artifacts by artifact_id (returned from store_artifact)
- Useful when building on work from previous steps or other agents
 - IMPORTANT: Do NOT attempt to retrieve artifacts using job_id or task_id. Only call
     `system_retrieve_artifact` when you have an explicit artifact_id (UUID)
     returned by a previous store_artifact call or delegation response.
     If a delegated agent returned its result inline (i.e., the response field contains the data),
     you do NOT need to call artifact retrieval — synthesize from the inline result instead.
     Calling artifact retrieval with job/task ids often fails and causes unnecessary retries.
"""
        else:
            # Explicitly tell non-coordinator agents they CANNOT delegate
            system += """
⚠️ IMPORTANT: You are a specialist agent and CANNOT delegate tasks to other agents.
- Use your available tools to complete the task yourself
- DO NOT attempt to use system_delegate_task or any delegation tools
- Focus on using your specialized tools to complete the task
- Synthesize findings from your tool calls and finish with a comprehensive answer

## Artifact Storage (ONLY for large results):
⚠️ CRITICAL: DO NOT use artifact tools unless explicitly storing/retrieving YOUR OWN large data (>100KB).

### When to store artifacts:
- Your final result/answer exceeds 100KB in size
- You need to save intermediate data for your own later use
- Example: {{"type":"tool","tool":"system_store_artifact","params":{{"data":"<large_content>","artifact_type":"result"}}}}
- Returns artifact_id for later retrieval

### When to retrieve artifacts:
- ONLY if you previously stored an artifact and have its artifact_id (UUID)
- DO NOT try to retrieve artifacts you didn't create
- DO NOT use random search terms or keys
- Example: {{"type":"tool","tool":"system_retrieve_artifact","params":{{"artifact_id":"<uuid_from_store>","artifact_type":"result"}}}}

⚠️ DO NOT use system_retrieve_artifact to search for data - use your domain tools instead!
"""

        system += """
When you complete the task:
{{"type":"finish","answer":"<comprehensive final answer>"}}

## Execution Guidelines:
- Use tools strategically - avoid redundant calls for the same information"""

        if can_delegate:
            system += """
- Delegate complex subtasks to specialized agents when available
- Use parallel processing for independent subtasks to improve efficiency
- Store intermediate results as artifacts when they'll be reused"""
        else:
            system += """
- Make the most of your specialized tools - they are designed for your domain
- Process information directly rather than attempting delegation
- Synthesize findings from multiple tool calls when needed"""

        system += """
- Focus on quality synthesis over quantity of actions
- Finish when you have sufficient information to provide a comprehensive answer

Think step-by-step internally, but output ONLY the JSON action object. No explanatory text."""


        return system
    
    def _build_autonomous_user_prompt(
        self,
        task_description: str,
        history: list[dict],
        iteration: int
    ) -> str:
        """Build user prompt with task and history."""
        
        prompt = f"TASK: {task_description}\n\n"
        
        if history:
            prompt += "HISTORY:\n"
            for i, entry in enumerate(history):
                if entry["action"] == "tool":
                    prompt += f"{i+1}. Used tool '{entry['tool']}' with params {entry.get('params', {})}\n"
                    if "error" in entry:
                        prompt += f"   ERROR: {entry['error']}\n"
                    else:
                        result_str = str(entry.get('result', ''))[:500]
                        prompt += f"   RESULT: {result_str}\n"
                
                elif entry["action"] == "delegate":
                    prompt += f"{i+1}. Delegated to agent '{entry['agent']}': {entry.get('task', 'N/A')}\n"
                    if "error" in entry:
                        prompt += f"   ERROR: {entry['error']}\n"
                    else:
                        result_str = str(entry.get('result', ''))[:500]
                        prompt += f"   RESULT: {result_str}\n"
                
                elif entry["action"] == "think":
                    prompt += f"{i+1}. THOUGHT: {entry.get('thought', '')[:200]}\n"
                
                elif entry["action"] == "system_hint":
                    prompt += f"\n⚠️ SYSTEM: {entry.get('message', '')}\n\n"
            
            prompt += "\n"

        # If a delegation result is present in history, add a short SYSTEM hint
        # so the LLM prefers synthesizing and finishing over re-delegating the
        # same task. This reduces redundant delegations and wasted tool calls.
        has_delegate_result = False
        for entry in history:
            if entry.get("action") == "delegate" and "result" in entry and entry.get("status") in {"completed", "success", None}:
                has_delegate_result = True
                break

        if has_delegate_result:
            prompt += "\nSYSTEM_HINT: A delegated agent has returned a result above. "
            prompt += "Prefer synthesizing a final answer from that result and other history. "
            prompt += "Do NOT re-delegate the same task unless the returned result is clearly insufficient or explicitly requests further delegation.\n\n"

        prompt += f"What should you do next? (Iteration {iteration + 1})\n"

        return prompt

    def _format_history_for_synthesis(self, history: list[dict]) -> str:
        """Format execution history for final answer synthesis."""
        formatted = []
        for i, entry in enumerate(history, 1):
            action = entry.get("action", "unknown")
            if action == "tool":
                tool_name = entry.get("tool", "unknown")
                result = entry.get("result", entry.get("error", "No result"))
                # Truncate large results
                result_str = str(result)[:500]
                formatted.append(f"{i}. Tool '{tool_name}' returned: {result_str}")
            elif action == "delegate":
                agent = entry.get("agent", "unknown")
                result = entry.get("result", entry.get("error", "No result"))
                formatted.append(f"{i}. Delegated to '{agent}', result: {result}")
        
        return "\n".join(formatted) if formatted else "No information gathered yet."

    def _parse_autonomous_action(self, response: str) -> dict:
        """Parse LLM response to extract action, preferring JSON format with text fallback."""
        # 1) Try JSON extraction anywhere in the response
        try:
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1 and end > start:
                payload = response[start : end + 1]
                data = json.loads(payload)
                # Normalize keys
                norm = {str(k).lower(): v for k, v in data.items()}
                action_type = norm.get("type") or norm.get("action") or "think"
                action_type = str(action_type).lower()
                
                # Handle LLM putting tool name in "action" field instead of "type"
                # e.g., {"action": "web_search", "tool": "web_search", ...}
                if action_type not in ["tool", "delegate", "finish", "think"]:
                    # LLM likely put the tool name in "action" field
                    # Check if there's a "tool" field, or use "action" value as tool name
                    if norm.get("tool") or norm.get("params"):
                        # This looks like a tool call
                        tool = norm.get("tool") or action_type
                        params = norm.get("params") or {}
                        return {"type": "tool", "tool": tool, "params": params}
                
                # Map common aliases
                if action_type == "tool":
                    tool = norm.get("tool") or norm.get("tool_name")
                    params = norm.get("params") or {}
                    return {"type": "tool", "tool": tool, "params": params}
                if action_type == "delegate":
                    agent = norm.get("agent") or norm.get("target")
                    task = norm.get("task") or norm.get("query") or norm.get("message")
                    timeout = norm.get("timeout") or 60
                    return {"type": "delegate", "agent": agent, "task": task, "timeout": timeout}
                if action_type == "finish":
                    answer = norm.get("answer") or norm.get("result") or response
                    return {"type": "finish", "answer": answer}
                # Default think
                return {"type": "think"}
        except Exception:
            pass

        # 2) Fallback to text parser for legacy format
        return self._parse_autonomous_action_text(response)

    def _parse_autonomous_action_text(self, response: str) -> dict:
        """Parse legacy text format with ACTION:/AGENT:/TOOL_NAME:/... lines."""
        lines = response.strip().split("\n")
        action_type = None
        data: dict[str, Any] = {}
        for line in lines:
            line = line.strip()
            if line.startswith("ACTION:"):
                action_str = line.replace("ACTION:", "").strip().upper()
                if "TOOL" in action_str:
                    action_type = "tool"
                elif "DELEGATE" in action_str:
                    action_type = "delegate"
                elif "FINISH" in action_str:
                    action_type = "finish"
            elif line.startswith("TOOL_NAME:"):
                data["tool"] = line.replace("TOOL_NAME:", "").strip()
            elif line.startswith("PARAMS:"):
                params_str = line.replace("PARAMS:", "").strip()
                try:
                    data["params"] = json.loads(params_str)
                except Exception:
                    data["params"] = {}
            elif line.startswith("AGENT:"):
                data["agent"] = line.replace("AGENT:", "").strip()
            elif line.startswith("TASK:"):
                data["task"] = line.replace("TASK:", "").strip()
            elif line.startswith("ANSWER:"):
                # Capture everything after ANSWER:
                answer_index = response.find("ANSWER:")
                if answer_index != -1:
                    data["answer"] = response[answer_index + 7 :].strip()
                else:
                    data["answer"] = line.replace("ANSWER:", "").strip()
        return {"type": action_type or "think", **data}
