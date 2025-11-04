# Recipes and edge cases

This page collects practical snippets for common edge cases.

## Force response offloading and retrieve

Set a tiny threshold so responses are offloaded to MinIO:

```bash
STORAGE_THRESHOLD_KB=1
```

When a delegated task returns an offloaded response, the message contains a pointer:

```json
{
  "offloaded": true,
  "bucket": "laddr",
  "key": "responses/2025/10/31/<task_id>.json",
  "size_bytes": 123456
}
```

Retrieve it using the system tool (bucket/key path):

```python
from laddr.core.system_tools import ArtifactStorageTool
# In runtime this is already bound as a tool; here is the direct form:
artifact = await artifact_tool.retrieve_artifact(bucket="laddr", key="responses/2025/10/31/<task_id>.json")
print(artifact["data"])
```

## Retrieve by artifact_id (legacy/manual storage)

If you stored an artifact with `store_artifact` and got an `artifact_id`:

```python
stored = await artifact_tool.store_artifact({"data": "big"}, artifact_type="result")
artifact_id = stored["artifact_id"]
retrieved = await artifact_tool.retrieve_artifact(artifact_id=artifact_id)
```

## Delegation: inline vs offloaded response

```python
result = await delegate_task(
  agent_name="researcher",
  task_description="Find top 3 sources",
  task_data={"query": "laddr agents"},
  wait_for_response=True,
)
if result.get("response_offloaded"):
    pointer = result["response_storage"]
    # Use retrieve_artifact(bucket=..., key=...)
else:
    data = result["response"]  # Inline small response
```

## Tracing: reduce noise

```python
agent = Agent(..., trace_enabled=True, trace_mask=["llm_call", "tool_result"])  # hide chat and tool payloads
```

## CLI: run agent locally without Redis/Postgres

```bash
laddr run-local researcher --input '{"topic": "RAG patterns"}'
```

This injects defaults (`DATABASE_URL=sqlite:///laddr.db`, in-memory queue) and imports agents from CWD.
