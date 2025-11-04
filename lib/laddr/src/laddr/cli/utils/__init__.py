"""
Utility modules for Laddr CLI.

Provides error handling, logging, configuration, Docker operations,
and template rendering.
"""

from .config import (
    ProjectConfigSchema,
    ProjectDetails,
    validate_project_directory,
)
from .docker import (
    add_worker_to_compose,
    check_docker,
    check_docker_compose,
    compose_down,
    compose_logs,
    compose_ps,
    compose_scale,
    compose_up,
    wait_for_service,
)
from .errors import (
    AgentNotFoundError,
    DockerComposeError,
    DockerNotFoundError,
    LaddrError,
    FileGenerationError,
    InvalidConfigError,
    InvalidInputError,
    NestedProjectError,
    ProjectExistsError,
    ProjectNotFoundError,
    ServiceNotReadyError,
)
from .logger import (
    console,
    get_logger,
    print_error,
    print_info,
    print_panel,
    print_success,
    print_table,
    print_warning,
)
from .templates import TemplateRenderer, get_template_renderer, write_file


__all__ = [
    # Config
    "ProjectConfigSchema",
    "ProjectDetails",
    "validate_project_directory",
    # Docker
    "add_worker_to_compose",
    "check_docker",
    "check_docker_compose",
    "compose_down",
    "compose_logs",
    "compose_ps",
    "compose_scale",
    "compose_up",
    "wait_for_service",
    # Errors
    "AgentNotFoundError",
    "DockerComposeError",
    "DockerNotFoundError",
    "LaddrError",
    "FileGenerationError",
    "InvalidConfigError",
    "InvalidInputError",
    "NestedProjectError",
    "ProjectExistsError",
    "ProjectNotFoundError",
    "ServiceNotReadyError",
    # Logger
    "console",
    "get_logger",
    "print_error",
    "print_info",
    "print_panel",
    "print_success",
    "print_table",
    "print_warning",
    # Templates
    "TemplateRenderer",
    "get_template_renderer",
    "write_file",
]
