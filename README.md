<div align="center">

<img src="./Assets/laddr.svg" alt="Laddr Logo" width="360" height="">

**Distributed agent framework for production-grade AI systems**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-optional-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/redis-7.0+-red.svg)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)](https://www.postgresql.org/)

[Quick Start](#quick-start) • [Features](#features) • [Agent Example](#agent-example) • [Tool Example](#tool-example) • [Dashboard](#dashboard--observability)

<img src="./Assets/dashboard.png" alt="Laddr Logo" width="600" height="315">

</div>

---

## Table of Contents

- [What is Laddr?](#what-is-laddr)
- [Features](#features)
- [Quick Start](#quick-start)
- [Agent Example](#agent-example)
- [Tool Example](#tool-example)
- [FastAPI Runtime](#fastapi-runtime--rest-api)
- [Dashboard & Observability](#dashboard--observability)
- [Architecture](#architecture)
- [License](#license)

---

## What is Laddr?

Laddr is a python framework for building **multi-agent systems** where agents communicate, delegate tasks, and execute work in parallel. Think of it as a microservices architecture for AI agents — with built-in message queues, observability, and horizontal scalability.

### Two Operating Modes

**Coordinator-Orchestrator Mode**  
Dynamic, autonomous workflows where a coordinator agent analyzes tasks, delegates to specialist agents, and synthesizes results. The coordinator makes real-time decisions about routing and orchestration.

**Sequential Deterministic Workflow Mode**  
Pre-defined, predictable pipelines where tasks flow through agents in a fixed sequence. Each step is explicitly defined with inputs, outputs, and dependencies.

---

## Features

### Scalability & Performance
- **Horizontal scaling** — Scale each agent independently based on workload
- **Multi-worker support** — Run multiple workers per agent for high throughput
- **Automatic load balancing** — Redis Streams distribute tasks across workers
- **Fault tolerance** — Worker failures don't stop the system

### Observability & Monitoring
- **Complete tracing** — Every agent action automatically logged (SQLite/PostgreSQL)
- **Langfuse integration** — Optional external tracing with automatic span creation
- **Real-time metrics** — Job status, duration, success rates, queue depth
- **Interactive dashboard** — Beautiful UI to monitor agents, traces, batches, and logs
- **Playground** — Test agents interactively with live streaming responses

### Developer Experience
- **Clean CLI** — Minimal, modern interface for project management
- **Hot reload** — Code changes reflect instantly in development mode
- **Type safety** — Full Python type hints throughout the codebase
- **Simple setup** — One command (`laddr init`) to scaffold complete projects

### AI-Optimized Architecture
- **Built-in delegation** — Agents can delegate tasks to other agents seamlessly
- **Batch operations** — Execute multiple tasks in parallel with full tracking and WebSocket monitoring
- **Parallel execution** — Process multiple independent tasks simultaneously
- **Context management** — Automatic artifact storage for large payloads (>1MB)
- **Smart retries** — Configurable retry logic and timeout handling per agent

### Production Ready
- **Docker native** — Everything runs in containers with docker-compose
- **Queue-based messaging** — Redis Streams for reliable, distributed communication
- **Artifact storage** — MinIO/S3 for handling large files and documents
- **REST API** — FastAPI server with auto-generated OpenAPI documentation
- **API security** — Optional API key authentication for all endpoints

### Extensibility
- **Custom tools** — Add any Python function as an agent tool with `@tool` decorator
- **Override system tools** — Extend delegation and storage with your own implementations
- **LLM agnostic** — Works with Gemini, OpenAI, Anthropic, Groq, Ollama, and local models
- **Pluggable backends** — Swap Redis, PostgreSQL, or storage providers easily

---

## Quick Start

### Installation

```bash
pip install laddr
```

### Create Your First Project

```bash
# Initialize a new project
laddr init my-agent-system
cd my-agent-system
```

### Configure API Keys

Edit `.env` file:

```bash
# Required for web search tools
SERPER_API_KEY=your_serper_api_key  # Get from https://serper.dev

# LLM API Keys (choose one or more)
GEMINI_API_KEY=your_gemini_key      # Get from https://aistudio.google.com
OPENAI_API_KEY=your_openai_key      # Get from https://platform.openai.com

# Or use Ollama for local models (free, private, offline)
# Install: curl -fsSL https://ollama.ai/install.sh | sh
# Then: ollama pull gemma2:2b
OLLAMA_BASE_URL=http://localhost:11434
LLM_BACKEND=ollama  # Use local models instead of cloud APIs

# Optional: API key authentication
LADDR_API_KEY=your_api_key_here  # Protect API endpoints

# Optional: Langfuse external tracing
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

> 💡 **Using Ollama?** See the [Ollama Integration Guide](docs/guides/ollama-integration.md) for complete setup instructions including Docker configuration.

### Start the System

```bash
# Start all services (API, workers, database, Redis, MinIO)
laddr run dev
```

This starts:
- ✅ **API Server** at `http://localhost:8000`
- ✅ **Dashboard** at `http://localhost:5173`
- ✅ **SQLite** for traces and job history (default, or PostgreSQL if configured)
- ✅ **Redis** for message queue
- ✅ **MinIO** for artifact storage
- ✅ **2 agents**: `coordinator` (orchestrator) and `researcher` (specialist)

### Test Your Agents

Open the dashboard at **http://localhost:5173/playground** or use the API:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "coordinator",
    "inputs": {
      "query": "What are the best hotels in Shimla?"
    }
  }'
```

---

## Agent Example

Agents are defined in simple Python files. Here's what `laddr init` generates:

```python
"""
Coordinator agent - orchestrates research tasks
"""
from laddr import Agent
from laddr.llms import gemini

coordinator = Agent(
    name="coordinator",
    role="Research Task Coordinator",
    goal="Coordinate research tasks by delegating to specialist agents",
    backstory="""You are a research coordinator who manages information 
    gathering tasks. You delegate specific queries to researcher agents 
    and compile their findings into comprehensive summaries.""",
    
    llm=gemini("gemini-2.0-flash"),
    
    # Coordinator can delegate to other agents
    is_coordinator=True,
    available_agents=["researcher"],
    
    # Behavior settings
    max_iterations=15,
    max_tool_calls=50,
    timeout=600,
    
    # Built-in delegation tools provided automatically
    tools=[],
    
    instructions="""
    ## Your workflow:
    1. Receive user query
    2. Delegate research to 'researcher' agent using system_delegate_task
    3. Wait for results (use wait_for_response=true)
    4. Synthesize findings into comprehensive answer
    5. Return final result to user
    
    ## Delegation format:
    {
      "type": "tool",
      "tool": "system_delegate_task",
      "params": {
        "agent_name": "researcher",
        "task": "Search for best hotels in Shimla with reviews",
        "wait_for_response": true,
        "timeout_seconds": 90
      }
    }
    """
)
```

**Key Features:**
- **Coordinators** delegate work to specialists
- **Specialists** use tools to complete tasks
- **LLM-powered** decision making
- **Configurable** behavior and limits
- **Clear instructions** guide agent behavior

---

## Tool Example

Tools are Python functions that agents can call. Here's a web search tool from the template:

```python
"""
Web search tool using Serper.dev API
"""
from typing import Dict
import os
import requests
from laddr import tool

@tool(
    name="web_search",
    description="Search the web using Serper.dev API. Returns title, URL, and snippet for each result.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (be specific for better results)"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (1-10, default 5)",
                "default": 5
            }
        },
        "required": ["query"]
    }
)
def web_search(query: str, max_results: int = 5) -> Dict:
    """
    Search the web and return structured results.
    
    Returns:
        {
            "query": str,
            "results": [
                {
                    "title": str,
                    "link": str,
                    "snippet": str,
                    "site": str
                },
                ...
            ],
            "count": int,
            "status": "success" | "error"
        }
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "error": "SERPER_API_KEY not set"
        }
    
    response = requests.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={"q": query, "num": max_results},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get("organic", [])[:max_results]:
        results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")[:500],
            "site": item.get("domain", "")
        })
    
    return {
        "query": query,
        "results": results,
        "count": len(results),
        "status": "success"
    }
```

**Features:**
- **@tool decorator** — Automatic registration
- **JSON Schema** — Parameters defined with validation
- **Structured output** — Consistent return format
- **Fast** — 15 second timeout
- **Error handling** — Graceful failures

---

## FastAPI Runtime & REST API

Laddr includes a **production-ready FastAPI server** with comprehensive REST endpoints:

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/jobs` | Submit a job to an agent |
| `GET` | `/api/jobs/{job_id}` | Get job status and result |
| `GET` | `/api/jobs` | List all jobs with filters |
| `POST` | `/api/jobs/{job_id}/replay` | Replay a failed job |
| `GET` | `/api/agents` | List all available agents |
| `GET` | `/api/agents/{agent_name}/tools` | Get agent's tools |
| `GET` | `/api/agents/{agent_name}/chat` | Interactive chat with agent |
| `POST` | `/api/agents/{agent_name}/batch` | Submit multiple tasks in parallel (batch) |
| `GET` | `/api/batches` | List all batch operations |
| `GET` | `/api/batches/{batch_id}` | Get batch status and results |
| `POST` | `/api/batches/{batch_id}/add-tasks` | Add tasks to existing batch |

### Observability Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/traces` | Get execution traces for jobs |
| `GET` | `/api/traces/grouped` | Get traces grouped by job |
| `GET` | `/api/traces/{trace_id}` | Get specific trace details |
| `GET` | `/api/metrics` | Get system metrics (jobs, latency, success rate) |
| `GET` | `/api/logs/containers` | List Docker containers |
| `GET` | `/api/logs/containers/{name}` | Stream container logs |

### Playground Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/prompts` | Create interactive prompt session |
| `GET` | `/api/prompts/{prompt_id}` | Get prompt status and messages |
| `GET` | `/api/prompts` | List all prompt sessions |
| `POST` | `/api/prompts/{prompt_id}/cancel` | Cancel running prompt |

### Example: Submit a Job

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "researcher",
    "inputs": {
      "query": "Latest AI trends 2025"
    }
  }'

# Response:
{
  "job_id": "job_abc123",
  "status": "queued",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Example: Submit Batch Tasks

Execute multiple tasks in parallel:

```bash
curl -X POST http://localhost:8000/api/agents/researcher/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"query": "What is Python?"},
      {"query": "What is JavaScript?"},
      {"query": "What is Rust?"}
    ],
    "wait": false
  }'

# Response:
{
  "batch_id": "batch-abc-123",
  "agent_name": "researcher",
  "status": "submitted",
  "task_count": 3,
  "job_ids": ["job-1", "job-2", "job-3"]
}
```

### API Authentication (Optional)

Set `LADDR_API_KEY` environment variable to enable API key authentication:

```bash
# Using header
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/agents

# Using Bearer token
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/api/agents

# Using query parameter (WebSocket)
ws://localhost:8000/ws/prompts/{prompt_id}?api_key=your-api-key
```

### Example: Get Job Result

```bash
curl http://localhost:8000/api/jobs/job_abc123

# Response:
{
  "job_id": "job_abc123",
  "status": "completed",
  "result": {
    "answer": "Based on my research, the top AI trends in 2025 are...",
    "sources": [...]
  },
  "agent_name": "researcher",
  "created_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:31:45Z",
  "duration_seconds": 105
}
```

### Interactive API Documentation

Full OpenAPI documentation available at:

http://localhost:8000/docs — Swagger UI  
---

## Dashboard & Observability

Laddr includes a **beautiful React dashboard** with real-time monitoring:

### Dashboard Features

 **Playground**
- Test agents interactively
- Live streaming responses
- Token usage tracking
- Save and replay sessions

 **Traces**
- Complete execution history
- Tool calls and results
- LLM interactions
- Delegation flows
- Filter by job, agent, or time range
- Job ID filtering for focused trace views

 **Batches**
- View all batch operations
- Real-time batch progress monitoring
- Detailed batch execution traces
- Task result aggregation
- WebSocket streaming for live updates

 **Metrics**
- System health overview
- Jobs per agent (success/failed)
- Average latency per agent
- Queue depth monitoring
- Worker status

 **Logs**
- Real-time container logs
- Filter by agent or service
- Error highlighting
- Download logs

 **Agents**
- List all agents and their tools
- Agent configuration viewer
- Worker scaling controls
- Health status

### Access the Dashboard

```bash
# Start the system
laddr run dev

# Open dashboard in browser
open http://localhost:5173
```

**Views:**
- `/` — Dashboard home with metrics
- `/playground` — Interactive agent testing
- `/traces` — Execution traces and history
- `/batches` — Batch operations management
- `/agents` — Agent management
- `/logs` — Container logs viewer
- `/settings` — Configuration

---

## Architecture

### Message Bus (Redis Streams)

Laddr uses **Redis Streams** for reliable, distributed messaging:

- **Agent Queues** — Each agent has a dedicated stream (`laddr:agent:{name}`)
- **Response Streams** — Temporary streams for delegation responses
- **Consumer Groups** — Multiple workers consume from the same stream
- **Automatic Load Balancing** — Redis distributes tasks across workers
- **Persistence** — Messages persisted until acknowledged
- **Backpressure** — Queue depth monitoring prevents overload

**Example flow:**
```
API → Redis Stream → Worker 1, Worker 2, Worker 3
                      ↓
                    Process task
                      ↓
                 Store result in Postgres
```

### Trace Storage (SQLite/PostgreSQL)

All agent executions are **automatically traced** to the database:

- **Default: SQLite** — Simple, file-based storage (no setup required)
- **PostgreSQL option** — Use `DB_BACKEND=postgres` for production scale
- **Complete history** — Every tool call, LLM interaction, delegation
- **Structured data** — JSON traces with metadata
- **Fast queries** — Indexed by job_id, agent_name, timestamp
- **Langfuse integration** — Optional external tracing (automatic span creation)
- **Smart storage** — Traces disabled with Postgres when Langfuse is enabled

**Trace data includes:**
- Tool calls and results
- LLM prompts and responses
- Delegation events
- Error stack traces
- Token usage
- Latency breakdown

**Langfuse Setup:**
```bash
# Optional: Enable Langfuse external tracing
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Artifact Storage (MinIO/S3)

Large payloads are **automatically stored** in object storage:

- **Automatic threshold** — Messages >1MB stored as artifacts
- **S3-compatible** — MinIO (local) or AWS S3 (production)
- **Efficient messaging** — Only artifact reference sent via Redis
- **Retrieval on demand** — Workers fetch artifacts when needed
- **Configurable** — Set size threshold, retention, bucket names

**Benefits:**
- Reduces Redis memory usage
- Prevents message size limits
- Enables large document processing
- Supports binary data (images, PDFs, etc.)

---

## Custom System Tools

Laddr allows you to **override built-in system tools** (delegation, artifact storage) with your own custom implementations:

```python
from laddr import override_system_tool, TaskDelegationTool

@override_system_tool("system_delegate_task")
async def custom_delegation(
    agent_name: str,
    task_description: str,
    task: str,
    task_data: dict = None,
    timeout_seconds: int = 300,
    _message_bus=None,
    _artifact_storage=None,
    _agent=None
):
    """Custom delegation with logging and metrics."""
    
    # Add your custom logic (logging, rate limiting, etc.)
    logger.info(f"Delegating to {agent_name}: {task_description}")
    
    # Reuse base tool for actual delegation
    delegation_tool = TaskDelegationTool(_message_bus, _artifact_storage, _agent)
    result = await delegation_tool.delegate_task(
        agent_name=agent_name,
        task_description=task_description,
        task=task,
        task_data=task_data,
        timeout_seconds=timeout_seconds
    )
    
    logger.info(f"Delegation completed: {result}")
    return result
```

**Available base tools:**
- `TaskDelegationTool` — Single-task delegation
- `ParallelDelegationTool` — Parallel multi-task delegation
- `ArtifactStorageTool` — Artifact storage and retrieval

**System tools you can override:**
- `system_delegate_task` — Single task delegation
- `system_delegate_parallel` — Parallel task delegation
- `system_store_artifact` — Store data artifacts
- `system_retrieve_artifact` — Retrieve data artifacts

**Learn more:** See the [Custom System Tools Guide](docs/guides/custom-system-tools.md) for complete documentation with advanced patterns like rate limiting, circuit breakers, retries, and metrics.

---

## FAQ

### General

**What is Laddr?**
Laddr is a Python framework for building multi-agent systems where agents communicate, delegate tasks, and execute work in parallel. Think of it as a microservices architecture for AI agents — with built-in message queues, observability, and horizontal scalability.

**How is Laddr different from LangGraph or CrewAI?**
Laddr is designed for production-grade distributed systems with queue-based messaging (Redis Streams), horizontal scaling, and a built-in observability dashboard. It supports both autonomous coordinator-orchestrator workflows and deterministic sequential pipelines.

**What license does Laddr use?**
Laddr is open-source under the Apache 2.0 License.

### Setup & Configuration

**How do I install Laddr?**
```bash
pip install laddr
laddr init my-project
cd my-project
```

**What are the system requirements?**
- Python 3.10+
- Redis 7.0+ (for queue-based messaging)
- PostgreSQL 15+ (optional, for trace storage)
- Docker & Docker Compose (recommended for production)

**Can I run Laddr without Docker?**
Yes. Docker is optional. You can run agents directly with Python, though Docker Compose is recommended for production deployments with Redis and PostgreSQL.

### Architecture

**What are the two operating modes?**
- **Coordinator-Orchestrator Mode**: Dynamic, autonomous workflows where a coordinator agent analyzes tasks, delegates to specialists, and synthesizes results in real-time.
- **Sequential Deterministic Workflow Mode**: Pre-defined pipelines where tasks flow through agents in a fixed sequence with explicit inputs, outputs, and dependencies.

**How do agents communicate?**
Agents communicate via Redis Streams, providing reliable, distributed message queuing with automatic load balancing across workers.

**What is the Dashboard?**
Laddr includes an interactive web dashboard for monitoring agents, traces, batches, and logs in real-time. It also features a playground for testing agents with live streaming responses.

### Scalability

**How does Laddr handle horizontal scaling?**
Each agent can be scaled independently with multiple workers. Redis Streams automatically distribute tasks across workers with built-in load balancing and fault tolerance.

**Can agents delegate tasks to other agents?**
Yes. Built-in delegation allows agents to seamlessly route tasks to other agents, enabling complex multi-step workflows.

### Observability

**What tracing options are available?**
- Built-in tracing with SQLite (dev) or PostgreSQL (prod) storage
- Optional Langfuse integration for external tracing with automatic span creation
- Real-time metrics: job status, duration, success rates, queue depth

### Troubleshooting

**Redis connection fails**
Ensure Redis 7.0+ is running and accessible. Check your `REDIS_URL` environment variable and network connectivity.

**Agent not starting**
Verify Python 3.10+ is installed, dependencies are installed (`pip install -r requirements.txt`), and API keys are configured in `.env`.

**Dashboard not loading**
Ensure the FastAPI runtime is running. The dashboard is served on the default port — check for port conflicts.

**Batch jobs stuck**
Check the dashboard for queue depth and worker status. Ensure Redis Streams are healthy and workers are not overloaded.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Visit us at AgnetLabs**: https://agnetlabs.com
- **Documentation**: https://laddr.agnetlabs.com
- **GitHub**: https://github.com/AgnetLabs/Laddr
- **Issues**: https://github.com/AgnetLabs/Laddr/issues

---

<div align="center">

**Built for production. Designed for scale. Made transparent.**

⭐ **Star us on GitHub** if Laddr helps you build better agent systems!

<!-- [Get Started →](https://docs.laddr.dev) | [View Examples →](docs/guides/recipes.md) | [Join Discord →](#) -->

</div>
