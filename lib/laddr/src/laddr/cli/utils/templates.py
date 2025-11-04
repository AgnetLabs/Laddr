"""
Template rendering utilities using Jinja2.

Provides file generation from templates with context variables.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

from .errors import FileGenerationError


class TemplateRenderer:
    """Jinja2 template renderer for Laddr CLI."""

    def __init__(self, templates_dir: Path):
        """Initialize template renderer.

        Args:
            templates_dir: Directory containing Jinja2 templates
        """
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Add custom filters
        self.env.filters["snake_case"] = self._snake_case
        self.env.filters["pascal_case"] = self._pascal_case
        self.env.filters["kebab_case"] = self._kebab_case

    @staticmethod
    def _snake_case(value: str) -> str:
        """Convert string to snake_case."""
        return value.replace("-", "_").replace(" ", "_").lower()

    @staticmethod
    def _pascal_case(value: str) -> str:
        """Convert string to PascalCase."""
        return "".join(word.capitalize() for word in value.replace("-", "_").split("_"))

    @staticmethod
    def _kebab_case(value: str) -> str:
        """Convert string to kebab-case."""
        return value.replace("_", "-").replace(" ", "-").lower()

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with context.

        Args:
            template_name: Template filename
            context: Template context variables

        Returns:
            Rendered template content

        Raises:
            FileGenerationError: If template rendering fails
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise FileGenerationError(template_name, str(e))

    def render_to_file(
        self,
        template_name: str,
        output_path: Path,
        context: dict[str, Any],
        create_dirs: bool = True,
    ) -> None:
        """Render a template and write to file.

        Args:
            template_name: Template filename
            output_path: Output file path
            context: Template context variables
            create_dirs: Create parent directories if needed (default: True)

        Raises:
            FileGenerationError: If rendering or writing fails
        """
        content = self.render_template(template_name, context)

        try:
            if create_dirs:
                output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise FileGenerationError(str(output_path), str(e))

    def render_string(self, template_str: str, context: dict[str, Any]) -> str:
        """Render a template string with context.

        Args:
            template_str: Template string
            context: Template context variables

        Returns:
            Rendered content

        Raises:
            FileGenerationError: If rendering fails
        """
        try:
            template = Template(template_str)
            return template.render(**context)
        except Exception as e:
            raise FileGenerationError("inline template", str(e))


def get_template_renderer() -> TemplateRenderer:
    """Get a configured template renderer.

    Returns:
        TemplateRenderer instance with CLI templates directory
    """
    # Find templates directory relative to this file
    cli_dir = Path(__file__).parent.parent
    templates_dir = cli_dir / "templates"

    if not templates_dir.exists():
        raise FileGenerationError(
            "templates directory",
            f"Templates directory not found at {templates_dir}",
        )

    return TemplateRenderer(templates_dir)


def write_file(path: Path, content: str, create_dirs: bool = True) -> None:
    """Write content to a file.

    Args:
        path: File path
        content: File content
        create_dirs: Create parent directories if needed (default: True)

    Raises:
        FileGenerationError: If write fails
    """
    try:
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise FileGenerationError(str(path), str(e))
