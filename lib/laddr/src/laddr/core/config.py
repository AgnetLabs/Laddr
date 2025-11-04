"""
Laddr v3 lightweight config helpers.

This module exposes helpers to construct bus, storage, tracer, and to
resolve agents dynamically from the 'agents' package if present.
"""

from __future__ import annotations

import importlib
import inspect
from typing import Dict, Any

def load_agents() -> Dict[str, Any]:
    """Load agents dynamically from 'agents.<name>.handler'.

    Supports two patterns:
    1) @actor-decorated classes named <Name>Agent (instantiated without args)
    2) Module-level Agent instances (any variable bound to laddr.core.agent_runtime.Agent)
    """
    discovered: Dict[str, Any] = {}
    try:
        agents_pkg = importlib.import_module("agents")
        import pkgutil

        for m in pkgutil.iter_modules(agents_pkg.__path__):
            name = m.name
            try:
                mod = importlib.import_module(f"agents.{name}.handler")

                # Prefer class pattern: <Name>Agent
                # We intentionally do NOT instantiate here to avoid needing configs.
                # run-local has a fallback path that constructs the class with AgentConfig/LaddrConfig.
                # So we skip adding classes in this discovery step.
                # cls_name = f"{name.capitalize()}Agent"
                # AgentCls = getattr(mod, cls_name, None)
                # if inspect.isclass(AgentCls):
                #     pass

                # Instance pattern: find any Agent instance in module globals
                for var_name, obj in vars(mod).items():
                    if not inspect.isclass(obj) and callable(getattr(obj, "handle", None)):
                        discovered[name] = obj
                        break
            except Exception:
                continue
    except Exception:
        pass
    return discovered
"""
Configuration management for Laddr.

Provides pluggable backend configuration via environment and YAML.
All integrations (queue, database, LLM, cache) are configurable.
"""

from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml


class LaddrConfig(BaseSettings):
    """
    Environment-based configuration for Laddr runtime.
    
    Supports pluggable backends for all infrastructure:
    - queue_backend: "redis" (default) | "memory"
    - db_backend: "postgres" (default) | "sqlite"
    - llm_backend: "noop" (default) | "openai" | "anthropic" | "gemini"
    - cache_backend: "inmemory" (default) | "redis"
    """

    # Pluggable backend selection
    queue_backend: str = Field(default="redis", description="Message queue backend")
    db_backend: str = Field(default="postgres", description="Database backend")
    llm_backend: str = Field(default="noop", description="LLM backend (noop=echo)")
    llm_model: str | None = Field(default=None, description="LLM model name (optional, backend-specific)")
    openai_base_url: str | None = Field(default=None, description="OpenAI-compatible base URL (e.g., vLLM)")
    cache_backend: str = Field(default="inmemory", description="Cache backend")

    # Database connection
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/laddr",
        description="Database connection URL (postgres or sqlite)",
    )

    # Redis connection (for queue and optional cache)
    redis_url: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )

    # Kafka (optional)
    kafka_bootstrap: str | None = Field(default=None, description="Kafka bootstrap servers (host:port)")

    # S3-Compatible Storage (AWS S3, MinIO, or compatible services)
    # For AWS S3: set endpoint to "s3.amazonaws.com", secure=True, and provide AWS credentials
    # For MinIO: set endpoint to "localhost:9000" or "minio:9000", secure=False
    storage_endpoint: str = Field(
        default="localhost:9000",
        description="S3-compatible storage endpoint (s3.amazonaws.com for AWS, localhost:9000 for MinIO)"
    )
    storage_access_key: str = Field(
        default="minioadmin",
        description="Storage access key (AWS Access Key ID or MinIO access key)"
    )
    storage_secret_key: str = Field(
        default="minioadmin123",
        description="Storage secret key (AWS Secret Access Key or MinIO secret key)"
    )
    storage_secure: bool = Field(
        default=False,
        description="Use HTTPS for storage (True for AWS S3, False for local MinIO)"
    )
    storage_region: str | None = Field(
        default=None,
        description="AWS region (e.g., 'us-east-1') - only needed for AWS S3"
    )
    storage_bucket: str = Field(
        default="laddr",
        description="Default storage bucket name"
    )

    # Tracing and metrics (stored in DB, not external services)
    enable_tracing: bool = Field(default=True, description="Enable internal tracing to DB")
    enable_metrics: bool = Field(default=True, description="Enable internal metrics collection")

    # Large Response Storage
    enable_large_response_storage: bool = Field(
        default=True, description="Enable automatic storage of large responses in S3-compatible storage"
    )
    storage_threshold_kb: int = Field(
        default=100, description="Size threshold in KB for storing responses in S3-compatible storage"
    )

    # Inline workers: when running locally via AgentRunner, also spin up
    # lightweight in-process workers to consume delegated tasks without Docker
    enable_inline_workers: bool = Field(
        default=True,
        description="Run inline local workers during AgentRunner.run() so delegated tasks execute without external workers",
    )

    # API
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    api_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins (avoid * in production)"
    )

    # Dashboard URL (for containerized setups)
    dashboard_url: str = Field(
        default="http://localhost:5173",
        description="Dashboard URL for links from API"
    )

    # Agent worker settings
    agent_name: str | None = Field(
        default=None, description="Agent name for worker mode"
    )
    worker_concurrency: int = Field(
        default=1, description="Number of concurrent tasks per worker"
    )

    # Coordinator-Specialist Architecture
    has_coordinator: bool = Field(
        default=False,
        description="Enable coordinator-specialist mode where all results route to coordinator"
    )
    coordinator_agent: str = Field(
        default="coordinator",
        description="Name of the coordinator agent (used when has_coordinator=True)"
    )
    
    # Delegation execution style
    # If True, delegation will block and wait for responses (legacy behavior).
    # If False, use the non-blocking pause/resume orchestration model (default).
    blocking_delegation: bool = Field(
        default=True,
        description=(
            "If True, delegation blocks and waits for delegated-agent responses. "
            "If False, delegation uses non-blocking pause/resume (recommended for production)."
        ),
    )
    
    # MCP (Model Context Protocol) Integration - DISABLED FOR THIS RELEASE
    # mcp_servers: list[dict[str, str]] = Field(
    #     default_factory=list,
    #     description="List of MCP server configs with 'url' and optional 'api_key'"
    # )

    # LLM API keys (optional, used when respective llm_backend is selected)
    gemini_api_key: str | None = Field(
        default=None, description="Google Gemini API key"
    )
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key"
    )
    anthropic_api_key: str | None = Field(
        default=None, description="Anthropic API key"
    )
    groq_api_key: str | None = Field(
        default=None, description="Groq API key"
    )
    xai_api_key: str | None = Field(
        default=None, description="xAI Grok API key"
    )
    grok_api_key: str | None = Field(
        default=None, description="xAI Grok API key (alias)"
    )
    http_llm_endpoint: str | None = Field(default=None, description="Generic HTTP LLM endpoint URL")

    # Tool API keys (optional)
    serper_api_key: str | None = Field(
        default=None, description="Serper.dev API key for web search"
    )

    # Dashboard auth (optional)
    laddr_dash_users: str | None = Field(
        default=None, description="Dashboard user credentials (user:pass)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore unknown fields from environment


# Backend protocols for pluggable implementations

# keep these:- interface defs
class QueueBackend(Protocol):
    """Protocol for message queue backends."""

    async def register_agent(self, name: str, metadata: dict) -> bool: ...
    async def publish_task(self, agent_name: str, task: dict) -> str: ...
    async def publish_response(self, task_id: str, response: dict) -> bool: ...
    async def consume_tasks(self, agent_name: str, block_ms: int, count: int) -> list[dict]: ...
    async def wait_for_response(self, task_id: str, timeout_sec: int) -> dict | None: ...
    async def get_registered_agents(self) -> dict[str, dict]: ...
    async def get_queue_depth(self, agent_name: str) -> int: ...
    async def health_check(self) -> bool: ...


class DatabaseBackend(Protocol):
    """Protocol for database backends."""

    def create_job(self, job_id: str, pipeline: str, inputs: dict) -> None: ...
    def save_result(self, job_id: str, outputs: dict) -> None: ...
    def get_result(self, job_id: str) -> dict | None: ...
    def list_jobs(self, limit: int) -> list[dict]: ...
    def append_trace(self, job_id: str, agent_name: str, event_type: str, payload: dict) -> None: ...
    def memory_put(self, agent_name: str, key: str, value: Any, job_id: str | None = None) -> None: ...
    def memory_get(self, agent_name: str, key: str, job_id: str | None = None) -> Any: ...
    def register_agent(self, agent_name: str, metadata: dict) -> None: ...
    def list_agents(self) -> list[dict]: ...



class LLMBackend(Protocol):
    """Protocol for LLM backends."""

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> str: ...


class CacheBackend(Protocol):
    """Protocol for cache backends."""

    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def clear(self) -> None: ...


class BackendFactory:
    """
    Factory for creating backend instances based on configuration.
    
    Provides pluggable implementations for queue, database, LLM, and cache.
    """

    def __init__(self, config: LaddrConfig):
        self.config = config

    # Singleton memory bus shared across agents within a process
    _memory_bus_singleton = None

    def create_queue_backend(self) -> QueueBackend:
        """Create message queue backend based on config."""
        import os as _os
        # Respect explicit env override first
        backend = _os.environ.get("QUEUE_BACKEND", self.config.queue_backend)
        # Smart default: if user didn't explicitly opt into Redis (no env for
        # QUEUE_BACKEND and no REDIS_URL), then default to in-memory for a
        # frictionless local run.
        if backend == "redis" and ("QUEUE_BACKEND" not in _os.environ) and ("REDIS_URL" not in _os.environ):
            backend = "memory"

        if backend == "redis":
            from .message_bus import RedisBus
            bus = RedisBus(self.config.redis_url)
        elif backend == "memory":
            from .message_bus import MemoryBus
            if BackendFactory._memory_bus_singleton is None:
                BackendFactory._memory_bus_singleton = MemoryBus()
            bus = BackendFactory._memory_bus_singleton
        elif backend == "kafka":
            from .message_bus import KafkaBus
            if not self.config.kafka_bootstrap:
                raise ValueError("kafka_bootstrap is required for kafka queue_backend")
            bus = KafkaBus(self.config.kafka_bootstrap)
        else:
            raise ValueError(f"Unknown queue_backend: {backend}")

        # Optionally enable large-response offload to storage
        try:
            if getattr(self.config, "enable_large_response_storage", True):
                print(f"[STORAGE] Enabling large response storage (threshold={self.config.storage_threshold_kb} KB)")
                storage = self.create_storage_backend()
                bus._storage = storage
                # Use new storage_bucket field, fallback to old minio_bucket for compatibility
                bucket = self.config.storage_bucket or self.config.minio_bucket or "laddr"
                bus._storage_bucket = bucket
                bus._storage_threshold_kb = self.config.storage_threshold_kb
                print(f"[STORAGE] Configured: bucket={bucket}, threshold={self.config.storage_threshold_kb} KB")
        except Exception as e:
            # Non-fatal: continue without offload
            print(f"[STORAGE] Failed to enable storage: {e}")
            import traceback
            traceback.print_exc()
            pass

        return bus

    def create_database_backend(self) -> DatabaseBackend:
        """Create database backend based on config."""
        from .database import DatabaseService
        import os as _os
        # Prefer env override if present, then config, else SQLite
        db_url = _os.environ.get("DATABASE_URL") or self.config.database_url or "sqlite:///laddr.db"
        return DatabaseService(db_url)

    def create_llm_backend(self) -> LLMBackend:
        """Create LLM backend based on config."""
        if self.config.llm_backend == "noop":
            from .llm import NoOpLLM
            return NoOpLLM()
        if self.config.llm_backend == "openai":
            from .llm import OpenAILLM
            return OpenAILLM(self.config.openai_api_key, self.config.llm_model, base_url=self.config.openai_base_url)
        if self.config.llm_backend == "anthropic":
            from .llm import AnthropicLLM
            return AnthropicLLM(self.config.anthropic_api_key, self.config.llm_model)
        if self.config.llm_backend == "gemini":
            from .llm import GeminiLLM
            return GeminiLLM(self.config.gemini_api_key, self.config.llm_model)
        if self.config.llm_backend == "groq":
            from .llm import GroqLLM
            return GroqLLM(self.config.groq_api_key, self.config.llm_model)
        if self.config.llm_backend == "grok":
            from .llm import GrokLLM
            return GrokLLM(self.config.xai_api_key or self.config.grok_api_key, self.config.llm_model)
        if self.config.llm_backend == "http":
            from .llm import HTTPLLM
            if not self.config.http_llm_endpoint:
                raise ValueError("http_llm_endpoint is required for http llm_backend")
            return HTTPLLM(self.config.http_llm_endpoint)
        if self.config.llm_backend == "vllm":
            from .llm import OpenAILLM
            if not self.config.openai_base_url:
                raise ValueError("openai_base_url is required for vllm llm_backend")
            return OpenAILLM(self.config.openai_api_key, self.config.llm_model, base_url=self.config.openai_base_url)
        raise ValueError(f"Unknown llm_backend: {self.config.llm_backend}")

    def create_cache_backend(self) -> CacheBackend:
        """Create cache backend based on config."""
        if self.config.cache_backend == "inmemory":
            from .cache import InMemoryCache
            return InMemoryCache()
        if self.config.cache_backend == "redis":
            from .cache import RedisCache
            return RedisCache(self.config.redis_url)
        raise ValueError(f"Unknown cache_backend: {self.config.cache_backend}")

    def create_storage_backend(self):
        """
        Create S3-compatible storage backend (AWS S3, MinIO, or compatible).
        
        Supports backward compatibility with old minio_* field names.
        """
        # Use new storage_* fields, fallback to old minio_* fields for backward compatibility
        endpoint = (
            self.config.storage_endpoint
            if self.config.storage_endpoint != "localhost:9000" or self.config.minio_endpoint is None
            else self.config.minio_endpoint or self.config.storage_endpoint
        )
        access_key = self.config.storage_access_key
        secret_key = self.config.storage_secret_key
        secure = self.config.storage_secure
        region = self.config.storage_region
        
        if endpoint:
            from .storage import S3Storage
            return S3Storage(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                region=region
            )
        # Fall back to in-memory storage if no storage configured
        from .storage import InMemoryStorage
        return InMemoryStorage()



class ProjectConfig(BaseModel):
    """
    Project configuration from laddr.yml.
    
    Defines which agents exist and backend preferences.
    """

    name: str = Field(description="Project name")

    # Backend selections (can override env defaults)
    queue_backend: str = Field(default="redis", description="Message queue backend")
    db_backend: str = Field(default="postgres", description="Database backend")
    llm_backend: str = Field(default="noop", description="LLM backend")
    cache_backend: str = Field(default="inmemory", description="Cache backend")

    # Agent registry
    agents: list[str] = Field(default_factory=list, description="List of agent names")


class AgentConfig(BaseModel):
    """
    Agent configuration (minimal for @actor pattern).
    
    Most runtime config is auto-discovered or comes from LaddrConfig.
    """

    name: str
    role: str
    goal: str
    backstory: str | None = None
    max_iterations: int = Field(default=5)  # Reduced from 7 to 5 - forced finish at 4 successful tools
    allow_delegation: bool = Field(default=True)
    verbose: bool = Field(default=False)


class PipelineStage(BaseModel):
    """Stage definition in a pipeline (simplified)."""

    agent: str = Field(description="Agent name to execute")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Stage inputs")


class PipelineConfig(BaseModel):
    """Pipeline configuration for sequential agent execution."""

    name: str
    description: str | None = None
    stages: list[PipelineStage]
