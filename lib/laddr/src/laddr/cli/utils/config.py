"""
Configuration schemas and validation for Laddr projects.

Uses Pydantic for type-safe YAML configuration parsing.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator
import yaml

from .errors import InvalidConfigError

class ProjectConfigSchema(BaseModel):
    """Project configuration schema (laddr.yml)."""

    project: ProjectDetails = Field(..., description="Project details")

    @classmethod
    def load_from_file(cls, path: Path) -> ProjectConfigSchema:
        """Load project config from YAML file.

        Args:
            path: Path to laddr.yml

        Returns:
            Parsed project configuration

        Raises:
            InvalidConfigError: If config is invalid
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except FileNotFoundError:
            raise InvalidConfigError(str(path), "File not found")
        except yaml.YAMLError as e:
            raise InvalidConfigError(str(path), f"Invalid YAML: {e}")
        except Exception as e:
            raise InvalidConfigError(str(path), str(e))

    def save_to_file(self, path: Path) -> None:
        """Save project config to YAML file.

        Args:
            path: Path to laddr.yml

        Raises:
            InvalidConfigError: If save fails
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.model_dump(exclude_none=True),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )
        except Exception as e:
            raise InvalidConfigError(str(path), f"Failed to save: {e}")


class ProjectDetails(BaseModel):
    """Project details section."""

    name: str = Field(..., description="Project name")
    broker: str = Field(default="redis", description="Message broker type")
    database: str = Field(default="postgres", description="Database type")
    storage: str = Field(default="minio", description="Storage backend")
    tracing: bool = Field(default=True, description="Enable tracing")
    metrics: bool = Field(default=True, description="Enable metrics")
    agents: list[str] = Field(default_factory=list, description="List of agent names")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Project name must be alphanumeric (with underscores/hyphens)")
        return v


def validate_project_directory(path: Path) -> bool:
    """Check if a directory contains a valid Laddr project.

    Args:
        path: Directory path to check

    Returns:
        True if valid project directory
    """
    return (path / "laddr.yml").exists()

