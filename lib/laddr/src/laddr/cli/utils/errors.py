"""
Error handling utilities for Laddr CLI.

Provides structured exception hierarchy and rich-formatted error display.
"""

from __future__ import annotations


class LaddrError(Exception):
    """Base exception for all Laddr CLI errors."""

    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint
        super().__init__(message)


class ProjectNotFoundError(LaddrError):
    """Raised when not in an Laddr project directory."""

    def __init__(self, message: str = "Not in an Laddr project directory"):
        super().__init__(
            message,
            hint="Run 'laddr init <project_name>' to create a new project",
        )


class ProjectExistsError(LaddrError):
    """Raised when trying to create a project that already exists."""

    def __init__(self, path: str):
        super().__init__(
            f"Directory {path} already contains an Laddr project",
            hint="Use a different directory or delete the existing laddr.yml",
        )


class NestedProjectError(LaddrError):
    """Raised when trying to create a nested project."""

    def __init__(self, parent_path: str):
        super().__init__(
            f"Detected existing Laddr project at {parent_path}",
            hint="Cannot create a nested project inside another Laddr project",
        )


class InvalidConfigError(LaddrError):
    """Raised when configuration files are invalid."""

    def __init__(self, filename: str, details: str):
        super().__init__(
            f"Invalid configuration in {filename}: {details}",
            hint="Check the file syntax and ensure all required fields are present",
        )


class DockerNotFoundError(LaddrError):
    """Raised when Docker is not installed or not running."""

    def __init__(self):
        super().__init__(
            "Docker not found or not running",
            hint="Install Docker (https://docs.docker.com/get-docker/) and ensure it's running",
        )


class DockerComposeError(LaddrError):
    """Raised when Docker Compose operations fail."""

    def __init__(self, operation: str, details: str):
        super().__init__(
            f"Docker Compose {operation} failed: {details}",
            hint="Check docker-compose.yml and ensure all services are properly configured",
        )


class AgentNotFoundError(LaddrError):
    """Raised when an agent doesn't exist."""

    def __init__(self, agent_name: str):
        super().__init__(
            f"Agent '{agent_name}' not found",
            hint=f"Run 'laddr add agent {agent_name}' to create it",
        )


class InvalidInputError(LaddrError):
    """Raised when user input is invalid."""

    def __init__(self, field: str, details: str):
        super().__init__(
            f"Invalid {field}: {details}",
            hint="Check the command usage with --help",
        )


class FileGenerationError(LaddrError):
    """Raised when file generation fails."""

    def __init__(self, filename: str, details: str):
        super().__init__(
            f"Failed to generate {filename}: {details}",
            hint="Check file permissions and available disk space",
        )


class ServiceNotReadyError(LaddrError):
    """Raised when a service is not ready after startup."""

    def __init__(self, service: str, timeout: int):
        super().__init__(
            f"Service '{service}' did not become ready within {timeout} seconds",
            hint=f"Check logs with 'laddr logs {service}' or 'docker compose logs {service}'",
        )
