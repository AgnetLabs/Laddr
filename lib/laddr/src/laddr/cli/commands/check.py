"""
Diagnostic command for Laddr CLI.

Runs the DiagnosticAgent if present and prints a structured report.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import click

from ..utils import (
    ProjectNotFoundError,
    console,
    print_error,
    print_info,
    print_success,
    validate_project_directory,
)


@click.command("check")
@click.option("--output", "output_path", default="diagnostic_report.json", help="Path to write JSON report")
def check(output_path: str):
    """Run diagnostic checks for the Laddr runtime using the DiagnosticAgent."""
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    try:
        mod = importlib.import_module("agents.diagnostic.handler")
    except Exception:
        print_error(
            "Diagnostic agent not found. Run: laddr add agent diagnostic",
            hint="This creates agents/diagnostic/handler.py"
        )
        raise click.Abort()

    AgentClass = getattr(mod, "DiagnosticAgent", None)
    if AgentClass is None:
        print_error("Invalid diagnostic agent module")
        raise click.Abort()

    import asyncio

    from laddr.core import AgentRunner, LaddrConfig  # type: ignore

    print_info("Running diagnostic checks...")
    runner = AgentRunner(env_config=LaddrConfig())
    report = asyncio.run(runner.run({"payload": {}}, agent_name="diagnostic"))

    results = report.get("results", [])
    ok_count = 0
    for r in results:
        status = r.get("status")
        subsystem = r.get("subsystem")
        message = r.get("message")
        prefix = "[green]✓[/green]" if status == "ok" else "[red]✗[/red]"
        console.print(f"{prefix} {subsystem}: {message}")
        if status == "ok":
            ok_count += 1

    overall_ok = ok_count == len(results)
    if overall_ok:
        console.print("\n[bold green]✅ Diagnostic complete: all subsystems operational[/bold green]")
    else:
        console.print("\n[bold red]❌ Diagnostic complete: issues detected[/bold red]")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print_success(f"Report saved to {output_path}")
    except Exception as e:
        print_error(f"Failed to write report: {e}")
