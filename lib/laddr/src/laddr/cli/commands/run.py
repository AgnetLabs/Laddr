"""
Run command for Laddr CLI.

Manages Docker environment and job execution.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Any

import click

from ..utils import (
        ProjectNotFoundError,
        check_docker,
        check_docker_compose,
        compose_up,
        print_info,
        print_panel,
        print_success,
        validate_project_directory,
        wait_for_service,
)


@click.group()
@click.pass_context
def run(ctx: click.Context):
        """Run environments, agents, or pipelines.

        Usage:
            laddr run dev [--build] [--no-detach]
            laddr run agent <agent_name> [--inputs '{...}']
            laddr run pipeline <file.yml>
        """


@run.command("dev")
@click.option("--build", is_flag=True, help="Force rebuild images")
@click.option("--detach", "-d", is_flag=True, help="Run in detached mode (background)")
def run_dev(build: bool, detach: bool):
    """Run the Laddr development environment.
    
    Starts all infrastructure services and agent workers:
    - PostgreSQL (internal observability database)
    - Redis (message bus)
    - API server
    - Agent workers
    - Dashboard
    
    By default, shows live logs (like docker compose up).
    Use --detach/-d to run in background.
    
    Examples:
        laddr run dev              # Show logs
        laddr run dev --build      # Rebuild and show logs
        laddr run dev --detach     # Run in background
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    # Check Docker availability
    check_docker()
    check_docker_compose()

    print_panel(
        "Starting Laddr Development Environment",
        "Building and starting all services...",
    )

    # Start services - if not detached, stream logs immediately
    if not detach:
        print_info("Starting services and streaming logs (Ctrl+C to stop)...")
        try:
            compose_up(detach=False, build=build)
        except KeyboardInterrupt:
            print_info("\nStopping services...")
            subprocess.run(["docker", "compose", "down"], check=False)
        return

    # Detached mode - start and wait for services
    compose_up(detach=True, build=build)

    # Wait for critical services
    print_info("Waiting for services to be ready...")
    time.sleep(5)

    critical_services = ["postgres", "redis", "api"]
    for service in critical_services:
        wait_for_service(service, timeout=30)

    print_success("Laddr is running!")
    _print_service_info()
    _print_management_commands()


@run.command("pipeline")
@click.argument("pipeline_file")
def run_pipeline(pipeline_file: str):
    """Run a pipeline defined in a YAML file."""
    # Lazy import to avoid hard deps when not running pipeline
    import yaml  # type: ignore

    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    with open(pipeline_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    stages = data.get("pipeline") or data.get("stages") or data.get("tasks")
    if not isinstance(stages, list):
        raise click.BadParameter("Pipeline YAML must define a list under 'pipeline' or 'stages'")

    # Use Laddr runtime (shared env for all agents)
    import asyncio

    from laddr.core import AgentRunner, LaddrConfig  # type: ignore

    results: dict[str, Any] = {}
    runner = AgentRunner(env_config=LaddrConfig())
    for stage in stages:
        agent_name = stage.get("agent")
        # Support both {inputs: {...}} and arbitrary keys; if tasks format, pass remaining keys except 'agent'
        inputs = stage.get("inputs", {k: v for k, v in stage.items() if k != "agent"})
        if not agent_name:
            raise click.BadParameter("Each stage must include 'agent'")
        print_panel("Running pipeline stage", f"agent: {agent_name}")
        res = asyncio.run(runner.run(inputs, agent_name=agent_name))
        results[agent_name] = res

    print_panel("Pipeline complete", json.dumps(results, indent=2, ensure_ascii=False))


@run.command("agent")
@click.argument("agent_name")
@click.option("--inputs", "inputs_json", default="{}", help="JSON dict of inputs for the agent")
def run_agent_cmd(agent_name: str, inputs_json: str):
    """Run a single agent locally using AgentRunner."""
    import asyncio
    import os
    import sys

    # Ensure local project imports work (agents package)
    try:
        cwd = str(Path.cwd())
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
    except Exception:
        pass

    # Favor local-friendly defaults to avoid external deps
    try:
        if not os.environ.get("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite:///laddr.db"
        if not os.environ.get("QUEUE_BACKEND") and not os.environ.get("REDIS_URL"):
            os.environ["QUEUE_BACKEND"] = "memory"
    except Exception:
        pass

    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    try:
        inputs = json.loads(inputs_json) if inputs_json else {}
    except json.JSONDecodeError:
        raise click.BadParameter("--inputs must be a valid JSON object")

    # Use new runtime
    try:
        from laddr.core import LaddrConfig, run_agent

        print_panel("Running agent", f"agent: {agent_name}")

        # Load environment config
        config = LaddrConfig()

        # Run agent
        result = asyncio.run(run_agent(agent_name, inputs, config))

        # Print result
        print_success(f"Job completed: {result['job_id']}")
        print_panel("Result", json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print_info(f"Error: {e}")
        raise click.ClickException(str(e))


@run.command("replay")
@click.argument("job_id")
@click.option("--reexecute", is_flag=True, help="Re-execute the job instead of returning stored result")
def replay_job(job_id: str, reexecute: bool):
    """Replay a previous job by job ID.
    
    Examples:
        laddr run replay abc123-456-def
        laddr run replay abc123-456-def --reexecute
    """
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    try:
        from laddr.core import AgentRunner, LaddrConfig

        print_panel("Replaying job", f"job_id: {job_id}\nreexecute: {reexecute}")

        # Load environment config
        config = LaddrConfig()
        runner = AgentRunner(env_config=config)

        # Replay
        result = runner.replay(job_id, reexecute=reexecute)

        # Print result
        print_success("Job replay complete")
        print_panel("Result", json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print_info(f"Error: {e}")
        raise click.ClickException(str(e))


def _print_service_info() -> None:
    """Print service URLs."""
    print_panel(
        "Services",
        "[cyan]Dashboard:[/cyan]  http://localhost:5173\n"
        "[cyan]API:[/cyan]        http://localhost:8000\n"
        "[cyan]API Docs:[/cyan]   http://localhost:8000/docs\n"
        "[cyan]Postgres:[/cyan]   localhost:5432\n"
        "[cyan]Redis:[/cyan]      localhost:6379",
        style="green",
    )


def _print_management_commands() -> None:
    """Print management command help."""
    print_panel(
        "Commands",
        "laddr logs <agent>  - View agent logs\n"
        "laddr ps            - Show container status\n"
        "laddr scale <agent> <N> - Scale agent workers\n"
        "laddr stop          - Stop all services",
        style="cyan",
    )


# Alias for backward compatibility
@click.command(name="run-dev", hidden=True)
def run_dev_alias():
    """Alias for 'laddr run dev'."""
    from click import Context

    ctx = Context(run_dev)
    ctx.invoke(run_dev)
