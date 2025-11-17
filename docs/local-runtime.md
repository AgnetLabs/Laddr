# Local Runtime Testing (Laddr with OpenAI)

This guide documents the **local testing workflow** for the Laddr multi-agent system using  
`python main.py` with the **in-memory queue backend**.  
It’s ideal for debugging agents, verifying tool logic, and validating agent coordination locally —  
**no Docker required.**

⚙️ **Tested Configuration:** OpenAI LLM backend (`gpt-4o-mini`), SQLite database, In-memory queue.


## Local Configuration

Set up your `.env` file as follows:

```bash
# Backend Configuration
LLM_BACKEND=openai
QUEUE_BACKEND=memory
DB_BACKEND=sqlite
DATABASE_URL=sqlite:///./Laddr.db

# LLM Keys
OPENAI_API_KEY=sk-proj-***
RESEARCHER_MODEL=gpt-4o-mini
COORDINATOR_MODEL=gpt-4o-mini
ANALYZER_MODEL=gpt-4o-mini
WRITER_MODEL=gpt-4o-mini
VALIDATOR_MODEL=gpt-4o-mini

# Optional Tool Keys
SERPER_API_KEY=***
```

💡 **Note:** The in-memory backend does not require Redis or Docker.  
SQLite is used for trace persistence.

---

## Testing Scenarios

### Single Agent Execution

```bash
AGENT_NAME=writer python main.py run '{"query": "Write a paragraph about artificial intelligence"}'
```

Runs the `writer` agent independently. No delegation or external workers required.

---

### Analyzer Tool Usage

```bash
AGENT_NAME=analyzer python main.py run '{"query": "Calculate the sum of 25, 50, 75, 100 and find the average"}'
```

Verifies `calculate` and `aggregate` tools within the same runtime.

---

### Sequential Workflow

```python
from Laddr import AgentRunner, LaddrConfig
import asyncio, uuid

async def test():
    runner = AgentRunner(env_config=LaddrConfig())
    job_id = str(uuid.uuid4())
    inputs = {'query': 'Calculate 100 + 200 + 300'}

    for agent in ['analyzer', 'writer']:
        result = await runner.run(inputs, agent_name=agent, job_id=job_id)
        if result.get('status') == 'success':
            inputs = {'input': result['result']}

asyncio.run(test())
```

Shared `job_id` ensures traces for all agents are grouped in the same workflow.

---

## Running Worker Processes Locally

To start an agent worker locally, run the agent script for the worker you want to start:

```bash
python agents/coordinator.py
```

You can start multiple workers by opening separate terminals and running:

```bash
# Terminal 1
python agents/coordinator.py

# Terminal 2
python agents/researcher.py

# Terminal 3
python agents/writer.py
```

**Note:** Delegation (workers handing tasks to each other) requires a queue backend such as Redis or Kafka.  
The in-memory queue is ideal for **single-agent debugging** but not for inter-process delegation.

---

## Known Limitations

- Delegation tools (`system_delegate_task`) need worker processes.  
- In-memory queue supports **single process only** (no inter-process communication).  
- Some agents (like `researcher`) may attempt delegation — refine prompts accordingly.

---

## Debugging and Trace Analysis

Traces are automatically logged to SQLite (`Laddr.db`):

```bash
sqlite3 Laddr.db "SELECT agent_name, event_type, timestamp FROM traces ORDER BY id DESC LIMIT 10;"
```

**Common trace events include:**
- `task_start`, `task_complete`  
- `llm_usage`, `tool_call`, `tool_error`  
- `autonomous_think` (agent reasoning)

---

## Local Testing Guidelines

- Use single-agent runs for debugging and instruction tuning.  
- Use sequential workflows to simulate multi-agent pipelines.  
- Enable tracing via SQLite for every run.  
- Avoid delegation without worker processes.

For full orchestration testing (delegation, parallel tasks), switch to  
`QUEUE_BACKEND=redis` and run **Docker-based workers**.

---

## Notes

- **MemoryBus** is a process-scoped singleton that enables agent task routing within the same runtime.  
  It’s perfect for local testing but not suitable for production scaling.  
- All events, tools, and LLM interactions are persisted in SQLite — query them anytime for debugging.
