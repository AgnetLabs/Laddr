# Configuration of Agent

This guide explains how to configure and run your own agents using the **laddr** framework — including environment setup, LLM configuration, execution control, and runtime behavior.

---

## Agent Definition Structure

Every agent (e.g. `researcher.py`, `writer.py`, `analyzer.py`) defines a specialized worker that connects to **laddr’s orchestration layer**.

Standard structure:

```python
from __future__ import annotations
import asyncio
import os
from dotenv import load_dotenv
from laddr import Agent, WorkerRunner
from laddr.llms import openai
from tools.web_tools import web_search, scrape_url, extract_links

load_dotenv()

TOOLS = [web_search, scrape_url, extract_links]

researcher = Agent(
    name="researcher",
    role="Web Research Specialist",
    goal="Search the web and summarize findings",
    backstory="You are a research-focused agent who finds accurate data online.",
    llm=openai(model="gpt-4o-mini", temperature=0.0),
    tools=TOOLS,
    max_retries=1,
    max_iterations=3,
    max_tool_calls=2,
    timeout=45,
    trace_enabled=True,
)

async def main():
    runner = WorkerRunner(agent=researcher)
    print("Starting researcher worker...")
    await runner.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Required Sections
1. Import dependencies  
2. Load `.env` configuration  
3. Register tools  
4. Define the agent configuration  
5. Create an async entry point (`WorkerRunner`)

---

## Environment Configuration

Agents use environment variables to control behavior, models, and external service keys.

```bash
# Queue and Database
QUEUE_BACKEND=redis
REDIS_URL=redis://localhost:6379
DB_BACKEND=sqlite
DATABASE_URL=sqlite:///./laddr.db

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.0
OPENAI_API_KEY=sk-...

# Optional: per-agent models
RESEARCHER_MODEL=gpt-4o-mini
WRITER_MODEL=claude-3-5-sonnet-20241022
ANALYZER_MODEL=gemini-1.5-pro

# Tool API keys
SERPER_API_KEY=...
```

If no database service is available, laddr defaults to SQLite:

```bash
DB_BACKEND=sqlite
DATABASE_URL=sqlite:///./laddr.db
```

---

## LLM Configuration

Example:

```python
from laddr.llms import openai
llm = openai(model="gpt-4o-mini", temperature=0.0)
```

### Common Providers
- **OpenAI** → `openai(model="gpt-4o-mini")` — Balanced reasoning, tool use  
- **Gemini** → `gemini(model="gemini-1.5-pro")` — Long context, large docs  
- **Anthropic** → `anthropic(model="claude-3-5-sonnet")` — Deep reasoning, writing  
- **Groq** → `groq(model="llama-3.3-70b-versatile")` — Fast and cost-efficient  
- **xAI Grok** → `grok(model="grok-beta")` — Real-time and social data  

### Temperature Recommendations
- Research / Analysis → `0.0`  
- Creative Writing → `0.7–0.9`  
- Support / Dialogue → `0.3–0.5`

---

## Core Agent Parameters

| Parameter | Type | Description | Default |
|------------|------|-------------|----------|
| name | str | Unique agent identifier | Required |
| role | str | Role description for LLM | Required |
| goal | str | Task objective | Required |
| backstory | str | Context for consistent behavior | Required |
| llm | object | LLM configuration | Required |
| tools | list | Registered functions | [] |
| max_retries | int | Retry count for failed runs | 1 |
| max_iterations | int | Reasoning loops before stop | 3 |
| max_tool_calls | int | Tool call limit per task | 2 |
| timeout | int | Max runtime in seconds | 45 |
| trace_enabled | bool | Enables trace storage | True |
| trace_mask | list | Redacted fields in traces | [] |

---

## Execution Control

| Parameter | Purpose | Typical Value | Notes |
|------------|----------|----------------|--------|
| max_retries | Retry on transient errors (LLM/API) | 1–2 | Keeps reliability balanced |
| max_iterations | LLM reasoning loops | 3 | Prevents infinite loops |
| max_tool_calls | Tool invocations allowed | 2 | Limits API usage |
| timeout | Total time before abort | 45s | Graceful termination |

---

## Tool Configuration

Tools extend agent capabilities.  
Each tool is a decorated Python function that exposes structured parameters.

```python
@tool(
    name="web_search",
    description="Search the web for information",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    }
)
def web_search(query: str, max_results: int = 5) -> Dict:
    # Implementation
    ...
```

### Usage Flow
- The LLM decides when to call tools  
- Tool calls and outputs are logged in traces  
- Each tool call consumes one `max_tool_calls` slot  

Example TOOLS list:

```python
TOOLS = [web_search, scrape_url, extract_links]
```

---

## Tracing Configuration

Tracing logs all agent activity to the database for debugging and auditing.

```python
trace_enabled=True
trace_mask=["api_key", "tool_result"]
```

### Logged Events
- Task start/end  
- LLM reasoning steps  
- Tool invocations  
- Errors or timeouts  

View recent traces:

```bash
sqlite3 laddr.db "SELECT * FROM traces ORDER BY id DESC LIMIT 5;"
```

### Best Practices
- Always enable tracing in production  
- Mask sensitive data  
- Rotate old traces periodically  

---

## Worker Runtime

Each agent runs as an independent worker process.

```python
async def main():
    runner = WorkerRunner(agent=researcher)
    print("Starting researcher worker...")
    await runner.start()

if __name__ == "__main__":
    asyncio.run(main())
```

Run locally:

```bash
python agents/researcher.py
```

Docker Compose example:

```yaml
services:
  researcher_worker:
    image: laddr
    command: python agents/researcher.py
    environment:
      - REDIS_URL=redis://redis:6379
      - DB_BACKEND=sqlite
      - DATABASE_URL=sqlite:///./laddr.db
```

---

## Recommended Defaults

### Development

```python
max_retries=0
max_iterations=5
max_tool_calls=5
timeout=120
trace_enabled=True
```

### Production

```bash
max_retries=2
max_iterations=3
max_tool_calls=2
timeout=45
trace_enabled=True
trace_mask=["api_key"]
```

---

## Monitoring & Debugging

| Check | Command |
|--------|----------|
| Active queues | `redis-cli XLEN laddr:tasks:researcher` |
| Worker registered | `redis-cli HGETALL laddr:agents` |
| Recent traces | `sqlite3 laddr.db "SELECT * FROM traces ORDER BY id DESC LIMIT 10;"` |
| Docker logs | `docker compose logs researcher_worker -f` |

### Common Issues
- Timeout → increase `timeout`  
- Repeated failures → raise `max_retries`  
- Incomplete results → increase `max_iterations`

---

## Troubleshooting Quick Reference

| Problem | Likely Cause | Fix |
|----------|---------------|-----|
| Agent not starting | Missing laddr package | `pip install -e .` |
| LLM errors | Missing API key | Set `OPENAI_API_KEY` or provider key |
| Tool calls failing | Missing `SERPER_API_KEY` | Add to `.env` |
| Frequent timeouts | Slow APIs | Increase timeout or reduce tool calls |
| Empty traces | Tracing disabled | Set `trace_enabled=True` |
| Delegation fails | No workers running | Start via `python agents/<name>.py` |

---

## Agent Extension Example

```python
from laddr import Agent
from laddr.llms import openai
from tools.math_tools import calculate

analyzer = Agent(
    name="analyzer",
    role="Data Analyst",
    goal="Perform numerical analysis and return structured data",
    llm=openai(model="gpt-4o-mini", temperature=0.0),
    tools=[calculate],
    max_iterations=2,
    max_tool_calls=1,
    timeout=30,
    instructions="Use the calculate tool and return results as JSON.",
)
```

Run:

```bash
python agents/analyzer.py
```

---

## Quick Reference

```python
Agent(
  name="researcher",
  llm=openai(model="gpt-4o-mini"),
  tools=[web_search],
  max_retries=1,
  max_iterations=3,
  max_tool_calls=2,
  timeout=45,
  trace_enabled=True
)
```

Environment defaults:

```bash
DB_BACKEND=sqlite
DATABASE_URL=sqlite:///./laddr.db
QUEUE_BACKEND=redis
REDIS_URL=redis://redis:6379
```
