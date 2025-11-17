"""
AgentRunner: High-level agent execution and orchestration.

Provides run(), replay(), and run_pipeline() for executing agents,
managing jobs, and orchestrating multi-agent workflows.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
import pkgutil
from contextlib import suppress
from datetime import datetime
import time
from typing import Any
import uuid

from .agent_runtime import Agent
from .config import AgentConfig, BackendFactory, LaddrConfig

logger = logging.getLogger(__name__)


def _sanitize_for_json(obj: Any, max_depth: int = 50) -> Any:
    """
    Recursively sanitize objects for JSON serialization.
    
    Converts non-serializable types (coroutines, datetimes, bytes, etc.) to strings.
    Prevents infinite recursion with max_depth limit.
    
    Args:
        obj: Object to sanitize
        max_depth: Maximum recursion depth
        
    Returns:
        JSON-serializable object
    """
    if max_depth <= 0:
        return "<max depth reached>"
    
    # Handle None
    if obj is None:
        return None
    
    # Handle coroutines (async functions that haven't been awaited)
    if asyncio.iscoroutine(obj):
        return f"<coroutine: {type(obj).__name__}>"
    
    # Handle coroutine functions
    if asyncio.iscoroutinefunction(type(obj)):
        return f"<coroutine function: {type(obj).__name__}>"
    
    # Handle datetime objects
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    # Handle bytes
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            return f"<bytes: {len(obj)} bytes>"
    
    # Handle sets
    if isinstance(obj, set):
        return [_sanitize_for_json(item, max_depth - 1) for item in obj]
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return {
            str(k): _sanitize_for_json(v, max_depth - 1)
            for k, v in obj.items()
        }
    
    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item, max_depth - 1) for item in obj]
    
    # Handle other non-serializable types
    try:
        # Try to serialize directly (works for primitives)
        import json
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # Convert to string representation
        try:
            return str(obj)
        except Exception:
            return f"<non-serializable: {type(obj).__name__}>"


class AgentRunner:
    """
    High-level agent runner for executing agents and managing jobs.
    
    Provides:
    - run(): Execute agent with job tracking
    - replay(): Replay previous job
    - run_pipeline(): Orchestrate multi-agent workflow
    """

    def __init__(
        self,
        agent: Agent | None = None,
        env_config: LaddrConfig | None = None
    ):
        """
        Initialize runner.
        
        
        
        Args:
            agent: Agent instance (created if None)
            env_config: Environment configuration
        """
        self.agent = agent
        self.env_config = env_config or LaddrConfig()
        self.factory = BackendFactory(self.env_config)
        self.database = self.factory.create_database_backend()
        # Inline worker control
        self._inline_worker_task = None
        self._inline_worker_stop = None

    async def run(
        self,
        inputs: dict,
        agent_name: str | None = None,
        job_id: str | None = None
    ) -> dict:
        """
        Run an agent with job tracking.
        
        Creates a job record, executes the agent, stores results and traces.
        
        Args:
            inputs: Task inputs
            agent_name: Agent name (uses self.agent if None)
            job_id: Job ID (generated if None)
        
        Returns:
            Structured result dict with job_id, status, result/error
        """
        # Determine agent
        if agent_name:
            # Try flat module style: agents/<name>.py exporting an Agent instance named <name>
            try:
                mod = importlib.import_module(f"agents.{agent_name}")
                candidate = getattr(mod, agent_name, None)
                if candidate and hasattr(candidate, "handle"):
                    # If the project exposed a module-level Agent instance, re-instantiate
                    # it with this runner's env_config to ensure runtime flags (like
                    # blocking_delegation) are respected.
                    try:
                        AgentCls = candidate.__class__
                        agent_cfg = getattr(candidate, "config", None)
                        if agent_cfg is None:
                            # Fallback to simple AgentConfig
                            agent_cfg = AgentConfig(
                                name=agent_name,
                                role=getattr(candidate, "ROLE", "Agent"),
                                goal=getattr(candidate, "GOAL", "Execute tasks")
                            )
                        # Preserve tools, llm, and other configuration from original instance
                        original_tools = getattr(candidate, "tools", None)
                        original_llm = getattr(candidate, "llm", None)
                        original_instructions = getattr(candidate, "_extra_instructions", None)
                        original_is_coordinator = getattr(candidate, "is_coordinator", None)
                        original_available_agents = getattr(candidate, "available_agents_hint", None)
                        original_mcp_providers = getattr(candidate, "_mcp_providers", None)
                        
                        # If original_tools is a ToolRegistry and we have MCP providers,
                        # we need to include MCP providers in the tools list so they get processed
                        tools_for_new_agent = original_tools
                        from laddr.core.tooling import ToolRegistry
                        if original_mcp_providers and isinstance(original_tools, ToolRegistry):
                            # Extract regular tools from registry and combine with MCP providers
                            # This ensures MCP providers are detected and registered in the new agent
                            regular_tools = [tool.func for tool in original_tools.list()]
                            tools_for_new_agent = regular_tools + list(original_mcp_providers)
                            logger.debug(f"Preserving {len(original_mcp_providers)} MCP providers when recreating agent {agent_name}")
                        
                        agent = AgentCls(
                            agent_cfg, 
                            self.env_config,
                            tools=tools_for_new_agent,
                            llm=original_llm,
                            instructions=original_instructions,
                            is_coordinator=original_is_coordinator,
                            available_agents=original_available_agents
                        )
                        
                        # Also preserve MCP providers directly as backup
                        if original_mcp_providers:
                            agent._mcp_providers = original_mcp_providers
                            logger.debug(f"Set _mcp_providers on new agent instance: {len(original_mcp_providers)} providers")
                    except Exception:
                        # Fall back to using the provided module-level instance
                        agent = candidate  # type: ignore[assignment]
                else:
                    raise AttributeError("No module-level agent instance found")
            except Exception:
                # Fallback to legacy handler class pattern: agents/<name>/handler.py with <Name>Agent
                try:
                    agent_mod = importlib.import_module(f"agents.{agent_name}.handler")
                    AgentClass = getattr(agent_mod, f"{agent_name.capitalize()}Agent")
                    agent_config = AgentConfig(
                        name=getattr(AgentClass, 'AGENT_NAME', agent_name),
                        role=getattr(AgentClass, 'ROLE', 'Agent'),
                        goal=getattr(AgentClass, 'GOAL', 'Execute tasks')
                    )
                    agent = AgentClass(agent_config, self.env_config)
                except Exception as primary_err:
                    raise ValueError(
                        f"Could not load agent '{agent_name}'. Ensure 'agents/{agent_name}.py' defines '{agent_name}' Agent instance "
                        f"or legacy 'agents/{agent_name}/handler.py' defines '{agent_name.capitalize()}Agent'. Root cause: {primary_err}"
                    )
            # Ensure bus registration
            # Ensure the agent instance uses this runner's env_config and backends.
            try:
                # Overwrite env_config and recreate factory/llm/cache/storage to match runner
                setattr(agent, "env_config", self.env_config)
                try:
                    setattr(agent, "factory", BackendFactory(self.env_config))
                except Exception:
                    pass
                try:
                    # Recreate LLM backend from runner config so correct provider (gemini/openai) is used
                    if hasattr(agent, "factory"):
                        # Respect any agent-specific llm override on the AgentConfig
                        import os as _os
                        backend_override = getattr(agent.config, "llm_backend", None) if hasattr(agent, "config") else None
                        model_override = getattr(agent.config, "llm_model", None) if hasattr(agent, "config") else None
                        # Env var override LLM_BACKEND_<AGENT>
                        try:
                            env_key = f"LLM_BACKEND_{(agent.config.name or '').upper()}"
                            env_model_key = f"LLM_MODEL_{(agent.config.name or '').upper()}"
                            if _os.environ.get(env_key):
                                backend_override = _os.environ.get(env_key)
                            if _os.environ.get(env_model_key):
                                model_override = _os.environ.get(env_model_key)
                        except Exception:
                            pass
                        setattr(agent, "llm", agent.factory.create_llm_backend(override=backend_override, model_override=model_override, agent_name=agent.config.name))
                except Exception:
                    pass
                # Connect/register on the bus
                try:
                    await agent.connect_bus()
                except Exception:
                    pass
            except Exception:
                # Best-effort; continue if we can't rewire the agent
                pass

            # Honor a caller-provided override to disable delegation for this run.
            # The API sets a private `_allow_delegation` key for single-shot prompts.
            try:
                if isinstance(inputs, dict) and "_allow_delegation" in inputs:
                    override = inputs.get("_allow_delegation")
                    if hasattr(agent, "config") and hasattr(agent.config, "allow_delegation"):
                        agent.config.allow_delegation = bool(override)
            except Exception:
                pass
        elif self.agent:
            agent = self.agent
        else:
            raise ValueError("No agent specified")

        # Optionally start inline local workers so delegated tasks are executed in-process
        inline_env = (str(getattr(self.env_config, "enable_inline_workers", "")).lower() or 
                      str(os.environ.get('ENABLE_INLINE_WORKERS', '1')).lower())
        enable_inline = inline_env not in ("0", "false", "no")

        if enable_inline and self._inline_worker_task is None:
            try:
                agent_names = self._discover_local_agents(exclude=[agent.config.name])
                if agent_names:
                    self._start_inline_workers(agent_names)
            except Exception:
                # Non-fatal: continue without inline workers
                pass

        # Create job
        job_id = job_id or str(uuid.uuid4())
        pipeline_name = agent.config.name

        self.database.create_job(
            job_id=job_id,
            pipeline=pipeline_name,
            inputs=inputs
        )

        # Execute
        start = time.time()
        try:
            # Add job_id to inputs
            task = {**inputs, "job_id": job_id}

            # Handle task
            result = await agent.handle(task)

            # Save result
            outputs = result.get("result", {})
            status = result.get("status", "completed")
            error = result.get("error")

            # Store error in outputs if present
            if error:
                outputs = {"error": error, **outputs}

            # Sanitize outputs before saving to prevent JSON serialization errors
            sanitized_outputs = _sanitize_for_json(outputs)
            self.database.save_result(
                job_id=job_id,
                outputs=sanitized_outputs,
                status=status
            )

            # Return structured response
            duration_ms = int((time.time() - start) * 1000)
            return {
                "job_id": job_id,
                "status": status,
                "result": outputs,
                "error": error,
                "duration_ms": duration_ms,
                "agent": pipeline_name
            }

        except Exception as e:
            # Save error
            sanitized_error = _sanitize_for_json({"error": str(e)})
            self.database.save_result(
                job_id=job_id,
                outputs=sanitized_error,
                status="failed"
            )

            duration_ms = int((time.time() - start) * 1000)
            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
                "duration_ms": duration_ms,
                "agent": pipeline_name
            }
        finally:
            # Stop inline workers if running
            if self._inline_worker_task is not None:
                with suppress(Exception):
                    self._stop_inline_workers()
    
    def _discover_local_agents(self, exclude: list[str] | None = None) -> list[str]:
        """Discover local agents under the 'agents' package for inline execution."""
        names: list[str] = []
        exclude = set(exclude or [])
        try:
            agents_pkg = importlib.import_module("agents")
            for m in pkgutil.iter_modules(agents_pkg.__path__):
                name = m.name
                if name in exclude:
                    continue
                # Ensure handler exists
                with suppress(Exception):
                    importlib.import_module(f"agents.{name}.handler")
                    names.append(name)
        except Exception:
            pass
        return names

    def _start_inline_workers(self, agent_names: list[str]) -> None:
        """Start a background task that consumes tasks and runs target agents inline."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Starting inline workers for agents: {agent_names}")
        
        stop = asyncio.Event()
        self._inline_worker_stop = stop

        async def _loop():
            # Cache agent instances per name to avoid re-import overhead
            agent_cache: dict[str, Agent] = {}
            bus = self.factory.create_queue_backend()
            logger.info(f"Inline worker loop started, listening for tasks...")
            while not stop.is_set():
                progress = False
                for name in agent_names:
                    try:
                        tasks = await bus.consume_tasks(name, block_ms=200, count=5)
                    except Exception:
                        logger.exception(f"Error consuming tasks for {name}")
                        tasks = []
                    if not tasks:
                        continue
                    logger.info(f"Inline worker received {len(tasks)} task(s) for {name}")
                    progress = True
                    for data in tasks:
                        try:
                            task_id = data.get("task_id")
                            payload = data.get("payload", {})
                            logger.info(f"Processing task {task_id} for {name}")
                            # Get or create agent instance
                            if name not in agent_cache:
                                try:
                                    mod = importlib.import_module(f"agents.{name}.handler")
                                    cls = getattr(mod, f"{name.capitalize()}Agent")
                                except Exception as e:
                                    # Skip if cannot import
                                    logger.error(f"Failed to import agent {name}: {e}")
                                    continue
                                agent_cfg = AgentConfig(
                                    name=getattr(cls, 'AGENT_NAME', name),
                                    role=getattr(cls, 'ROLE', 'Agent'),
                                    goal=getattr(cls, 'GOAL', 'Execute tasks')
                                )
                                inst: Agent = cls(agent_cfg, self.env_config)
                                await inst.connect_bus()
                                logger.info(f"Created inline worker agent instance for {name}")
                                agent_cache[name] = inst
                            inst = agent_cache[name]
                            # Execute task
                            result = await inst.handle(payload)
                            logger.info(f"Task {task_id} completed: {result.get('status', 'unknown')}")
                            # Publish response for waiter
                            if task_id:
                                with suppress(Exception):
                                    await bus.publish_response(task_id, result)
                                logger.info(f"Published response for task {task_id}")
                        except Exception:
                            # On processing error, continue loop
                            logger.exception(f"Error processing task {data.get('task_id')} for {name}")
                            continue

                # Avoid busy loop if no progress
                if not progress:
                    try:
                        await asyncio.wait_for(stop.wait(), timeout=0.25)
                    except asyncio.TimeoutError:
                        pass

        self._inline_worker_task = asyncio.create_task(_loop())

    def _stop_inline_workers(self) -> None:
        if self._inline_worker_stop is not None:
            self._inline_worker_stop.set()
        if self._inline_worker_task is not None:
            self._inline_worker_task.cancel()
            with suppress(Exception):
                # Try to get running loop first, fallback to event loop for sync context
                try:
                    loop = asyncio.get_running_loop()
                    # If we have a running loop, we can't use run_until_complete
                    # Just cancel and let the loop handle it
                except RuntimeError:
                    # No running loop, safe to use get_event_loop()
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(self._inline_worker_task)
        self._inline_worker_task = None
        self._inline_worker_stop = None

    def replay(
        self,
        job_id: str,
        reexecute: bool = False
    ) -> dict:
        """
        Replay a previous job.
        
        Args:
            job_id: Job ID to replay
            reexecute: If True, re-execute the job; if False, return stored result
        
        Returns:
            Job result
        """
        # Get stored result
        result = self.database.get_result(job_id)

        if not result:
            return {
                "status": "error",
                "error": f"Job not found: {job_id}"
            }

        if reexecute:
            # Re-execute with stored inputs
            inputs = result.get("inputs", {})
            pipeline_name = result.get("pipeline_name")

            # Run with same job_id
            return asyncio.run(self.run(inputs, agent_name=pipeline_name, job_id=job_id))
        # Return stored result
        return {
            "job_id": job_id,
            "status": result.get("status"),
            "result": result.get("outputs"),
            "error": result.get("error"),
            "pipeline_name": result.get("pipeline_name"),
            "created_at": result.get("created_at"),
            "completed_at": result.get("completed_at")
        }

    async def run_pipeline(
        self,
        stages: list[dict],
        pipeline_name: str = "pipeline",
        job_id: str | None = None
    ) -> dict:
        """
        Run a multi-stage pipeline (sequential agents).
        
        Each stage is executed in order, with outputs from previous
        stages passed as inputs to next stage.
        
        Args:
            stages: List of stage dicts, each with:
                - agent: Agent name
                - inputs: Static inputs for this stage
                - pass_previous: If True, pass previous stage outputs
            pipeline_name: Pipeline identifier
            job_id: Job ID (generated if None)
        
        Returns:
            Pipeline result with all stage outputs
        """
        job_id = job_id or str(uuid.uuid4())

        # Create job
        self.database.create_job(
            job_id=job_id,
            pipeline_name=pipeline_name,
            inputs={"stages": stages}
        )

        # Trace pipeline start
        self.database.append_trace(
            job_id,
            pipeline_name,
            "pipeline_start",
            {"stages": [s.get("agent") for s in stages]}
        )

        # Execute stages
        stage_results = []
        previous_output = {}

        for i, stage in enumerate(stages):
            agent_name = stage.get("agent")
            static_inputs = stage.get("inputs", {})
            pass_previous = stage.get("pass_previous", True)

            # Build inputs
            if pass_previous and previous_output:
                inputs = {**previous_output, **static_inputs}
            else:
                inputs = static_inputs

            # Trace stage start
            self.database.append_trace(
                job_id,
                pipeline_name,
                "stage_start",
                {
                    "stage": i,
                    "agent": agent_name,
                    "inputs": inputs
                }
            )

            # Run stage
            try:
                stage_result = await self.run(inputs, agent_name=agent_name)

                stage_results.append({
                    "stage": i,
                    "agent": agent_name,
                    "status": stage_result.get("status"),
                    "result": stage_result.get("result"),
                    "error": stage_result.get("error")
                })

                # Update previous output
                if stage_result.get("status") == "success":
                    previous_output = stage_result.get("result", {})
                else:
                    # Pipeline failed
                    self.database.append_trace(
                        job_id,
                        pipeline_name,
                        "pipeline_error",
                        {"stage": i, "error": stage_result.get("error")}
                    )

                    sanitized_stage_results = _sanitize_for_json({"stage_results": stage_results})
                    self.database.save_result(
                        job_id=job_id,
                        outputs=sanitized_stage_results,
                        status="error"
                    )

                    return {
                        "job_id": job_id,
                        "status": "error",
                        "stage_results": stage_results,
                        "error": f"Pipeline failed at stage {i}"
                    }

            except Exception as e:
                # Stage exception
                self.database.append_trace(
                    job_id,
                    pipeline_name,
                    "stage_error",
                    {"stage": i, "error": str(e)}
                )

                stage_results.append({
                    "stage": i,
                    "agent": agent_name,
                    "status": "error",
                    "error": str(e)
                })

                sanitized_stage_results = _sanitize_for_json({"stage_results": stage_results})
                self.database.save_result(
                    job_id=job_id,
                    outputs=sanitized_stage_results,
                    status="error"
                )

                return {
                    "job_id": job_id,
                    "status": "error",
                    "stage_results": stage_results,
                    "error": str(e)
                }

        # Pipeline success
        self.database.append_trace(
            job_id,
            pipeline_name,
            "pipeline_complete",
            {"stages": len(stages)}
        )

        sanitized_final_outputs = _sanitize_for_json({"stage_results": stage_results, "final": previous_output})
        self.database.save_result(
            job_id=job_id,
            outputs=sanitized_final_outputs,
            status="completed"
        )

        return {
            "job_id": job_id,
            "status": "success",
            "stage_results": stage_results,
            "final_output": previous_output
        }


# Convenience function for CLI/API
async def run_agent(
    agent_name: str,
    inputs: dict,
    env_config: LaddrConfig | None = None
) -> dict:
    """
    Convenience function to run an agent by name.
    
    Args:
        agent_name: Agent name
        inputs: Task inputs
        env_config: Environment configuration
    
    Returns:
        Job result
    """
    runner = AgentRunner(env_config=env_config)
    return await runner.run(inputs, agent_name=agent_name)


class WorkerRunner:
    """
    Lightweight worker runner for a single agent instance.

    Consumes tasks from the message bus for the agent's name and publishes results.
    """

    def __init__(
        self,
        agent: Agent,
        database_url: str | None = None,
        redis_url: str | None = None,
        storage_endpoint: str | None = None,
        storage_access_key: str | None = None,
        storage_secret_key: str | None = None,
        storage_secure: bool | None = None,
        storage_region: str | None = None,
    ) -> None:
        # Build env config from provided values (fallback to defaults)
        # Support both new storage_* and old minio_* parameter names
        defaults = LaddrConfig()
        self.env_config = LaddrConfig(
            database_url=database_url or defaults.database_url,
            redis_url=redis_url or defaults.redis_url,
            storage_endpoint=storage_endpoint or defaults.storage_endpoint,
            storage_access_key=storage_access_key or defaults.storage_access_key,
            storage_secret_key=storage_secret_key or defaults.storage_secret_key,
            storage_secure=storage_secure if storage_secure is not None else (
                False
            ),
            storage_region=storage_region or defaults.storage_region,
            storage_bucket=defaults.storage_bucket,  # Read from env
            enable_large_response_storage=defaults.enable_large_response_storage,  # Read from env
            storage_threshold_kb=defaults.storage_threshold_kb,  # Read from env
        )
        self.factory = BackendFactory(self.env_config)
        self.agent = agent

    async def start(self) -> None:
        """Start processing tasks indefinitely for the agent's queue."""        
        # Create bus from factory to ensure proper configuration (Kafka, Redis, etc.)
        bus = self.factory.create_queue_backend()
        
        # Replace agent's bus with the correctly configured one
        self.agent.bus = bus
        
        # Ensure agent is connected/registered with retry logic
        max_retries = 10
        retry_delay = 1  # Start with 1 second
        
        for attempt in range(max_retries):
            try:
                await self.agent.connect_bus()
                logger.info(f"Agent {self.agent.config.name} connected to bus")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect agent to bus (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff, max 30s
                else:
                    logger.error(f"Failed to connect agent to bus after {max_retries} attempts: {e}")
                    raise

        agent_name = self.agent.config.name
        logger.info(f"Starting consume loop for agent: {agent_name}")

        while True:
            tasks = await bus.consume_tasks(agent_name, block_ms=2000, count=5)
            if not tasks:
                logger.debug(f"No tasks for {agent_name}, continuing...")
                continue
            logger.info(f"Received {len(tasks)} task(s) for {agent_name}")
            for message in tasks:
                task_id = message.get("task_id")
                payload = message.get("payload", {})
                logger.debug(f"Processing task {task_id}")
                try:
                    result = await self.agent.handle(payload)
                    if task_id:
                        await bus.publish_response(task_id, result)
                        logger.debug(f"Published response for task {task_id}")
                except Exception as e:
                    logger.error(f"Error processing task {task_id}: {e}")
                    if task_id:
                        await bus.publish_response(task_id, {"status": "error", "error": str(e)})
