# Laddr REST API

**Base URL:** `http://localhost:8000`

---

## `GET /`

Returns basic API information such as name, version, and documentation links.

**Response Example:**
```json
{
  "service": "Laddr API",
  "version": "0.8.0",
  "status": "running",
  "dashboard": "http://localhost:5173",
  "docs": "/docs"
}
```

---

## `GET /api/health`

Checks the health of the Laddr system and its connected services such as the database, message bus, and storage backend.

**Response Example:**
```json
{
    "status": "ok",
    "version": "0.8.0",
    "components": {
        "database": db_type,
        "storage": storage_type,
        "message_bus": queue_type
    }
}
```

---

## `POST /api/jobs`

Submit a new job for execution by providing the pipeline name and input data.

**Request Body Example:**
```json
{
  "pipeline_name": "text_analysis_agent",
  "inputs": {
    "text": "Analyze this message for sentiment"
  }
}
```

**Response Example:**
```json
{
  "job_id": "job_1b203f",
  "status": "queued",
  "created_at": "2025-11-08T18:45:00Z"
}
```

---

## `GET /api/jobs`

Fetch a list of recent jobs with pagination support.

**Query Parameters:**
- `limit` (optional): Number of jobs to return (default: 50)
- `offset` (optional): Skip a number of jobs (default: 0)

**Response Example:**
```json
[
  {
    "job_id": "job_1b203f",
    "pipeline_name": "text_analysis_agent",
    "status": "completed",
    "created_at": "2025-11-08T18:45:00Z"
  },
  {
    "job_id": "job_1b202b",
    "pipeline_name": "image_classification_agent",
    "status": "failed",
    "created_at": "2025-11-08T18:40:00Z"
  }
]
```

---

## `GET /api/jobs/{job_id}`

Retrieve details for a specific job, including inputs, outputs, and execution metadata.

**Response Example:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "pipeline_name": "analyzer",
  "inputs": {"numbers": [1,2,3,4,5]},
  "outputs": {"sum": 15, "average": 3.0},
  "error": null,
  "created_at": "2025-11-03T16:40:04.630542Z",
  "completed_at": "2025-11-03T16:40:05.234720Z",
  "token_usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

---

## `POST /api/jobs/{job_id}/replay`

Replay a previous job.

**Request Body Example:**
```json
{
  "job_id": "...",
  "request: True
}
```

**Response Example:**
```json
{
  "job_id": "uuid (new or same)",
  "status": "completed",
  "result": "Job result",
  "replayed": true,
  "original_job_id": "original-uuid"
}
```

---

## `POST /api/prompts`

Submit a new prompt execution request.  
Supports both **single-agent** and **sequential multi-agent** execution modes.

**Request Body Example:**
```json
{
    "prompt_name": "writer",
    "inputs": {"task": "Write a haiku"}
    "mode": "single" // or "sequential"
    "agents": ["analyzer", "writer"] // optional for sequential
}
```

**Response Example:**
```json
{
  "prompt_id": "uuid",
  "status": "running",
  "agent": "writer",
  "mode": "single",
  "agents": ["writer"]
}
```

---

## `GET /api/prompts?limit=50`

Retrieve a list of recent prompt executions.

**Query Parameters:**
- `limit` (optional): Number of prompts to return (default: 50)
- `offset` (optional): Skip a number of prompts (default: 0)

**Response Example:**
```json
{
  "prompts": [
    {
      "prompt_id": "uuid",
      "status": "completed",
      "prompt_name": "writer",
      "created_at": "2025-11-03T16:39:52.113651Z",
      "completed_at": "2025-11-03T16:39:54.234720Z"
    }
  ],
  "limit": 50
}
```

---

## `GET /api/prompts/{prompt_id}`

Get the current status, outputs, and trace summary of a specific prompt execution.

**Response Example:**
```json
{
  "prompt_id": "uuid",
  "status": "completed",
  "prompt_name": "writer",
  "inputs": {"task": "Write a haiku"},
  "outputs": {"result": "Haiku text..."},
  "error": null,
  "created_at": "2025-11-03T16:39:52.113651Z",
  "completed_at": "2025-11-03T16:39:54.234720Z",
  "token_usage": {
    "prompt_tokens": 150,
    "completion_tokens": 75,
    "total_tokens": 225
  }
}
```



## `GET /api/agents`

List all registered agents with metadata and available tools.

**Response Example:**
```json
{
  "agents": [
    {
      "name": "writer",
      "role": "Content Writer",
      "goal": "Generate high-quality content",
      "status": "active",
      "tools": ["format_json", "parse_csv"],
      "last_seen": "2025-11-03T16:30:00.000000Z"
    }
  ]
}
```

---

## `GET /api/agents/{agent_name}/chat`

Send a chat message to a specific agent and receive its reply.

**Query Parameters:**
- `message`: The text message to send
- `timeout`: Optional response timeout (seconds)
- `wait`: boolean value

**Response Example:**
```json
// wait=true (successful)
{
  "task_id": "uuid",
  "status": "completed",
  "result": "Agent's response text or structured data",
  "agent": "writer"
}

// wait=false (async)
{
  "task_id": "uuid",
  "status": "submitted"
}

// timeout
{
  "task_id": "uuid",
  "status": "timeout",
  "message": "Agent did not respond in time"
}
```


## `GET /api/traces`

Retrieve a list of trace events across all agents and jobs.

**Query Parameters:**
- `limit` (optional): Number of traces to return
- `job_id` (optional): Filter by job ID
- `agent` (optional): Filter by agent name

**Response Example:**
```json
{
  "traces": [
    {
      "id": 510,
      "job_id": "d780d103-a860-4536-98a7-1deed7097cb9",
      "agent_name": "writer",
      "event_type": "task_error",
      "payload": {
        "error": "LLM generation failed: ...",
        "worker": "writer",
        "ended_at": "2025-11-03T16:40:07.323933Z"
      },
      "timestamp": "2025-11-03T16:40:07.324541Z"
    }
  ]
}
```

---

## `GET /api/traces/grouped?limit=50`

Retrieve traces grouped by job ID, showing all events related to each execution.

**Query Parameters:**
- `limit` (optional): Number of traces to return

**Response Example:**
```json
{
  "grouped_traces": [
    {
      "job_id": "d780d103-a860-4536-98a7-1deed7097cb9",
      "trace_count": 2,
      "agents": ["writer"],
      "start_time": "2025-11-03T16:40:07.315138Z",
      "end_time": "2025-11-03T16:40:07.324541Z",
      "traces": [
        {
          "id": 509,
          "job_id": "d780d103-a860-4536-98a7-1deed7097cb9",
          "agent_name": "writer",
          "event_type": "task_start",
          "payload": {...},
          "timestamp": "2025-11-03T16:40:07.315138Z"
        },
        {
          "id": 510,
          "job_id": "d780d103-a860-4536-98a7-1deed7097cb9",
          "agent_name": "writer",
          "event_type": "task_error",
          "payload": {...},
          "timestamp": "2025-11-03T16:40:07.324541Z"
        }
      ]
    }
  ]
}
```

---

## `GET /api/traces/{trace_id}`

Retrieve details of a specific trace, including payload, timestamps, and linked job.

**Response Example:**
```json
{
  "id": 510,
  "job_id": "d780d103-a860-4536-98a7-1deed7097cb9",
  "agent_name": "writer",
  "event_type": "task_error",
  "payload": {
    "error": "LLM generation failed: openai package not installed",
    "worker": "writer",
    "ended_at": "2025-11-03T16:40:07.323933Z"
  },
  "timestamp": "2025-11-03T16:40:07.324541Z"
}
```

---

## `GET /api/metrics`

Get aggregated system metrics.

**Response Example:**
```json
{
  "total_jobs": 16,
  "avg_latency_ms": 0,
  "active_agents_count": 5,
  "cache_hits": 0,
  "tool_calls": 0,
  "timestamp": "2025-11-03T16:40:30.429696Z"
}
```

---

## `GET /api/responses/{task_id}/resolved`

Retrieve a resolved response payload, including any data that was offloaded to object storage.

**Response Example:**
```json
// Inline response
{
  "task_id": "uuid",
  "offloaded": false,
  "pointer": null,
  "data": {
    "result": "Agent response data"
  }
}

// Offloaded response
{
  "task_id": "uuid",
  "offloaded": true,
  "pointer": {
    "bucket": "laddr",
    "key": "responses/task-uuid",
    "size_bytes": 524288
  },
  "data": {
    "result": "Large agent response data..."
  }
}
```
