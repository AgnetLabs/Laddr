"""
Structured logging utilities for Laddr CLI.

Provides rich-formatted console output with proper log levels.
"""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.theme import Theme


# Custom theme for Laddr CLI
laddr_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "debug": "dim",
    }
)

# Global console instance
console = Console(theme=laddr_theme)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger with rich handler.

    Args:
        name: Logger name (usually __name__)
        level: Log level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Add rich handler
    handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger


def print_success(message: str, details: str | None = None) -> None:
    """Print a success message.

    Args:
        message: Main success message
        details: Optional additional details
    """
    console.print(f"[success]✓[/success] {message}")
    if details:
        console.print(f"  {details}", style="dim")


def print_error(message: str, hint: str | None = None) -> None:
    """Print an error message.

    Args:
        message: Error message
        hint: Optional hint for resolution
    """
    console.print(f"[error]✗[/error] {message}")
    if hint:
        console.print(f"  [dim]Hint:[/dim] {hint}", style="yellow")


def print_warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Warning message
    """
    console.print(f"[warning]![/warning] {message}")


def print_info(message: str) -> None:
    """Print an info message.

    Args:
        message: Info message
    """
    console.print(f"[info]ℹ[/info] {message}")


def print_panel(title: str, content: str, style: str = "cyan") -> None:
    """Print a styled panel.

    Args:
        title: Panel title
        content: Panel content
        style: Panel border style (default: cyan)
    """
    console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style=style))


def print_table(data: list[dict], title: str | None = None) -> None:
    """Print data as a rich table.

    Args:
        data: List of dictionaries (each dict is a row)
        title: Optional table title
    """
    from rich.table import Table

    if not data:
        console.print("[dim]No data to display[/dim]")
        return

    table = Table(title=title, show_header=True, header_style="bold cyan")

    # Add columns from first row keys
    for key in data[0].keys():
        table.add_column(key, style="white")

    # Add rows
    for row in data:
        table.add_row(*[str(v) for v in row.values()])

    console.print(table)
