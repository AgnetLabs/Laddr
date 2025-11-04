"""
CLI command to show infrastructure configuration and status.
"""

from __future__ import annotations

import click

from laddr.cli.utils import console, print_error


@click.command(name="infra")
@click.option(
    "--show-config/--no-show-config",
    default=True,
    help="Show configuration values",
)
def infra(show_config: bool):
    """Show infrastructure configuration and status."""
    try:
        from laddr.core import LaddrConfig

        config = LaddrConfig()

        console.print("\n[cyan bold]Laddr Infrastructure[/cyan bold]\n")

        # Queue backend
        console.print(f"[green]Queue Backend:[/green] {config.queue_backend}")
        if config.queue_backend == "redis":
            console.print(f"  └─ URL: [dim]{config.redis_url}[/dim]")

        # Database backend
        console.print(f"\n[green]Database:[/green] {config.db_backend}")
        if show_config:
            console.print(f"  └─ URL: [dim]{config.database_url}[/dim]")

        # LLM backend
        console.print(f"\n[green]LLM Backend:[/green] {config.llm_backend}")
        if config.llm_model:
            console.print(f"  └─ Model: [dim]{config.llm_model}[/dim]")

        # Storage
        console.print("\n[green]Storage:[/green] MinIO")
        if show_config:
            console.print(f"  ├─ Endpoint: [dim]{config.minio_endpoint}[/dim]")
            console.print(f"  ├─ Bucket: [dim]{config.minio_bucket}[/dim]")
            console.print(f"  └─ Large response offload: [dim]{'enabled' if config.enable_large_response_storage else 'disabled'}[/dim]")
            if config.enable_large_response_storage:
                console.print(f"     └─ Threshold: [dim]{config.storage_threshold_kb} KB[/dim]")

        # Cache backend
        console.print(f"\n[green]Cache:[/green] {config.cache_backend}")
        if config.cache_backend == "redis" and show_config:
            console.print(f"  └─ URL: [dim]{config.redis_url}[/dim]")

        # Observability
        console.print("\n[green]Observability:[/green]")
        console.print(f"  ├─ Tracing: [dim]{'enabled (DB)' if config.enable_tracing else 'disabled'}[/dim]")
        console.print(f"  └─ Metrics: [dim]{'enabled (DB)' if config.enable_metrics else 'disabled'}[/dim]")

        console.print()

    except Exception as e:
        print_error(f"Failed to show infrastructure: {e}")
