"""
Built-in system tools for agent task delegation and artifact management.

Provides tools for:
- Delegating tasks to other agents via message queue
- Storing large payloads in artifact registry (MinIO/S3)
- Retrieving artifacts by ID
- Tool override system for custom implementations
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
from typing import Any, Callable
import uuid

# Module logger
logger = logging.getLogger(__name__)

# Global registry for tool overrides
_TOOL_OVERRIDES: dict[str, Callable] = {}


def override_system_tool(tool_name: str):
    """
    Decorator to override a system tool with a custom implementation.
    
    Use this decorator to replace built-in system tools (like system_delegate_parallel,
    system_split_document, etc.) with your own implementations.
    
    Example:
        from laddr.core.system_tools import override_system_tool
        
        @override_system_tool("system_delegate_parallel")
        async def my_custom_parallel_delegation(agent_name: str, tasks: list[str], **kwargs):
            # Your custom implementation
            print(f"Custom parallel delegation: {len(tasks)} tasks to {agent_name}")
            return {"status": "success", "results": [...]}
    
    Args:
        tool_name: Name of the system tool to override (e.g., "system_delegate_parallel")
    
    Returns:
        Decorator function that registers the override
    """
    def decorator(func: Callable) -> Callable:
        _TOOL_OVERRIDES[tool_name] = func
        
        # Also register common aliases
        if tool_name == "system_delegate_parallel":
            _TOOL_OVERRIDES["delegate_parallel"] = func
        elif tool_name == "system_split_document":
            _TOOL_OVERRIDES["split_document"] = func
        elif tool_name == "system_delegate_task":
            _TOOL_OVERRIDES["delegate_task"] = func
        
        logger.info(f"✅ Registered tool override: {tool_name} -> {func.__name__}")
        return func
    
    return decorator


def get_tool_override(tool_name: str) -> Callable | None:
    """
    Get a tool override if it exists.
    
    Args:
        tool_name: Name of the tool to check
    
    Returns:
        The override function if registered, None otherwise
    """
    return _TOOL_OVERRIDES.get(tool_name)


def clear_tool_overrides():
    """Clear all tool overrides. Useful for testing."""
    global _TOOL_OVERRIDES
    _TOOL_OVERRIDES = {}
    logger.info("Cleared all tool overrides")


def list_tool_overrides() -> dict[str, str]:
    """
    List all registered tool overrides.
    
    Returns:
        Dict mapping tool names to their override function names
    """
    return {
        name: func.__name__ 
        for name, func in _TOOL_OVERRIDES.items()
    }


class TaskDelegationTool:
    """Tool for delegating tasks to other agents."""

    def __init__(self, message_bus, artifact_storage=None, agent=None):
        """
        Initialize task delegation tool.
        
        Args:
            message_bus: Message queue backend for inter-agent communication
            artifact_storage: Optional storage backend for large payloads
            agent: Optional agent instance for accessing current_job_id
        """
        self.message_bus = message_bus
        self.artifact_storage = artifact_storage
        self.agent = agent
        self._size_threshold_kb = 100  # Store payloads > 100KB in artifact registry

    async def delegate_task(
        self,
        agent_name: str,
        task_description: str | None = None,
        task: str | None = None,
        task_data: dict | None = None,
        wait_for_response: bool = True,  # Changed default to True for blocking delegation
        timeout_seconds: int = 90,  # Increased default timeout
        timeout: int | None = None,  # Backward compatibility alias
        parent_job_id: str | None = None,  # Injected by agent runtime at execution time
        **kwargs
    ) -> dict:
        """
        Delegate a task to another agent for execution.

        Use this to assign specialized work to other agents (e.g., delegate research to 'researcher', analysis to 'analyst').

        Parameters:
        - agent_name: Name of the target agent (e.g., "researcher", "analyst", "writer")
        - task_description: Clear description of what you need the agent to do
        - task_data: Optional structured data/context for the task
        - wait_for_response: If true, blocks until agent completes and returns full result (default: True)
        - timeout_seconds: Max seconds to wait if wait_for_response=true (default 90)
        - timeout: Alias for timeout_seconds (backward compatibility)

        Returns:
        - task_id: Unique identifier for tracking
        - status: "queued", "completed", or "timeout"
        - response: If wait_for_response=true and agent completed, contains the full result
          - If response size < 100KB: Full data is in 'response' field directly
          - If response size > 100KB: Data is in storage, retrieve using the artifact reference

        IMPORTANT: 
        - If wait_for_response=true and status="completed", the 'response' field contains the FULL result
        - You do NOT need to call retrieve_artifact unless response explicitly says {"stored_in_registry": true}
        - task_id is for tracking only, NOT for artifact retrieval
        """
        import sys
        # Backward compatibility: accept "timeout" as alias for "timeout_seconds"
        if timeout is not None:
            timeout_seconds = timeout
        
        # Backwards-compatible param mapping: accept either `task_description` or
        # `task` (some LLMs produce `task`), and normalize to payload.description
        task_data = task_data or {}
        desc = task_description or task or kwargs.get("task_description") or kwargs.get("description") or ""

        # Build task payload
        payload = {
            "description": desc,
            "data": task_data,
            "delegated_at": datetime.utcnow().isoformat()
        }

        # CRITICAL: Propagate job_id from parent agent to maintain single job context
        # This ensures all traces from delegated agents belong to the same job
        # Priority: 1) Injected parent_job_id (runtime), 2) Agent's current_job_id (fallback)
        job_id_to_use = parent_job_id
        if not job_id_to_use and self.agent and hasattr(self.agent, 'current_job_id'):
            job_id_to_use = self.agent.current_job_id
        
        # DEBUG: Show agent identity and state
        agent_id = id(self.agent) if self.agent else None
        agent_name_debug = getattr(self.agent.config, 'name', 'unknown') if self.agent and hasattr(self.agent, 'config') else 'unknown'
        print(f"[DELEGATION DEBUG] agent_id={agent_id}, agent_name={agent_name_debug}, has_current_job_id={hasattr(self.agent, 'current_job_id') if self.agent else False}, agent.job_id={self.agent.current_job_id if self.agent and hasattr(self.agent, 'current_job_id') else None}, injected_parent_job_id={parent_job_id}, final_job_id={job_id_to_use}", file=sys.stderr, flush=True)
        
        if job_id_to_use:
            if "job_id" not in payload:
                payload["job_id"] = job_id_to_use
                print(f"[DELEGATION] ✓ Propagating job_id={job_id_to_use} to {agent_name}", file=sys.stderr, flush=True)
        else:
            print(f"[DELEGATION WARNING] ✗ No job_id to propagate from agent {agent_name_debug}", file=sys.stderr, flush=True)

        # Check if payload is too large and should be stored in artifact registry
        payload_size_kb = len(json.dumps(payload).encode()) / 1024
        artifact_id = None

        if self.artifact_storage and payload_size_kb > self._size_threshold_kb:
            # Store in artifact registry
            artifact_id = await self._store_artifact(payload)
            payload = {
                "artifact_id": artifact_id,
                "artifact_size_kb": payload_size_kb,
                "description": task_description
            }

        # Publish task to message queue
        task_id = await self.message_bus.publish_task(agent_name, payload)

        result = {
            "task_id": task_id,
            "agent_name": agent_name,
            "status": "queued"
        }

        if artifact_id:
            result["artifact_id"] = artifact_id
            result["stored_in_registry"] = True

        # Wait for response if requested
        if wait_for_response:
            response = await self.message_bus.wait_for_response(
                task_id,
                timeout_sec=timeout_seconds
            )

            if response:
                result["status"] = "completed"
                
                # Check if response was offloaded to storage (>100KB)
                if isinstance(response, dict) and response.get("offloaded"):
                    # Response is a pointer to stored data
                    result["response_offloaded"] = True
                    result["response_storage"] = {
                        "bucket": response.get("bucket"),
                        "key": response.get("key"),
                        "size_bytes": response.get("size_bytes")
                    }
                    result["note"] = "Large response stored in Artifact Registry. Use retrieve_artifact with bucket/key to fetch if needed."
                # Check if response contains artifact_id (legacy artifact storage)
                elif isinstance(response, dict) and "artifact_id" in response:
                    artifact_data = await self._retrieve_artifact(response["artifact_id"])
                    if artifact_data:
                        result["response"] = artifact_data
                    else:
                        result["response"] = response
                        result["artifact_retrieval_failed"] = True
                else:
                    # Response is inline, directly available
                    result["response"] = response
            else:
                result["status"] = "timeout"
                result["error"] = f"No response after {timeout_seconds}s"

        return result

    async def _store_artifact(self, data: dict) -> str:
        """Store large payload in artifact registry."""
        artifact_id = str(uuid.uuid4())

        if self.artifact_storage:
            await self.artifact_storage.put_object(
                bucket="laddr-artifacts",
                key=f"tasks/{artifact_id}.json",
                data=json.dumps(data).encode()
            )

        return artifact_id

    async def _retrieve_artifact(self, artifact_id: str) -> dict | None:
        """Retrieve artifact from registry."""
        if not self.artifact_storage:
            return None

        try:
            data = await self.artifact_storage.get_object(
                bucket="laddr-artifacts",
                key=f"tasks/{artifact_id}.json"
            )
            return json.loads(data.decode())
        except Exception:
            return None


class ArtifactStorageTool:
    """Tool for storing and retrieving large data artifacts.

    Backward-compatible retrieval:
    - Old style: by artifact_id and artifact_type (stored under default artifact bucket)
    - New style: by bucket+key (e.g., offloaded response pointers)
    """

    def __init__(self, storage_backend):
        """
        Initialize artifact storage tool.
        
        Args:
            storage_backend: Storage backend (MinIO/S3)
        """
        self.storage = storage_backend

    async def store_artifact(
        self,
        data: str | bytes | dict,
        artifact_type: str = "generic",
        metadata: dict | None = None
    ) -> dict:
        """
        Store large data in artifact registry (MinIO/S3).
        
        Args:
            data: Data to store (string, bytes, or dict which will be JSON-serialized)
            artifact_type: Type label (e.g., "result", "dataset", "file")
            metadata: Optional metadata dict
        
        Returns:
            Dict with artifact_id, size, and storage location
        """
        artifact_id = str(uuid.uuid4())

        # Convert data to bytes
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode()
        elif isinstance(data, str):
            data_bytes = data.encode()
        else:
            data_bytes = data

        # Store in artifact registry
        bucket = "laddr-artifacts"
        key = f"{artifact_type}/{artifact_id}"

        await self.storage.put_object(
            bucket=bucket,
            key=key,
            data=data_bytes,
            metadata=metadata or {}
        )

        return {
            "artifact_id": artifact_id,
            "type": artifact_type,
            "size_bytes": len(data_bytes),
            "size_kb": round(len(data_bytes) / 1024, 2),
            "location": f"{bucket}/{key}",
            "stored_at": datetime.utcnow().isoformat()
        }

    async def retrieve_artifact(
        self,
        artifact_id: str | None = None,
        artifact_type: str = "generic",
        bucket: str | None = None,
        key: str | None = None,
    ) -> dict:
        """
        Retrieve previously stored artifact data using its artifact_id.
        
        IMPORTANT: Only use this tool if:
        1. You previously called store_artifact and received an artifact_id
        2. A delegation response explicitly contains {"stored_in_registry": true, "artifact_id": "..."}

        Parameters:
        - artifact_id (required): The UUID returned from store_artifact
        - artifact_type (optional): Type label like "generic", "result", etc
        - bucket (optional): For direct MinIO retrieval (advanced usage)
        - key (optional): For direct MinIO retrieval (advanced usage)

        DO NOT use this tool with task_id, job_id, or other identifiers. Only use artifact_id.
        If delegation response contains data directly, you already have the full result - no retrieval needed.

        Returns:
            Dict with artifact data, metadata, and retrieval info
        """
        # New path: direct bucket/key retrieval (e.g., offloaded responses)
        # NOTE: artifact storage uses the bucket "laddr-artifacts" by default
        # for stored task artifacts. Use that as the default to avoid confusing
        # callers that pass only a key or a job id.
        if key is not None:
            use_bucket = bucket or "laddr-artifacts"
            try:
                data = await self.storage.get_object(bucket=use_bucket, key=key)
                try:
                    parsed_data = json.loads(data.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    parsed_data = data.decode(errors='replace')

                return {
                    "bucket": use_bucket,
                    "key": key,
                    "data": parsed_data,
                    "size_bytes": len(data),
                    "retrieved_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                return {
                    "bucket": use_bucket,
                    "key": key,
                    "error": str(e),
                    "status": "not_found",
                }

        # Legacy path: artifact registry lookup by id/type
        bucket = "laddr-artifacts"
        if not artifact_id:
            return {
                "error": "artifact_id or (bucket and key) is required",
                "status": "invalid_params",
            }
        legacy_key = f"{artifact_type}/{artifact_id}"

        try:
            data = await self.storage.get_object(bucket=bucket, key=legacy_key)
            try:
                parsed_data = json.loads(data.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                parsed_data = data.decode(errors='replace')

            return {
                "artifact_id": artifact_id,
                "type": artifact_type,
                "data": parsed_data,
                "size_bytes": len(data),
                "retrieved_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "artifact_id": artifact_id,
                "error": str(e),
                "status": "not_found",
            }

    async def list_artifacts(
        self,
        artifact_type: str | None = None,
        limit: int = 20
    ) -> dict:
        """
        List artifacts in storage.
        
        Args:
            artifact_type: Optional type filter
            limit: Max number of artifacts to return
        
        Returns:
            Dict with list of artifact metadata
        """
        bucket = "laddr-artifacts"
        prefix = f"{artifact_type}/" if artifact_type else ""

        try:
            objects = await self.storage.list_objects(
                bucket=bucket,
                prefix=prefix,
                max_keys=limit
            )

            artifacts = []
            for obj in objects:
                # Extract artifact_id from key
                parts = obj["key"].split("/")
                artifact_id = parts[-1] if parts else obj["key"]

                artifacts.append({
                    "artifact_id": artifact_id,
                    "type": parts[0] if len(parts) > 1 else "generic",
                    "size_bytes": obj.get("size", 0),
                    "last_modified": obj.get("last_modified")
                })

            return {
                "artifacts": artifacts,
                "count": len(artifacts),
                "bucket": bucket
            }

        except Exception as e:
            return {
                "error": str(e),
                "artifacts": []
            }


class ParallelDelegationTool:
    """Tool for delegating multiple tasks in parallel (sharding/fan-out pattern)."""

    def __init__(self, message_bus, artifact_storage=None, agent=None):
        """
        Initialize parallel delegation tool.
        
        Args:
            message_bus: Message queue backend for inter-agent communication
            artifact_storage: Optional storage backend for large payloads
            agent: Optional agent instance for job context propagation
        """
        self.message_bus = message_bus
        self.artifact_storage = artifact_storage
        self.agent = agent
        self.delegation_tool = TaskDelegationTool(message_bus, artifact_storage, agent)

    async def delegate_parallel(
        self,
        agent_name: str | None = None,
        tasks: list[str] | None = None,
        timeout_seconds: int = 120,
        **kwargs: Any,
    ) -> dict:
        """
        Delegate multiple tasks to workers in parallel and wait for all results.
        
        Use this for sharding/fan-out patterns when you need to process multiple
        independent chunks of work simultaneously (e.g., splitting a large document
        into sections and processing them in parallel).

        Parameters:
        - agent_name: Target agent name (e.g., "researcher"). Also accepts 'agent' (alias).
        - tasks: List of task descriptions to delegate (e.g., ["analyze section 1", "analyze section 2"]).
                 Each task should be a SHORT description or the actual chunk content to process.
        - timeout_seconds: Max seconds to wait per task (default 120). Also accepts 'timeout' (alias).

        Returns:
        - status: "success" (all completed), "partial" (some failed), or "failed" (all failed)
        - results: List of task results with their status
        - completed: Number of successful tasks
        - failed: Number of failed tasks
        - total: Total number of tasks
        """
        import asyncio
        import time
        # Use UTC ISO timestamps with 'Z' suffix for clarity
        from datetime import datetime as _dt

        # Backward/LLM-friendly parameter aliases
        if agent_name is None:
            agent_name = kwargs.get("agent")
        if tasks is None:
            tasks = kwargs.get("tasks")
        # Prefer explicit timeout_seconds but allow 'timeout'
        if "timeout" in kwargs and (timeout_seconds is None or timeout_seconds == 120):
            try:
                timeout_seconds = int(kwargs["timeout"])  # type: ignore[arg-type]
            except Exception:
                pass

        if not agent_name:
            return {"status": "error", "error": "agent_name (or 'agent') is required"}
        if not tasks or not isinstance(tasks, list):
            return {"status": "error", "error": "tasks must be a non-empty list of strings"}

        async def delegate_one(task_desc: str, index: int) -> dict:
            """Delegate a single task."""
            try:
                _started_at = _dt.utcnow().isoformat() + "Z"
                _t0 = time.perf_counter()
                result = await self.delegation_tool.delegate_task(
                    agent_name=agent_name,
                    task_description=task_desc,
                    wait_for_response=True,
                    timeout_seconds=timeout_seconds
                )
                _duration_ms = int((time.perf_counter() - _t0) * 1000)
                _ended_at = _dt.utcnow().isoformat() + "Z"
                return {
                    "index": index,
                    "task": task_desc,
                    "worker": (result or {}).get("agent_name", agent_name),
                    "started_at": _started_at,
                    "ended_at": _ended_at,
                    "duration_ms": _duration_ms,
                    "result": result,
                    "status": "success"
                }
            except Exception as e:
                _ended_at = _dt.utcnow().isoformat() + "Z"
                return {
                    "index": index,
                    "task": task_desc,
                    "worker": agent_name,
                    "started_at": _started_at if '_started_at' in locals() else None,
                    "ended_at": _ended_at,
                    "duration_ms": int((time.perf_counter() - _t0) * 1000) if '_t0' in locals() else None,
                    "error": str(e),
                    "status": "failed"
                }

        # Execute all delegations in parallel
        results = await asyncio.gather(
            *[delegate_one(task, i) for i, task in enumerate(tasks)],
            return_exceptions=True
        )

        # Handle exceptions and aggregate results
        processed_results = []
        for r in results:
            if isinstance(r, Exception):
                processed_results.append({
                    "error": str(r),
                    "status": "failed"
                })
            else:
                processed_results.append(r)

        # Calculate stats
        completed = sum(1 for r in processed_results if r.get("status") == "success")
        failed = len(processed_results) - completed

        return {
            "status": "success" if failed == 0 else ("partial" if completed > 0 else "failed"),
            "results": processed_results,
            "completed": completed,
            "failed": failed,
            "total": len(tasks)
        }

    def split_document(
        self,
        document: str,
        num_chunks: int = 3,
        overlap: int = 0
    ) -> dict:
        """
        Split a large document into smaller chunks for parallel processing.
        
        Use this before calling delegate_parallel to divide large documents
        into manageable sections that can be processed by multiple workers.

        Parameters:
        - document: The document text to split
        - num_chunks: Number of chunks to split into (e.g., 3 for 3 workers)
        - overlap: Number of characters to overlap between chunks (for context continuity)

        Returns:
        - chunks: List of document chunks
        - metadata: Information about the split (lengths, chunk count, etc.)
        """
        doc_len = len(document)
        
        if num_chunks <= 0:
            num_chunks = 3
        
        if num_chunks == 1:
            return {
                "chunks": [document],
                "metadata": {
                    "original_length": doc_len,
                    "chunk_sizes": [doc_len],
                    "num_chunks": 1,
                    "overlap": 0
                }
            }

        # Helper: choose a split point near target on whitespace to avoid mid-word cuts
        def nearest_whitespace(target: int, low: int, high: int) -> int:
            target = max(low, min(high, target))
            window = 200  # search window on either side
            left = max(low, target - window)
            right = min(high, target + window)
            best = None
            best_dist = None
            for idx in range(target, left - 1, -1):
                if document[idx:idx+1].isspace():
                    best = idx
                    best_dist = abs(idx - target)
                    break
            if best is None:
                for idx in range(target, right + 1):
                    if document[idx:idx+1].isspace():
                        best = idx
                        best_dist = abs(idx - target)
                        break
            return best if best is not None else target

        # Calculate approximate equal segments
        base = doc_len // num_chunks
        indices = [0]
        for i in range(1, num_chunks):
            target = i * base
            # ensure monotonic increase
            low = indices[-1] + 1
            high = doc_len - 1
            split_at = nearest_whitespace(target, low, high)
            indices.append(split_at)
        indices.append(doc_len)

        # Build chunks with optional overlap (character-based)
        chunks = []
        for i in range(num_chunks):
            start = indices[i]
            end = indices[i+1]
            # apply overlap: extend end by overlap for all but last, and start backward for all but first
            start_o = max(0, start - (overlap if i > 0 else 0))
            end_o = min(doc_len, end + (overlap if i < num_chunks - 1 else 0))
            chunks.append(document[start_o:end_o])
        
        return {
            "chunks": chunks,
            "metadata": {
                "original_length": doc_len,
                "chunk_sizes": [len(c) for c in chunks],
                "num_chunks": len(chunks),
                "overlap": overlap
            }
        }


def create_system_tools(message_bus, storage_backend=None, agent=None) -> dict[str, tuple[Any, list[str]]]:
    """
    Create system tools for task delegation and artifact management.
    
    This function checks for user-provided overrides before registering
    the default implementations. Users can use @override_system_tool 
    decorator to replace any system tool.
    
    Args:
        message_bus: Message queue backend
        storage_backend: Optional storage backend (MinIO/S3)
        agent: Optional agent instance for accessing current_job_id context
    
    Returns:
        Dict mapping tool names to (tool_function, aliases) tuples
    """
    tools = {}

    # Task delegation tool (with agent context for job_id propagation)
    override = get_tool_override("system_delegate_task")
    if override:
        logger.info("✅ Using custom override for system_delegate_task")
        tools["system_delegate_task"] = (override, [])
    else:
        delegation_tool = TaskDelegationTool(message_bus, storage_backend, agent=agent)
        tools["system_delegate_task"] = (delegation_tool.delegate_task, [])

    # Parallel delegation and document splitting tools WITH ALIASES
    parallel_tool = ParallelDelegationTool(message_bus, storage_backend, agent=agent)
    
    # Register with aliases instead of duplicate entries
    override = get_tool_override("system_delegate_parallel")
    if override:
        logger.info("✅ Using custom override for system_delegate_parallel")
        tools["system_delegate_parallel"] = (override, ["delegate_parallel"])
    else:
        tools["system_delegate_parallel"] = (
            parallel_tool.delegate_parallel,
            ["delegate_parallel"]  # Friendly alias
        )
    
    override = get_tool_override("system_split_document")
    if override:
        logger.info("✅ Using custom override for system_split_document")
        tools["system_split_document"] = (override, ["split_document"])
    else:
        tools["system_split_document"] = (
            parallel_tool.split_document,
            ["split_document"]  # Friendly alias
        )

    # Artifact storage tools (if storage backend available)
    if storage_backend:
        artifact_tool = ArtifactStorageTool(storage_backend)
        
        override = get_tool_override("system_store_artifact")
        if override:
            logger.info("✅ Using custom override for system_store_artifact")
            tools["system_store_artifact"] = (override, [])
        else:
            tools["system_store_artifact"] = (artifact_tool.store_artifact, [])
        
        override = get_tool_override("system_retrieve_artifact")
        if override:
            logger.info("✅ Using custom override for system_retrieve_artifact")
            tools["system_retrieve_artifact"] = (override, [])
        else:
            tools["system_retrieve_artifact"] = (artifact_tool.retrieve_artifact, [])
        
        override = get_tool_override("system_list_artifacts")
        if override:
            logger.info("✅ Using custom override for system_list_artifacts")
            tools["system_list_artifacts"] = (override, [])
        else:
            tools["system_list_artifacts"] = (artifact_tool.list_artifacts, [])

    return tools
