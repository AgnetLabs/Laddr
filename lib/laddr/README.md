# Laddr

**A transparent, Docker-native, observable, distributed agent framework.**

Laddr is a superset of CrewAI that removes excessive abstractions and introduces real distributed runtime, local observability, and explicit agent communication.

## 🎯 Philosophy

CrewAI is too abstract, making it nearly impossible to understand or debug what's happening under the hood.

Laddr fixes this by being:

- **Transparent** — All logic (task flow, prompts, tool calls) visible and traceable
- **Pluggable** — Configure your own queues, databases, models, or tools
- **Observable** — Every agent action recorded via OpenTelemetry
- **Containerized** — Everything runs inside Docker for predictable behavior

> **In short:** Laddr = CrewAI with explicit communication, Docker-native execution, local observability, and zero hidden magic.

## 🏗️ Architecture

### Communication Model

Unlike CrewAI's internal synchronous calls, Laddr uses **Redis Streams** for explicit message passing:

```
Controller → Redis Queue → Agent Worker → Redis Response Stream
```

Each agent runs in its own container and consumes tasks from a dedicated Redis stream.

### Services

- **PostgreSQL** (with pgvector) — Stores traces, job history, agent metadata
- **Redis** — Message bus for task distribution
- **MinIO** — S3-compatible storage for artifacts and large payloads
- **Jaeger** — OpenTelemetry trace collection and visualization
- **Prometheus** — Metrics collection and monitoring
- **API Server** — FastAPI server for job submission and queries
- **Worker Containers** — One per agent, consumes and processes tasks
- **Dashboard** — Real-time monitoring and agent interaction

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd lib/laddr

# Install locally (for now)
pip install -e .
```

### Create a Project

```bash
# Initialize a new project
laddr init my_project

# Navigate to project
cd my_project

# Configure API keys in .env
# Edit .env and add your GEMINI_API_KEY and SERPER_API_KEY

# Start the environment (includes default researcher agent)
laddr run dev
```

This will start all services with a working researcher agent and web_search tool ready to use.

**What's included out-of-the-box:**
- Default `researcher` agent with Gemini 2.0 Flash
- `web_search` tool powered by Serper.dev
- Sample `research_pipeline.yml`
- Full observability stack (Jaeger, Prometheus, Dashboard)

Access the dashboard at `http://localhost:5173` to interact with your agents.

## 📦 Project Structure

```
my_project/
├── laddr.yml              # Project configuration
├── docker-compose.yml       # Docker services (auto-generated)
├── Dockerfile               # Container definition
├── .env                     # Environment variables
├── agents/                  # Agent configurations
│   ├── summarizer/
│   │   └── agent.yml
│   └── analyzer/
│       └── agent.yml
├── tools/                   # Custom tools
│   └── my_tool.py
└── pipelines/               # Pipeline definitions
    └── analysis_pipeline.yml
```

## 🤖 Creating Agents

### Add an Agent

```bash
laddr add agent researcher
```

This will:
1. Create `agents/researcher/agent.yml`
2. Add worker service to `docker-compose.yml`
3. Register agent in `laddr.yml`

**Note**: A default `researcher` agent with `web_search` tool is created automatically when you run `laddr init`.

### Agent Configuration

`agents/researcher/agent.yml`:

```yaml
name: researcher
role: Research Agent
goal: Research topics on the web and summarize findings concisely
backstory: A helpful researcher that gathers and condenses information from reliable web sources
llm:
  provider: gemini
  model: gemini-2.5-flash
  api_key: ${GEMINI_API_KEY}
  temperature: 0.7
  max_tokens: 2048
tools:
  - web_search
max_iterations: 15
allow_delegation: false
verbose: true
```

### LLM Providers

Laddr supports multiple LLM providers:
- **Gemini** (default) - Google's Gemini models
- **OpenAI** - GPT-4, GPT-3.5, etc.
- **Anthropic** - Claude models
- **Groq** - Fast inference
- **Ollama** - Local models
- **llama.cpp** - Local C++ inference

Set your API keys in `.env`:
```bash
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

## 🔧 Custom Tools

### Default Tool: web_search

A `web_search` tool using Serper.dev is included by default:

```python
# tools/web_search.py
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Serper.dev API."""
    # Uses SERPER_API_KEY from .env
    # Get your free API key at https://serper.dev
```

**Setup**: Add your Serper.dev API key to `.env`:
```bash
SERPER_API_KEY=your_serper_key_here
```

### Add More Tools

```bash
laddr add tool my_custom_tool
```

Edit `tools/my_custom_tool.py`:

```python
def my_custom_tool(param: str) -> str:
    """Your custom tool logic."""
    return result
```

## 📋 Pipelines

A sample pipeline (`research_pipeline.yml`) is created automatically on init.

### Example Pipeline

`pipelines/research_pipeline.yml`:

```yaml
name: research_pipeline
description: Example research pipeline using the researcher agent
tasks:
  - name: search_topic
    description: "Search the web for information about: {topic}"
    agent: researcher
    expected_output: A comprehensive summary of web search results
    tools:
      - web_search
    async_execution: false
    
  - name: analyze_results
    description: Analyze the search results and extract key insights
    agent: researcher
    expected_output: Key insights and recommendations based on the research
    context:
      - search_topic
    async_execution: false
```

### Run a Pipeline

```bash
laddr run pipeline pipelines/analysis.yml
```

Note: Pipeline inputs are defined in the YAML file or can be passed via API.

## 🔍 Observability

### View Traces

Navigate to Jaeger at `http://localhost:16686` to see:
- Task execution traces
- LLM API calls
- Tool invocations
- Error spans

### View Metrics

Navigate to Prometheus at `http://localhost:9090` to query:
- `laddr_agent_task_duration_seconds` — Task execution time
- `laddr_queue_depth` — Pending tasks per agent
- `laddr_tokens_total` — Token usage
- `laddr_errors_total` — Error counts

### Agent Logs

```bash
# View logs for an agent
laddr logs summarizer

# Follow logs in real-time
laddr logs summarizer -f
```

## 🌐 API Reference

### Submit Job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "analysis",
    "inputs": {"document": "report.pdf"}
  }'
```

### Get Job Status

```bash
curl http://localhost:8000/jobs/{job_id}
```

### List Agents

```bash
curl http://localhost:8000/agents
```

## 📊 Dashboard

Access the dashboard at `http://localhost:5173` to:

- View all active agents
- Monitor real-time logs
- Inspect OpenTelemetry traces
- Interact with individual agents
- Visualize job workflows
- Check system health metrics

## 🐳 Docker Commands

```bash
# Start all services
laddr run dev

# View logs
laddr logs <agent_name>

# Stop all services
laddr stop

# Rebuild containers
docker compose up -d --build
```

## ⚙️ Configuration

### Environment Variables

Edit `.env` to customize:

```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/laddr
REDIS_URL=redis://redis:6379
MINIO_ENDPOINT=minio:9000
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
API_HOST=0.0.0.0
API_PORT=8000
```

### Project Configuration

Edit `laddr.yml`:

```yaml
project:
  name: my_project
  broker: redis
  database: postgres
  storage: minio
  tracing: true
  metrics: true
  agents:
    - summarizer
    - analyzer
```

## 🔄 Message Format

### Task Message

```json
{
  "task_id": "uuid",
  "job_id": "uuid",
  "source_agent": "controller",
  "target_agent": "summarizer",
  "payload": {
    "description": "Summarize this document",
    "context": "...",
    "expected_output": "..."
  },
  "trace_parent": "trace-id",
  "created_at": "timestamp"
}
```

### Response Message

```json
{
  "task_id": "uuid",
  "job_id": "uuid",
  "agent_name": "summarizer",
  "status": "completed",
  "result": {"output": "..."},
  "metrics": {
    "tokens": 2200,
    "latency_ms": 5200
  },
  "trace_parent": "trace-id",
  "completed_at": "timestamp"
}
```

## 🔧 Development

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/laddr/laddr.git
cd laddr

# Install dependencies
cd lib/laddr
pip install -e .[dev]

# Run tests
pytest
```

## 📝 CLI Reference

```bash
laddr init [project_name]        # Initialize new project
laddr add agent <name>           # Add new agent
laddr add tool <name>            # Add custom tool
laddr run dev                      # Start development environment
laddr run agent <agent>            # Run single agent locally
laddr run pipeline <file.yml>      # Run a pipeline
laddr logs <agent>                 # View agent logs
laddr stop                       # Stop all services
```

## 🆚 Laddr vs CrewAI

| Feature | CrewAI | Laddr |
|---------|--------|---------|
| **Communication** | Hidden internal calls | Explicit Redis message bus |
| **Runtime** | In-memory Python | Docker containers per agent |
| **Observability** | Limited logging | Full OpenTelemetry + Prometheus |
| **Scalability** | Single process | Distributed workers |
| **Transparency** | Opaque orchestration | Visible task flow |
| **Storage** | In-memory | MinIO/S3 for artifacts |
| **Monitoring** | None | Dashboard + Jaeger + Prometheus |
| **Configuration** | Code-based | YAML + Docker Compose |

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Documentation**: Coming soon
- **GitHub**: https://github.com/laddr/laddr
- **Issues**: https://github.com/laddr/laddr/issues

---

**Built with transparency in mind. No hidden magic. Just distributed agents.**
