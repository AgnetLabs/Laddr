"""
CLI commands for prompt execution (new terminology).

Provides 'laddr prompt run' and 'laddr prompt list' commands.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from laddr.cli.utils import console, print_error, print_success
from laddr.core import LaddrConfig, run_agent


@click.group(name="prompt")
def prompt():
    """Run and manage prompt executions."""


@prompt.command(name="run")
@click.argument("prompt_name")
@click.option(
    "--input",
    "-i",
    "inputs",
    multiple=True,
    help="Input as KEY=VALUE pair (can be repeated)",
)
@click.option(
    "--json",
    "-j",
    "json_input",
    help="Input as JSON string or @file.json",
)
@click.option(
    "--wait/--no-wait",
    default=True,
    help="Wait for completion (default: wait)",
)
@click.option(
    "--timeout",
    default=60,
    help="Timeout in seconds (default: 60)",
)
def run_prompt(prompt_name: str, inputs: tuple, json_input: str | None, wait: bool, timeout: int):
    """
    Run a prompt execution.
    
    Examples:
        laddr prompt run researcher --input query="AI trends"
        laddr prompt run researcher --json '{"query": "AI trends"}'
        laddr prompt run researcher --json @inputs.json
    """
    try:
        # Parse inputs
        parsed_inputs = {}

        if json_input:
            if json_input.startswith("@"):
                # Load from file
                file_path = Path(json_input[1:])
                if not file_path.exists():
                    print_error(f"Input file not found: {file_path}")
                    return
                with open(file_path) as f:
                    parsed_inputs = json.load(f)
            else:
                # Parse JSON string
                parsed_inputs = json.loads(json_input)

        # Add KEY=VALUE inputs
        for inp in inputs:
            if "=" not in inp:
                print_error(f"Invalid input format: {inp}. Expected KEY=VALUE")
                return
            key, value = inp.split("=", 1)
            parsed_inputs[key] = value

        if not parsed_inputs:
            print_error("No inputs provided. Use --input KEY=VALUE or --json")
            return

        console.print(f"[cyan]Running prompt:[/cyan] {prompt_name}")
        console.print(f"[dim]Inputs:[/dim] {json.dumps(parsed_inputs, indent=2)}")

        # Load config and run
        config = LaddrConfig()

        result = asyncio.run(run_agent(
            agent_name=prompt_name,
            inputs=parsed_inputs,
            env_config=config
        ))

        prompt_id = result.get("prompt_id") or result.get("job_id")

        if result.get("status") == "success":
            print_success(f"Prompt completed: {prompt_id}")
            console.print("\n[green bold]Result:[/green bold]")
            console.print(json.dumps(result.get("result"), indent=2))
        else:
            print_error(f"Prompt failed: {result.get('error')}")
            console.print(f"[dim]Prompt ID:[/dim] {prompt_id}")

    except Exception as e:
        print_error(f"Failed to run prompt: {e}")
        if "--debug" in click.get_current_context().params:
            raise


@prompt.command(name="list")
@click.option(
    "--limit",
    default=20,
    help="Maximum number of prompts to show (default: 20)",
)
def list_prompts(limit: int):
    """List recent prompt executions."""
    try:
        from laddr.core import DatabaseService, LaddrConfig

        config = LaddrConfig()
        db = DatabaseService(config.database_url)

        prompts = db.list_prompts(limit=limit)

        if not prompts:
            console.print("[yellow]No prompt executions found[/yellow]")
            return

        console.print(f"\n[cyan bold]Recent Prompts[/cyan bold] (limit: {limit})\n")

        for prompt in prompts:
            status = prompt.get("status", "unknown")
            status_color = {
                "completed": "green",
                "pending": "yellow",
                "running": "blue",
                "failed": "red"
            }.get(status, "dim")

            console.print(f"[{status_color}]●[/{status_color}] {prompt.get('prompt_id')} - {prompt.get('prompt_name')}")
            console.print(f"   Status: [{status_color}]{status}[/{status_color}]")
            console.print(f"   Created: {prompt.get('created_at')}")
            console.print()

    except Exception as e:
        print_error(f"Failed to list prompts: {e}")
