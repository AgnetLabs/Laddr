"""
Laddr Core module.

Exports:
- Configuration: LaddrConfig, AgentConfig, ProjectConfig
- Agent runtime: Agent, AgentRunner, run_agent
- Decorators: tool
- Backends: BackendFactory
- Database: DatabaseService
- Message bus: RedisBus, MemoryBus
- Tool registry: ToolRegistry, discover_tools, bind_tools
"""
# NOTE: MCP feature disabled for this release
# - MCP: MCPToolSource, MCPToolRegistry

from .agent_runtime import Agent, AgentMemory
from .cache import InMemoryCache, RedisCache
from .config import (
    AgentConfig,
    BackendFactory,
    CacheBackend as CacheBackendProtocol,
    DatabaseBackend,
    LaddrConfig,
    LLMBackend,
    PipelineConfig,
    ProjectConfig,
    QueueBackend,
)
from .database import (
    AgentRegistry,
    DatabaseService,
    Job,
    Memory,
    PromptExecution,
    Trace,
)
from .llm import AnthropicLLM, GeminiLLM, NoOpLLM, OpenAILLM

# MCP feature disabled for this release
# from .mcp_client import MCPToolRegistry, MCPToolSource

from .message_bus import MemoryBus, RedisBus, ResponseMessage, TaskMessage
from .runtime_entry import AgentRunner, WorkerRunner, run_agent
from .tooling import (
    Tool,
    ToolRegistry,
    bind_tools,
    create_tool_schema,
    discover_tools,
    # register_mcp_tools,  # MCP disabled for this release
    tool,
)

# Backward-compatible aliases for protocol types
LLMBase = LLMBackend

__all__ = [
    # Core classes
    "Agent",
    "AgentMemory",
    "AgentRunner",
    "WorkerRunner",
    "run_agent",
    # Decorators
    "tool",
    # Workflow
    "Workflow",
    # Configuration
    "LaddrConfig",
    "AgentConfig",
    "ProjectConfig",
    "PipelineConfig",
    "BackendFactory",
    # Database
    "DatabaseService",
    "Job",
    "PromptExecution",
    "Trace",
    "Memory",
    "AgentRegistry",
    # Message bus
    "RedisBus",
    "MemoryBus",
    "TaskMessage",
    "ResponseMessage",
    # Tooling
    "Tool",
    "ToolRegistry",
    "discover_tools",
    "bind_tools",
    # "register_mcp_tools",  # MCP disabled for this release
    "create_tool_schema",
    # MCP - disabled for this release
    # "MCPToolSource",
    # "MCPToolRegistry",
    # Backend protocols
    "QueueBackend",
    "DatabaseBackend",
    "LLMBackend",
    "CacheBackendProtocol",
    # Backend implementations
    "InMemoryCache",
    "RedisCache",
    "NoOpLLM",
    "OpenAILLM",
    "AnthropicLLM",
    "GeminiLLM",
    "LLMBase",
]