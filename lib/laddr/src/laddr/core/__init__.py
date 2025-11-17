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
- System tools: TaskDelegationTool, ParallelDelegationTool, ArtifactStorageTool
- MCP: MCPToolProvider, MultiMCPToolProvider, MCPClient
"""

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

from .mcp_client import MCPClient, MCPError, MCPTransport
from .mcp_tools import MCPToolProvider, MultiMCPToolProvider

from .message_bus import MemoryBus, RedisBus, ResponseMessage, TaskMessage
from .runtime_entry import AgentRunner, WorkerRunner, run_agent
from .system_tools import (
    ArtifactStorageTool,
    ParallelDelegationTool,
    TaskDelegationTool,
    clear_tool_overrides,
    create_system_tools,
    get_tool_override,
    list_tool_overrides,
    override_system_tool,
)
from .tooling import (
    Tool,
    ToolRegistry,
    bind_tools,
    create_tool_schema,
    discover_tools,
    register_mcp_tools,
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
    "register_mcp_tools",
    "create_tool_schema",
    # System tools - base classes for user extensions
    "TaskDelegationTool",
    "ParallelDelegationTool",
    "ArtifactStorageTool",
    "override_system_tool",
    "get_tool_override",
    "list_tool_overrides",
    "clear_tool_overrides",
    "create_system_tools",
    # MCP
    "MCPToolProvider",
    "MultiMCPToolProvider",
    "MCPClient",
    "MCPError",
    "MCPTransport",
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