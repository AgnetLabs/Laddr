"""
Add command for Laddr CLI.

Adds agents and tools to existing projects.
"""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from ..utils import (
    AgentNotFoundError,
    ProjectNotFoundError,
    add_worker_to_compose,
    console,
    get_template_renderer,
    print_completion,
    print_header,
    print_step,
    validate_project_directory,
    write_file,
)


@click.group()
def add():
    """Add resources to your project (agents, tools)."""


@add.command("agent")
@click.argument("agent_name")
@click.option("--role", help="Agent role")
@click.option("--goal", help="Agent goal")
@click.option("--backstory", help="Agent backstory")
@click.option("--llm-provider", default="gemini", help="LLM provider")
@click.option("--llm-model", default="gemini-2.5-flash", help="LLM model")
def add_agent(
    agent_name: str,
    role: str | None,
    goal: str | None,
    backstory: str | None,
    llm_provider: str,
    llm_model: str,
):
    """Add a new agent to the project.
    
    Examples:
        laddr add agent summarizer
        laddr add agent analyst --role "Data Analyst" --goal "Analyze data"
    """
    # Validate agent name
    if "-" in agent_name:
        raise click.BadParameter(
            "Agent name cannot contain hyphens (-). Use underscores (_) instead.",
            param_hint="agent_name"
        )
    
    if not agent_name.replace("_", "").isalnum():
        raise click.BadParameter(
            "Agent name must contain only letters, numbers, and underscores.",
            param_hint="agent_name"
        )
    
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    print_header(f"Adding Agent → {agent_name}")

    # Prompt for missing details
    if not role:
        role = click.prompt("Agent role")
    if not goal:
        goal = click.prompt("Agent goal")
    if not backstory:
        backstory = click.prompt("Agent backstory", default="", show_default=False)

    # Create agent files
    print_step("Generating agent file", f"agents/{agent_name}.py")
    _create_agent_files(
        agent_name=agent_name,
        role=role,
        goal=goal,
        backstory=backstory,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )

    print_completion(f"Agent '{agent_name}' created")
    console.print("[dim]Next:[/dim]")
    console.print(f"  [cyan]laddr run agent {agent_name} --inputs '{{}}'[/cyan]\n")


@add.command("tool")
@click.argument("tool_name")
@click.option("--agent", help="Agent to attach tool to (default: first agent)")
@click.option("--description", help="Tool description")
def add_tool(
    tool_name: str,
    agent: str | None,
    description: str | None,
):
    """Add a new tool to an agent.
    
    Examples:
        laddr add tool calculator
        laddr add tool scraper --agent researcher
    """
    # Validate tool name
    if "-" in tool_name:
        raise click.BadParameter(
            "Tool name cannot contain hyphens (-). Use underscores (_) instead.",
            param_hint="tool_name"
        )
    
    if not tool_name.replace("_", "").isalnum():
        raise click.BadParameter(
            "Tool name must contain only letters, numbers, and underscores.",
            param_hint="tool_name"
        )
    
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    print_header(f"Adding Tool → {tool_name}")

    # Determine target agent
    if not agent:
        with open("laddr.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agents = config.get("project", {}).get("agents", [])
        if not agents:
            raise AgentNotFoundError("No agents found in project")
        agent = agents[0]
        print_step("Attaching to agent", agent)

    # Prompt for description if not provided
    if not description:
        description = click.prompt("Tool description", default=f"{tool_name} tool")

    # Create tool file
    print_step("Generating tool file", f"tools/{tool_name}.py")
    _create_tool_file(tool_name, agent, description)

    print_completion(f"Tool '{tool_name}' created")
    console.print(f"[dim]Add to agents/{agent}.py:[/dim]")
    console.print(f"  [dim]from tools.{tool_name} import {tool_name}[/dim]\n")


def _create_agent_files(
    agent_name: str,
    role: str,
    goal: str,
    backstory: str,
    llm_provider: str,
    llm_model: str,
) -> None:
    """Create agent files (flat layout) and update configuration."""
    renderer = get_template_renderer()

    # Ensure agents package exists
    agents_dir = Path("agents")
    agents_dir.mkdir(parents=True, exist_ok=True)
    write_file(agents_dir / "__init__.py", "")

    # Render flat agent module
    agent_context = {
        "name": agent_name,
        "role": role,
        "goal": goal,
        "backstory": backstory or "",
        "is_coordinator": agent_name.lower() == "coordinator",
        "available_agents": [],
        "model_env": f"{agent_name.upper()}_MODEL",
        "model": llm_model,
        "temperature": 0.3 if agent_name.lower() == "coordinator" else 0.2,
        "max_retries": 3,
        "max_iterations": 5 if agent_name.lower() == "coordinator" else 15,
        "timeout": 600,
        "instructions": (
            "When you receive a task: 1) Analyze 2) Plan 3) Execute using tools 4) Synthesize results."
            if agent_name.lower() == "coordinator"
            else "Be concise and cite sources when researching."
        ),
    }
    renderer.render_to_file("agent_flat.py.j2", agents_dir / f"{agent_name}.py", agent_context)

    # Worker entry using WorkerRunner template
    worker_context = {"agent_name": agent_name}

    # Update laddr.yml
    with open("laddr.yml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if agent_name not in config_data["project"].get("agents", []):
        config_data["project"].setdefault("agents", []).append(agent_name)

    with open("laddr.yml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    # Add worker service to docker-compose.yml
    add_worker_to_compose(Path.cwd(), agent_name)

    # Update project .env with canonical per-agent LLM settings if present
    # Do not overwrite existing values. Use canonical names: LLM_MODEL_<AGENT>, LLM_BACKEND_<AGENT>
    env_path = Path(".env")
    try:
        if env_path.exists():
            existing = env_path.read_text(encoding="utf-8")
        else:
            existing = ""

        env_lines: list[str] = []
        upper = agent_name.upper()
        model_key = f"LLM_MODEL_{upper}"
        backend_key = f"LLM_BACKEND_{upper}"

        if model_key not in existing:
            env_lines.append(f"{model_key}={llm_model}")
        if backend_key not in existing:
            env_lines.append(f"{backend_key}={llm_provider}")

        if env_lines:
            # Append with a blank line separator if file not empty
            sep = "\n" if existing and not existing.endswith("\n") else ""
            content = existing + sep + "\n".join(env_lines) + "\n"
            write_file(env_path, content)
            print_step("Updating .env", ", ".join(env_lines))
    except Exception:
        # Non-fatal: skip env update if anything goes wrong
        pass


def _create_tool_file(tool_name: str, agent_name: str, description: str) -> None:
    """Create tool file (project-level) and update agent configuration."""
    renderer = get_template_renderer()

    # Create tool file in top-level tools directory
    tools_dir = Path("tools")
    tools_dir.mkdir(parents=True, exist_ok=True)

    tool_context = {
        "tool_name": tool_name,
        "tool_function_name": tool_name.lower().replace("-", "_"),
        "tool_description": description,
        "tool_params": "query: str",  # Default params
        "params": [{"name": "query", "description": "Input query"}]
    }
    renderer.render_to_file("tool.py.j2", tools_dir / f"{tool_name}.py", tool_context)

