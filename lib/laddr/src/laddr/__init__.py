"""
Laddr - A small-surface, high-abstraction distributed agent framework.

Laddr provides:
- Minimal API with @actor and @tool decorators
- Pluggable backends (queue, database, LLM, cache)
- Internal observability (no Jaeger/Prometheus needed)
- Async-first architecture
- Docker-native execution
- Real distributed runtime with message bus
"""

__version__ = "0.5.0"

# Core exports
from laddr.core import (
    Agent as CoreAgent,
    AgentConfig,
    AgentRunner,
    WorkerRunner,
    BackendFactory,
    DatabaseService,
    LaddrConfig,
    MemoryBus,
    RedisBus,
    ToolRegistry,
    discover_tools,
    run_agent,
    tool,
)

# Tool override system
from laddr.core.system_tools import (
    override_system_tool,
    list_tool_overrides,
    clear_tool_overrides,
    get_tool_override,
)


def Agent(
    *,
    name: str,
    role: str,
    goal: str,
    backstory: str | None = None,
    tools: "ToolRegistry | list[object] | None" = None,
    llm: object | None = None,
    queue: object | None = None,
    instructions: str | None = None,
    is_coordinator: bool | None = None,
    available_agents: list[str] | None = None,
    max_iterations: int | None = None,  # Maximum autonomous iterations before forced finish
    max_tool_calls: int | None = None,  # Maximum successful tool calls before forced finish
    max_retries: int | None = None,  # reserved for future behavior
    timeout: int | None = None,      # reserved for future behavior
    trace_enabled: bool = True,      # Enable/disable tracing for this agent
    trace_mask: list[str] | set[str] | None = None,  # Event types to exclude from traces
):
    """Factory for user-friendly Agent(...) syntax.

    Creates a CoreAgent instance under the hood using AgentConfig and LaddrConfig.
    Unrecognized parameters like max_retries/timeout are currently accepted for
    forward-compatibility but not used directly.
    """
    cfg = LaddrConfig()
    a_cfg = AgentConfig(
        name=name,
        role=role,
        goal=goal,
        backstory=backstory,
        max_iterations=max_iterations if max_iterations is not None else 5,
    )
    agent = CoreAgent(
        a_cfg,
        cfg,
        tools=tools,  # CoreAgent accepts ToolRegistry or list of callables
        llm=llm,
        queue=queue,
        instructions=instructions,
        is_coordinator=is_coordinator,
        available_agents=available_agents,
    )
    # Set tracing configuration directly on instance
    agent._trace_enabled = bool(trace_enabled)
    agent._trace_mask = set(trace_mask or [])
    # Set max_tool_calls limit if specified
    if max_tool_calls is not None:
        agent._max_tool_calls = max_tool_calls
    return agent


__all__ = [
    # Main API
    "Agent",
    "AgentRunner",
    "WorkerRunner",
    "tool",
    "run_agent",
    # Configuration
    "LaddrConfig",
    "AgentConfig",
    "BackendFactory",
    # Core services
    "DatabaseService",
    "RedisBus",
    "MemoryBus",
    "ToolRegistry",
    "discover_tools",
    # Tool override system
    "override_system_tool",
    "list_tool_overrides",
    "clear_tool_overrides",
    "get_tool_override",
]
