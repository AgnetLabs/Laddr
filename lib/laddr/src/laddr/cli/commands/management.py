"""
Management commands for Laddr CLI.

Provides logs, ps, scale, and stop commands for Docker environment management.
"""

from __future__ import annotations

from pathlib import Path

import click

from ..utils import (
    ProjectNotFoundError,
    compose_down,
    compose_logs,
    compose_ps,
    compose_scale,
    console,
    print_info,
    print_success,
    validate_project_directory,
)


@click.command()
@click.argument("agent_name")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--tail", type=int, help="Number of lines to show from end")
def logs(agent_name: str, follow: bool, tail: int | None):
    """View logs for an agent worker.
    
    Examples:
        laddr logs researcher
        laddr logs researcher --follow
        laddr logs researcher --tail 100
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    service_name = f"{agent_name}_worker"
    print_info(f"Fetching logs for {service_name}...")

    try:
        compose_logs(service_name, follow=follow, tail=tail)
    except KeyboardInterrupt:
        print_info("Stopped following logs")


@click.command()
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="Output format")
def ps(format: str):
    """Show status of all services and workers.
    
    Examples:
        laddr ps
        laddr ps --format json
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    print_info("Fetching service status...")

    output = compose_ps()

    if format == "json":
        # TODO: Parse and format as JSON
        console.print(output)
    else:
        console.print(output)


@click.command()
@click.argument("agent_name")
@click.argument("replicas", type=int)
def scale(agent_name: str, replicas: int):
    """Scale an agent worker to N replicas.
    
    Examples:
        laddr scale researcher 3
        laddr scale summarizer 0  # Stop all replicas
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    if replicas < 0:
        raise click.BadParameter("Replicas must be >= 0")

    service_name = f"{agent_name}_worker"
    print_info(f"Scaling {service_name} to {replicas} replicas...")

    compose_scale(service_name, replicas)

    print_success(f"{agent_name} scaled to {replicas} instances")

    # Show updated status
    output = compose_ps([service_name])
    console.print("\n" + output)


@click.command()
@click.option("--volumes", "-v", is_flag=True, help="Remove named volumes")
def stop(volumes: bool):
    """Stop all Laddr services.
    
    Examples:
        laddr stop
        laddr stop --volumes  # Also remove data volumes
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    print_info("Stopping Laddr services...")

    compose_down(remove_volumes=volumes)

    print_success("Services stopped")

    if volumes:
        print_info("Named volumes removed")
