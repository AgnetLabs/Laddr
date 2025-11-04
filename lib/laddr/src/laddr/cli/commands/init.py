"""
Init command for Laddr CLI.

Creates new Laddr projects with full scaffolding.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn
import yaml

from ..utils import (
    NestedProjectError,
    ProjectConfigSchema,
    ProjectDetails,
    ProjectExistsError,
    add_worker_to_compose,
    get_template_renderer,
    print_panel,
    print_success,
    validate_project_directory,
    write_file,
)


@click.command()
@click.argument("project_name", required=False)
@click.option("--path", default=".", help="Path to create project in")
def init(project_name: str | None, path: str):
    """Initialize a new Laddr project.
    
    Creates project structure with:
    - Configuration files (laddr.yml, .env)
    - Docker setup (docker-compose.yml, Dockerfile)
    - Default researcher agent
    - Example tools and pipeline
    
    Users import from laddr package:
        from laddr import Agent, AgentRunner, run_agent, actor, tool
    
    Examples:
        laddr init myproject
        laddr init myproject --path /path/to/dir
        laddr init  # Interactive mode
    """
    # Prompt for project name if not provided
    if not project_name:
        project_name = click.prompt("Project name")

    # Resolve project path
    project_path = Path(path)
    if project_name and project_name != ".":
        project_path = project_path / project_name
    project_path = project_path.resolve()

    # Check if project already exists
    if project_path.exists() and validate_project_directory(project_path):
        raise ProjectExistsError(str(project_path))

    # Check for nested project
    for parent in project_path.parents:
        if validate_project_directory(parent):
            raise NestedProjectError(str(parent))

    # Handle in-place creation
    create_in_place = False
    if project_name in (".", ""):
        create_in_place = True
    else:
        cwd_name = Path.cwd().name
        if path in (".", "") and project_name == cwd_name:
            create_in_place = True

    if create_in_place:
        project_path = Path.cwd().resolve()

    # Check if directory is empty (except for existing laddr.yml)
    if project_path.exists() and any(project_path.iterdir()):
        if not validate_project_directory(project_path):
            raise ProjectExistsError(str(project_path))

    print_panel(
        "Initializing Laddr Project",
        f"Creating project: [bold]{project_path.name}[/bold]",
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)

        # Create directory structure
        _create_directories(project_path)

        # Generate core modules
        progress.update(task, description="Generating core modules...")
        _generate_core_modules(project_path)

        # Generate configuration files
        progress.update(task, description="Creating configuration...")
        _generate_config_files(project_path, project_path.name)

        # Generate Docker setup
        progress.update(task, description="Creating Docker configuration...")
        _generate_docker_setup(project_path)

        # Generate default agent
        progress.update(task, description="Seeding default agent...")
        _generate_default_agent(project_path)

        # Generate README
        progress.update(task, description="Creating README...")
        _generate_readme(project_path, project_path.name)

    print_success(f"Project created: {project_path}")
    print_panel(
        "Next Steps",
        f"cd {project_path if project_path != Path.cwd() else '.'}\nladdr run dev",
        style="green",
    )


def _create_directories(project_path: Path) -> None:
    """Create project directory structure."""
    directories = [
        project_path,
        project_path / "agents",
        project_path / "tools",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _generate_core_modules(project_path: Path) -> None:
    """
    V3.0: Users import from laddr package, no need to generate core files.
    
    This function is kept for backward compatibility but does nothing.
    Users should use: from laddr import Agent, AgentRunner, run_agent
    """


def _generate_config_files(project_path: Path, project_name: str) -> None:
    """Generate configuration files."""
    renderer = get_template_renderer()

    # laddr.yml
    config = ProjectConfigSchema(
        project=ProjectDetails(
            name=project_name,
            broker="redis",
            database="postgres",
            storage="minio",
            tracing=True,
            metrics=True,
            agents=[],
        )
    )
    config.save_to_file(project_path / "laddr.yml")

    # .env
    renderer.render_to_file("dotenv.j2", project_path / ".env", {})


def _generate_docker_setup(project_path: Path) -> None:
    """Generate Docker configuration."""
    renderer = get_template_renderer()

    renderer.render_to_file("docker-compose.yml.j2", project_path / "docker-compose.yml", {})
    renderer.render_to_file("Dockerfile.j2", project_path / "Dockerfile", {})
    renderer.render_to_file("requirements.txt.j2", project_path / "requirements.txt", {})


def _generate_default_agent(project_path: Path) -> None:
    """Generate default coordinator and researcher agents."""
    renderer = get_template_renderer()

    # Create agents directory __init__
    write_file(project_path / "agents" / "__init__.py", "")

    # Define both default agents (flat files in agents/)
    default_agents = [
        {
            "name": "coordinator",
            "role": "Orchestration Coordinator & Task Manager",
            "goal": "Analyze complex user requests, break them into specific subtasks, delegate each subtask to the appropriate specialist agent, and synthesize their responses into a comprehensive final answer",
            "backstory": "An experienced orchestrator who excels at task decomposition and delegation. You never perform research yourself - instead, you coordinate a team of specialists. You understand that effective delegation requires clear, specific instructions and that your role is to combine specialist outputs into coherent, complete responses for users.",
            "is_coordinator": True,
            "available_agents": ["researcher"],
        },
        {
            "name": "researcher",
            "role": "Web Research Specialist & Information Analyst",
            "goal": "Conduct thorough web research using available tools (web_search, scrape_url, extract_links) to find accurate, relevant information and deliver comprehensive, well-sourced answers",
            "backstory": "A meticulous research specialist with expertise in web searching, content extraction, and information synthesis. You have direct access to powerful web tools and know how to use them effectively. Your strength is finding high-quality sources, extracting key information, and presenting findings clearly with proper citations. You prioritize accuracy and always verify information across multiple sources when possible.",
            "is_coordinator": False,
            "available_agents": [],
        }
    ]

    agent_names = []

    for agent_config in default_agents:
        agent_name = agent_config["name"]
        agent_names.append(agent_name)

        # agents/__init__.py once
        write_file(project_path / "agents" / "__init__.py", "")

        # Render flat agent file
        agent_context = {
            "name": agent_name,
            "role": agent_config["role"],
            "goal": agent_config["goal"],
            "backstory": agent_config["backstory"],
            "is_coordinator": agent_config.get("is_coordinator", False),
            "available_agents": agent_config.get("available_agents", []),
            "model_env": f"{agent_name.upper()}_MODEL",
            "model": "gemini-2.5-flash",
            "fallback_model_env": f"{agent_name.upper()}_FALLBACK_MODEL",
            "fallback_model": "gpt-3.5-turbo",
            "temperature": 0.3 if agent_config.get("is_coordinator") else 0.2,
            "max_retries": 3,
            "max_iterations": 5 if agent_config.get("is_coordinator") else 15,
            "timeout": 600,
            "instructions": (
                "When you receive a task: 1) Analyze 2) Plan 3) Execute using tools 4) Synthesize results."
                if agent_config.get("is_coordinator")
                else "Be concise and cite sources when researching."
            ),
        }
        renderer.render_to_file("agent_flat.py.j2", project_path / "agents" / f"{agent_name}.py", agent_context)

        # Add worker to docker-compose
        add_worker_to_compose(project_path, agent_name)

    # Tools package and defaults
    write_file(project_path / "tools" / "__init__.py", "")
    renderer.render_to_file("tools_web.py.j2", project_path / "tools" / "web_tools.py", {})
    renderer.render_to_file("tools_communication.py.j2", project_path / "tools" / "communication_tools.py", {})

    # Main entry - simple runner selecting agent by env
    renderer.render_to_file("main_flat.py.j2", project_path / "main.py", {})

    # Update laddr.yml to add both agents
    config_path = project_path / "laddr.yml"
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    config_data["project"]["agents"] = agent_names

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)


def _generate_readme(project_path: Path, project_name: str) -> None:
    """Generate project README."""
    renderer = get_template_renderer()
    renderer.render_to_file(
        "README.md.j2",
        project_path / "README.md",
        {"project_name": project_name},
    )
