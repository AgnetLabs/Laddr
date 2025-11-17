# Getting Started
 
This guide walks you through everything you need to get started with the framework — from environment setup to running your first agent.

---

## Docker Setup

For the full experience (including the web UI and isolated environments), we recommend using **Docker**.

Download it from the [official Docker website](https://www.docker.com/products/docker-desktop).

---

## Python Virtual Environment

Before installing dependencies, it’s best to create a Python virtual environment.

**Create one:**
```bash
python -m venv venv
```

**Activate it:**

On **Windows (Git Bash or CMD)**:
```bash
.\venv\Scripts\activate
```

On **macOS/Linux**:
```bash
source venv/bin/activate
```

---

## Installation

Install **Laddr** (CLI, core, and API):

```bash
pip install laddr
```

Or develop against the local repository (editable mode):

```bash
pip install -e lib/laddr
```

---

## Create a New Project

Initialize a new project and move into it:

```bash
laddr init my_agent_system
cd my_agent_system
```

The project includes:

- `agents/` — Agent modules  
- `workers/` — Worker scripts  
- `Dockerfile` — Build configuration  
- `docker-compose.yml` — Multi-service orchestration  
- `main.py` — Application runner  

---

## Set API Keys

To enable integrations, add your API keys to a `.env` file in your project root:

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key
SERPER_API_KEY=your_serper_api_key
```

> **Note:**  
> - The `web_search` tool requires a Serper API key.  
> - Gemini is used for LLM integrations.  
> - Set both keys before running the stack.

---

## Run the Stack (Docker)

Start the stack using either of these commands:

```bash
laddr run dev -d
```

or

```bash
docker compose up -d
```

Once running, open:

- Dashboard → `http://localhost:5173`  
- API → `http://localhost:8000`

To run agents **without Docker**, see [Local Setup](config/local-runtime).

---

## Add an Agent and Tool

Create a new agent and attach a tool to it:

```bash
laddr add agent researcher --role "Researcher" --goal "Find facts" --llm-model gemini-2.5-flash
laddr add tool web_search --agent researcher --description "Search the web"
```

---

## Quick Run

Run your agent with a quick test command:

```bash
laddr run researcher '{"topic": "Latest AI agent trends"}'
```

This executes a local run of your `researcher` agent using the default configuration.

---

You’re all set!  
You’ve installed **Laddr**, initialized a project, configured API keys, and run your first agent.
