# `laddr`

**Usage**:

```console
$ laddr [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `init`: Initialize a new laddr project
* `add agent`: Add a new agent to your project
* `add tool`: Add a new tool to an existing agent
* `run`: Run an agent or coordinator locally
* `check`: Validate project structure and configuration
* `infra up`: Start infrastructure services
* `infra down`: Stop infrastructure services
* `worker`: Start a worker process for an agent
* `prompt view`: View an agent’s system prompt
* `prompt edit`: Edit an agent’s system prompt

---

## `laddr init`

Initialize a new laddr project.

**Usage**:
```console
$ laddr init my-project
$ cd my-project
```

**Creates:**
- `laddr.yml` – Main config  
- `.env` – Environment variables (Redis, Postgres, MinIO)  
- `agents/` – Agent folders  
- `workers/` – Worker modules  

**Options:**
- Project is created in a subdirectory with the given name.

---

## `laddr add agent`

Add a new agent to your project.

**Usage**:
```console
$ laddr add agent researcher
```

**Creates:**
- `agents/researcher/handler.py` – Agent handler with tools  
- `agents/researcher/prompt.md` – System prompt  

**Options:**
- Agent name must be lowercase, `snake_case`.

---

## `laddr add tool`

Add a new tool to an existing agent.

**Usage**:
```console
$ laddr add tool researcher
```

**Creates:**
Tool files inside the specified agent directory and updates `handler.py`.

**Options:**
- Tool name must be lowercase, `snake_case`.

---

## `laddr run`

Run an agent or coordinator locally (without Redis/Postgres).

**Usage**:
```console
$ laddr run researcher "Search for latest AI news"
```

**Options:**
- `--trace` – Enable tracing output  
- `--trace-mask <tool1,tool2>` – Mask specific tools from traces  

**Environment:**
- Uses in-memory implementations (no Redis/Postgres required)  
- Loads `.env` for LLM credentials.

---

## `laddr check`

Validate project structure and configuration.

**Usage**:
```console
$ laddr check
```

**Verifies:**
- All agents have `handler.py` and `prompt.md`  
- All tools are valid Python modules  
- Environment variables are set correctly  
- `laddr.yml` structure is valid.

---

## `laddr infra up`

Start infrastructure services (Redis, Postgres, MinIO) via Docker Compose.

**Usage**:
```console
$ laddr infra up
```

**Options:**
- `-d`, `--detach` – Run in background.

---

## `laddr infra down`

Stop infrastructure services.

**Usage**:
```console
$ laddr infra down
```

---

## `laddr worker`

Start a worker process for an agent.

**Usage**:
```console
$ laddr worker researcher
```

**Options:**
- Connects to Redis queue specified in `laddr.yml`  
- Loads agent from `agents/researcher/handler.py`  
- Processes tasks from the coordinator.

---

## `laddr prompt view`

View an agent’s system prompt.

**Usage**:
```console
$ laddr prompt view researcher
```

---

## `laddr prompt edit`

Edit an agent’s system prompt.

**Usage**:
```console
$ laddr prompt edit researcher
```

**Behavior:**
- Opens `prompt.md` in your default editor.

---

## Edge Cases

### Running without infrastructure
For local testing without Redis/Postgres:
```console
$ laddr run researcher "test query"
```
Uses in-memory implementations and does not require `laddr infra up`.

### Tracing specific agents
Enable tracing for debugging:
```console
$ laddr run researcher "query" --trace
```
Mask noisy tools:
```console
$ laddr run researcher "query" --trace --trace-mask web_search,file_read
```

### Custom environment file
Use a custom `.env` file:
```console
$ export LADDR_ENV_FILE=.env.production
$ laddr check
```
