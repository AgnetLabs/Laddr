# CLI Commands

This page is auto-generated from the Click command tree.

# CLI Commands

Laddr provides a comprehensive CLI for scaffolding projects, managing agents, and running workflows.

## Usage

```bash
laddr --help
```

## Command Reference

### `laddr init`

Initialize a new Laddr project.

```bash
laddr init my-project
cd my-project
```

Creates:
- `laddr.yml` – Main config
- `.env` – Environment variables (Redis, Postgres, MinIO)
- `agents/` – Agent folders
- `workers/` – Worker modules

**Options:**
- Project is created in a subdirectory with the given name

### `laddr add agent`

Add a new agent to your project.

```bash
laddr add agent researcher
```

Creates:
- `agents/researcher/handler.py` – Agent handler with tools
- `agents/researcher/prompt.md` – System prompt

**Options:**
- Agent name must be lowercase, snake_case

### `laddr add tool`

Add a new tool to an existing agent.

```bash
laddr add tool researcher web_search
```

Creates:
- `agents/researcher/tools/web_search.py` – Tool function with Pydantic model

**Options:**
- Tool name must be lowercase, snake_case
- Generates a Pydantic InputModel for typed parameters

### `laddr run`

Run an agent or coordinator locally (without Redis/Postgres).

```bash
laddr run researcher "Search for latest AI news"
```

**Options:**
- `--trace` – Enable tracing output
- `--trace-mask <tool1,tool2>` – Mask specific tools from traces

**Environment:**
- Uses in-memory implementations (no Redis/Postgres required)
- Loads `.env` for LLM credentials

### `laddr check`

Validate project structure and configuration.

```bash
laddr check
```

Verifies:
- All agents have handler.py and prompt.md
- All tools are valid Python modules
- Environment variables are set correctly
- laddr.yml structure is valid

### `laddr infra up`

Start infrastructure services (Redis, Postgres, MinIO) via Docker Compose.

```bash
laddr infra up
```

**Options:**
- `-d, --detach` – Run in background

### `laddr infra down`

Stop infrastructure services.

```bash
laddr infra down
```

### `laddr worker`

Start a worker process for an agent.

```bash
laddr worker researcher
```

**Options:**
- Connects to Redis queue specified in laddr.yml
- Loads agent from `agents/researcher/handler.py`
- Processes tasks from the coordinator

### `laddr prompt view`

View an agent's system prompt.

```bash
laddr prompt view researcher
```

### `laddr prompt edit`

Edit an agent's system prompt.

```bash
laddr prompt edit researcher
```

Opens prompt.md in your default editor.

## Edge Cases

### Running without infrastructure

For local testing without Redis/Postgres:

```bash
laddr run researcher "test query"
```

This uses in-memory implementations and doesn't require `laddr infra up`.

### Tracing specific agents

Enable tracing for debugging:

```bash
laddr run researcher "query" --trace
```

Mask noisy tools:

```bash
laddr run researcher "query" --trace --trace-mask web_search,file_read
```

### Custom environment file

```bash
export EVENAGE_ENV_FILE=.env.production
laddr check
```
