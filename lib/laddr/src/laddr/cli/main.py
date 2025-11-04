"""
Laddr CLI - Production-grade modular CLI.

Provides project initialization, agent management, and Docker orchestration.
"""

from __future__ import annotations

import sys
import traceback

import click

from .commands import (
    add,
    check,
    infra,
    init,
    logs,
    prompt,
    ps,
    run,
    run_dev_alias,
    scale,
    stop,
)
from .utils import LaddrError, console, print_error


try:
    from laddr import __version__ as pkg_version
except ImportError:
    pkg_version = "0.2.3"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=pkg_version, prog_name="Laddr")
def cli():
    """Laddr - Transparent, Docker-native agent framework."""


cli.add_command(init)
cli.add_command(add)
cli.add_command(run)
cli.add_command(logs)
cli.add_command(ps)
cli.add_command(scale)
cli.add_command(stop)
cli.add_command(run_dev_alias)
cli.add_command(check)
cli.add_command(prompt)
cli.add_command(infra)



@cli.command(name="run-local")
@click.argument("agent")
@click.option("--input", "input_json", default="{}", help="JSON input to the agent")
def run_local(agent: str, input_json: str):
    """Run an agent once locally using in-memory components (no Redis/DB)."""
    import json
    import asyncio
    import os
    import sys
    # Ensure current working directory is importable (for 'agents' package)
    try:
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
    except Exception:
        pass
    # Sensible local defaults to avoid external deps
    try:
        if not os.environ.get("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite:///laddr.db"
        if not os.environ.get("QUEUE_BACKEND") and not os.environ.get("REDIS_URL"):
            os.environ["QUEUE_BACKEND"] = "memory"
    except Exception:
        pass
    from laddr.core.config import load_agents

    try:
        payload = json.loads(input_json)
    except Exception as e:
        raise click.ClickException(f"Invalid JSON for --input: {e}")

    agents = load_agents()
    a = agents.get(agent)
    if a is None:
        # Fallback: try instantiating legacy-style agent (requires config/env)
        try:
            mod = __import__(f"agents.{agent}.handler", fromlist=["*"])
            cls_name = f"{agent.capitalize()}Agent"
            AgentCls = getattr(mod, cls_name)
            from laddr.core.config import LaddrConfig, AgentConfig  # type: ignore
            cfg = AgentConfig(name=agent, role=getattr(AgentCls, "ROLE", agent), goal=getattr(AgentCls, "GOAL", ""))
            env = LaddrConfig()
            a = AgentCls(cfg, env)
        except Exception as e:
            hint = (
                "Make sure you're running this command from your project root where the 'agents/' folder exists, "
                "and that 'agents/__init__.py' is present."
            )
            raise click.ClickException(f"Agent not found or cannot be constructed: {e}\n{hint}")

    result = asyncio.run(a.handle(payload))
    click.echo(json.dumps(result, ensure_ascii=False))


def main():
    """Main entry point with error handling."""
    try:
        cli()
    except LaddrError as e:
        print_error(e.message, hint=e.hint)
        sys.exit(1)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red bold]Unexpected error:[/red bold] {e}")
        if "--debug" in sys.argv:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
