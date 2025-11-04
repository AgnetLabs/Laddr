# Getting started

## Install

Create a virtual environment and install Laddr (CLI, core, API):

```bash
pip install laddr
```

Or develop against this repository (editable):

```bash
pip install -e lib/laddr
```

## Create a new project

```bash
laddr init my_agent_system
cd my_agent_system
```

The project includes agents/, workers/, a Dockerfile, docker-compose.yml, and a main.py runner.

## Run the stack (Docker)

```bash
docker compose up -d
```

Open the dashboard at http://localhost:5173 and the API at http://localhost:8000.

## Add an agent and a tool

```bash
laddr add agent researcher --role "Researcher" --goal "Find facts" --llm-model gemini-2.5-flash
laddr add tool web_search --agent researcher --description "Search the web"
```

## Quick run

```bash
laddr run coordinator '{"topic": "Latest AI agent trends"}'
```
