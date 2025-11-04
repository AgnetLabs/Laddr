# API routes

Base URL: `http://localhost:8000`

## Health

```http
GET /api/health
```

Response

```json
{
  "status": "healthy",
  "queue": true,
  "database": true,
  "version": "x.y.z"
}
```

## Submit job (legacy)

```http
POST /api/jobs
Content-Type: application/json

{
  "pipeline_name": "coordinator",
  "inputs": {"topic": "Latest AI agents"}
}
```

Response

```json
{
  "job_id": "...",
  "status": "success",
  "result": {"...": "..."},
  "error": null,
  "duration_ms": 1234,
  "agent": "coordinator"
}
```

## Get job

```http
GET /api/jobs/{job_id}
```

## List jobs

```http
GET /api/jobs?limit=50&offset=0
```

## Replay job

```http
POST /api/jobs/{job_id}/replay
Content-Type: application/json

{"reexecute": false}
```

## Prompts (preferred)

```http
POST /api/prompts
Content-Type: application/json

{
  "prompt_name": "coordinator",
  "inputs": {"topic": "Latest AI agents"}
}
```

```http
GET /api/prompts/{prompt_id}
```

```http
GET /api/prompts?limit=50
```

See also the full module reference in the [Reference Section](../reference/laddr.api.main.md).
