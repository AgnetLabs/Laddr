"""
Tool system with decorator, registry, and auto-discovery.

Provides @tool decorator for marking functions as agent tools,
ToolRegistry for managing available tools, and auto-discovery
from agents.<name>.tools packages.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import importlib
import inspect
import pkgutil
from typing import Any, get_type_hints


try:
    from pydantic import BaseModel, create_model
except ImportError:
    BaseModel = None
    create_model = None


@dataclass
class Tool:
    """
    Tool metadata and callable.
    
    Represents a single tool that can be invoked by agents.
    """

    name: str
    func: Callable
    description: str
    input_model: type | None = None
    # Optional explicit JSON schema for parameters (for LLM function-calling UIs)
    parameters_schema: dict | None = None
    # Tracing controls
    trace_enabled: bool = True
    trace_mask: set[str] = field(default_factory=set)

    def validate_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate inputs against input_model if available.
        
        Returns validated inputs or raises ValidationError.
        """
        if self.input_model is None:
            return inputs

        if BaseModel and issubclass(self.input_model, BaseModel):
            # Pydantic validation
            validated = self.input_model(**inputs)
            return validated.model_dump()

        # No validation available
        return inputs

    def invoke(self, **kwargs) -> Any:
        """
        Invoke the tool with validated inputs.
        
        Returns tool execution result.
        """
        validated = self.validate_inputs(kwargs)
        return self.func(**validated)


def tool(
    name: str | None = None,
    description: str | None = None,
    *,
    trace: bool = True,
    trace_mask: list[str] | None = None,
    parameters: dict | None = None,
):
    """
    Decorator to mark a function as an agent tool.
    
    Usage:
        @tool(name="web_search", description="Search the web")
        def search(query: str) -> dict:
            return {"results": [...]}
    
    Or with Pydantic input model:
        class SearchInput(BaseModel):
            query: str
            limit: int = 10
        
        @tool()
        def search(inputs: SearchInput) -> dict:
            return {"results": [...]}
    
    The decorator attaches metadata to the function as __laddr_tool__.
    """
    def decorator(func: Callable) -> Callable:
        # Infer name from function if not provided
        tool_name = name or func.__name__

        # Infer description from docstring if not provided
        tool_description = description or (func.__doc__ or "").strip().split("\n")[0]

        # Try to extract input model from type hints
        input_model = None
        try:
            hints = get_type_hints(func)
            # Check if first parameter has a Pydantic BaseModel hint
            params = list(inspect.signature(func).parameters.values())
            if params and BaseModel:
                first_param_hint = hints.get(params[0].name)
                if first_param_hint and inspect.isclass(first_param_hint) and issubclass(first_param_hint, BaseModel):
                    input_model = first_param_hint
        except Exception:
            pass

        # Attach metadata
        func.__laddr_tool__ = Tool(
            name=tool_name,
            func=func,
            description=tool_description,
            input_model=input_model,
            parameters_schema=parameters,
            trace_enabled=bool(trace),
            trace_mask=set(trace_mask or []),
        )

        return func

    return decorator


class ToolRegistry:
    """
    Registry for managing available tools.
    
    Supports registration, lookup, and listing of tools.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._aliases: dict[str, str] = {}  # alias -> canonical name mapping

    def register(self, tool_obj: Tool | Callable, name: str | None = None, aliases: list[str] | None = None) -> None:
        """
        Register a tool with optional aliases.
        
        Args:
            tool_obj: Tool instance or callable to register
            name: Optional explicit name (overrides tool_obj.name)
            aliases: Optional list of alias names that resolve to this tool
        """
        # Determine the canonical name and tool object
        if isinstance(tool_obj, Tool):
            tool = tool_obj
            canonical_name = name or tool.name
            # Update the tool's name if explicit name provided
            if name and name != tool.name:
                tool = Tool(name=name, func=tool.func, description=tool.description)
        elif hasattr(tool_obj, "__laddr_tool__"):
            tool = tool_obj.__laddr_tool__
            canonical_name = name or tool.name
            # Update the tool's name if explicit name provided
            if name and name != tool.name:
                tool = Tool(name=name, func=tool.func, description=tool.description)
        elif callable(tool_obj):
            # Auto-wrap callable without decorator
            canonical_name = name or tool_obj.__name__
            tool = Tool(
                name=canonical_name,
                func=tool_obj,
                description=(tool_obj.__doc__ or "").strip().split("\n")[0]
            )
        else:
            raise ValueError(f"Cannot register {tool_obj} as a tool")

        # Register the tool under its canonical name
        self._tools[canonical_name] = tool

        # Register aliases if provided
        if aliases:
            for alias in aliases:
                self._aliases[alias] = canonical_name

    def get(self, name: str) -> Tool | None:
        """
        Get a tool by name or alias.
        
        Args:
            name: Tool name (canonical or alias)
        
        Returns:
            Tool instance or None if not found
        """
        # Check if name is an alias first
        canonical_name = self._aliases.get(name, name)
        return self._tools.get(canonical_name)

    def list(self) -> list[Tool]:
        """List all registered tools (excludes aliases)."""
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        """List all canonical tool names (excludes aliases)."""
        return list(self._tools.keys())

    def list_all_names(self) -> list[str]:
        """List all names including aliases (for debugging)."""
        return list(self._tools.keys()) + list(self._aliases.keys())

    def has(self, name: str) -> bool:
        """Check if a tool exists (checks both canonical names and aliases)."""
        return name in self._tools or name in self._aliases


def discover_tools(agent_name: str) -> ToolRegistry:
    """
    Auto-discover tools for an agent from agents.<agent_name>.tools package.
    
    Scans for:
    1. Functions decorated with @tool
    2. Functions named 'run' (fallback)
    
    Args:
        agent_name: Name of the agent (e.g., "researcher")
    
    Returns:
        ToolRegistry with discovered tools
    """
    registry = ToolRegistry()

    try:
        # Import the tools package
        tools_module = importlib.import_module(f"agents.{agent_name}.tools")

        # First, scan the package module itself (for tools defined in __init__.py)
        for name, obj in inspect.getmembers(tools_module):
            if hasattr(obj, "__laddr_tool__"):
                registry.register(obj)
            elif name == "run" and callable(obj):
                registry.register(obj)

        # Then, scan all submodules in the tools package
        if hasattr(tools_module, "__path__"):
            for _, module_name, _ in pkgutil.iter_modules(tools_module.__path__):
                try:
                    module = importlib.import_module(f"agents.{agent_name}.tools.{module_name}")

                    for name, obj in inspect.getmembers(module):
                        if hasattr(obj, "__laddr_tool__"):
                            registry.register(obj)
                        elif name == "run" and callable(obj):
                            registry.register(obj)
                except Exception:
                    continue
    except ImportError:
        pass

    return registry


def bind_tools(agent_instance: Any, tools: list[str | Callable]) -> None:
    """
    Bind tools to an agent instance for explicit, readable tool registration.
    
    Supports:
    - String names: auto-import from agents.<agent>.tools.<name>
    - Callables: register directly
    - Decorated functions: extract Tool metadata
    
    Usage:
        from agents.researcher.tools import web_search
        bind_tools(self, [web_search.run, "summarize"])
    
    Args:
        agent_instance: Agent instance with .tools registry
        tools: List of tool names (str) or callables
    """
    if not hasattr(agent_instance, "tools"):
        raise AttributeError("Agent must have .tools ToolRegistry")
    
    agent_name = agent_instance.config.name
    
    for tool_ref in tools:
        if isinstance(tool_ref, str):
            # Auto-import from agents.<agent>.tools.<tool_name>
            try:
                module = importlib.import_module(f"agents.{agent_name}.tools.{tool_ref}")
                # Look for 'run' function or decorated tool
                tool_func = None
                if hasattr(module, "run"):
                    tool_func = module.run
                else:
                    # Find first decorated function
                    for name, obj in inspect.getmembers(module):
                        if hasattr(obj, "__laddr_tool__"):
                            tool_func = obj
                            break
                
                if tool_func:
                    agent_instance.tools.register(tool_func)
            except ImportError as e:
                raise ImportError(f"Could not import tool '{tool_ref}' for agent '{agent_name}': {e}")
        elif callable(tool_ref):
            # Register callable directly
            agent_instance.tools.register(tool_ref)
        else:
            raise ValueError(f"Tool must be string or callable, got {type(tool_ref)}")


# MCP feature disabled for this release
# def register_mcp_tools(agent_instance: Any, mcp_source: Any) -> None:
#     """
#     Register MCP-discovered tools to an agent instance.
#     
#     Fetches tools from MCPToolSource and wraps them as callables.
#     
#     Usage:
#         from laddr.core.mcp_client import MCPToolSource
#         mcp = MCPToolSource("http://localhost:3000", api_key="...")
#         register_mcp_tools(self, mcp)
#     
#     Args:
#         agent_instance: Agent instance with .tools registry
#         mcp_source: MCPToolSource instance
#     """
#     import asyncio
#     
#     if not hasattr(agent_instance, "tools"):
#         raise AttributeError("Agent must have .tools ToolRegistry")
#     
#     # Discover tools from MCP server
#     try:
#         tools_metadata = asyncio.run(mcp_source.discover())
#     except Exception as e:
#         raise RuntimeError(f"Failed to discover MCP tools: {e}")
#     
#     # Wrap each MCP tool as a callable
#     for tool_meta in tools_metadata:
#         tool_name = tool_meta.get("name")
#         tool_desc = tool_meta.get("description", "")
#         
#         # Create async wrapper
#         async def mcp_tool_wrapper(**kwargs):
#             return await mcp_source.call_tool(tool_name, kwargs)
#         
#         # Create sync wrapper for compatibility
#         def sync_wrapper(**kwargs):
#             return asyncio.run(mcp_tool_wrapper(**kwargs))
#         
#         sync_wrapper.__name__ = tool_name
#         sync_wrapper.__doc__ = tool_desc
#         
#         # Register as tool
#         tool_obj = Tool(
#             name=tool_name,
#             func=sync_wrapper,
#             description=tool_desc
#         )
#         agent_instance.tools.register(tool_obj)


def create_tool_schema(tool: Tool) -> dict[str, Any]:
    """
    Create a JSON schema for a tool (for LLM function calling).
    
    Returns OpenAI-style function schema.
    """
    # If user provided an explicit parameters schema via decorator, honor it directly
    if getattr(tool, "parameters_schema", None):
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters_schema,
        }

    schema = {
        "name": tool.name,
        "description": tool.description,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }

    # Try to extract parameters from input_model or function signature
    if tool.input_model and BaseModel and issubclass(tool.input_model, BaseModel):
        # Use Pydantic schema
        model_schema = tool.input_model.model_json_schema()
        schema["parameters"]["properties"] = model_schema.get("properties", {})
        schema["parameters"]["required"] = model_schema.get("required", [])
    else:
        # Fallback: extract from function signature
        sig = inspect.signature(tool.func)
        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls"]:
                continue

            param_schema = {"type": "string"}  # Default type

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_schema["type"] = "integer"
                elif param.annotation == float:
                    param_schema["type"] = "number"
                elif param.annotation == bool:
                    param_schema["type"] = "boolean"
                elif param.annotation == list:
                    param_schema["type"] = "array"
                elif param.annotation == dict:
                    param_schema["type"] = "object"

            schema["parameters"]["properties"][param_name] = param_schema

            if param.default == inspect.Parameter.empty:
                schema["parameters"]["required"].append(param_name)

    return schema
