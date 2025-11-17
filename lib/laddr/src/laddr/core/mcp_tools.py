"""
MCP Tool Provider for integrating MCP servers with Laddr agents.

Provides MCPToolProvider for single server and MultiMCPToolProvider for multiple servers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .mcp_client import (
    HttpMCPTransport,
    MCPClient,
    MCPError,
    SSEMCPTransport,
    StdioMCPTransport,
)

logger = logging.getLogger(__name__)


class MCPToolProvider:
    """
    Provider for tools from a single MCP server.
    
    Automatically discovers and registers tools from an MCP server into Laddr's ToolRegistry.
    """
    
    def __init__(
        self,
        command: Optional[str] = None,
        url: Optional[str] = None,
        transport: str = "stdio",
        auto_refresh: bool = False,
        api_key: Optional[str] = None,
        server_name: Optional[str] = None,
    ):
        """
        Initialize MCP tool provider.
        
        Args:
            command: Command string for stdio transport (e.g., "npx -y @modelcontextprotocol/server-filesystem /path")
            url: URL for streamable-http or SSE transport
            transport: Transport type ("stdio", "streamable-http", "sse")
            auto_refresh: If True, reconnect and refresh tools on each agent run
            api_key: Optional API key for authenticated servers
            server_name: Optional identifier for this MCP server (used for tool name prefixing)
        """
        if not command and not url:
            raise ValueError("Either 'command' (for stdio) or 'url' (for http/sse) must be provided")
        
        self.command = command
        self.url = url
        self.transport_type = transport
        self.auto_refresh = auto_refresh
        self.api_key = api_key
        self.server_name = server_name or self._infer_server_name()
        
        self._client: Optional[MCPClient] = None
        self._tools_cache: List[Dict[str, Any]] = []
        self._connected = False
    
    def _infer_server_name(self) -> str:
        """Infer server name from command or URL."""
        if self.command:
            # Extract server name from command (e.g., "server-filesystem" from "npx -y @modelcontextprotocol/server-filesystem")
            parts = self.command.split()
            for part in parts:
                if "server-" in part:
                    return part.split("server-")[-1].split("/")[-1]
            return "stdio"
        elif self.url:
            # Extract from URL domain or path
            if "/" in self.url:
                parts = self.url.split("/")
                return parts[-1] if parts[-1] else parts[-2]
            return "http"
        return "mcp"
    
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        if self._connected and not self.auto_refresh:
            return
        
        try:
            # Create transport based on type
            if self.transport_type == "stdio":
                if not self.command:
                    raise ValueError("command required for stdio transport")
                logger.debug(f"Creating stdio transport with command: {self.command}")
                transport = StdioMCPTransport(self.command)
            elif self.transport_type in ("streamable-http", "http"):
                if not self.url:
                    raise ValueError("url required for http transport")
                transport = HttpMCPTransport(self.url, self.api_key)
            elif self.transport_type == "sse":
                if not self.url:
                    raise ValueError("url required for SSE transport")
                transport = SSEMCPTransport(self.url, self.api_key)
            else:
                raise ValueError(f"Unknown transport type: {self.transport_type}")
            
            # Create and connect client
            logger.debug(f"Creating MCP client for server '{self.server_name}'")
            self._client = MCPClient(transport)
            await self._client.connect()
            
            # Discover tools
            logger.debug(f"Discovering tools from MCP server '{self.server_name}'")
            self._tools_cache = await self._client.list_tools()
            self._connected = True
            
            tool_names = [t.get("name", "unknown") for t in self._tools_cache]
            logger.info(f"Connected to MCP server '{self.server_name}' with {len(self._tools_cache)} tools: {tool_names}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.server_name}': {e}", exc_info=True)
            raise
    
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting from MCP server '{self.server_name}': {e}")
            finally:
                self._client = None
                self._connected = False
                self._tools_cache = []
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self._connected and self._client is not None
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Fetch and return list of available tools from server."""
        if not self._connected:
            await self.connect()
        
        if self.auto_refresh:
            # Refresh tools cache
            self._tools_cache = await self._client.list_tools()
        
        return self._tools_cache.copy()
    
    async def register_tools(self, registry: Any) -> None:
        """
        Register discovered tools into a ToolRegistry.
        
        Args:
            registry: ToolRegistry instance to register tools into
        """
        if not self._connected:
            logger.info(f"Connecting to MCP server '{self.server_name}' for tool registration...")
            await self.connect()
        
        tools = await self.discover_tools()
        
        if not tools:
            logger.warning(f"No tools discovered from MCP server '{self.server_name}'")
            return
        
        logger.info(f"Registering {len(tools)} tools from MCP server '{self.server_name}'")
        
        # Track registered tools to avoid duplicates
        registered_names = set()
        failed_registrations = []
        
        for tool_def in tools:
            tool_name = tool_def.get("name")
            if not tool_name:
                logger.warning(f"Skipping tool with no name: {tool_def}")
                continue
            
            # Prefix tool name with server name if needed to avoid collisions
            prefixed_name = f"{self.server_name}_{tool_name}" if self.server_name else tool_name
            
            # Skip if already registered
            if prefixed_name in registered_names:
                logger.debug(f"Tool {prefixed_name} already in registration batch, skipping")
                continue
            
            if registry.has(prefixed_name):
                logger.debug(f"Tool {prefixed_name} already registered in registry, skipping")
                continue
            
            # Create tool wrapper
            try:
                tool_wrapper = self._create_tool_wrapper(tool_name, tool_def, prefixed_name)
            except Exception as e:
                logger.error(f"Failed to create wrapper for MCP tool {tool_name}: {e}", exc_info=True)
                failed_registrations.append(tool_name)
                continue
            
            # Register tool
            try:
                registry.register(tool_wrapper, name=prefixed_name)
                registered_names.add(prefixed_name)
                logger.info(f"✓ Registered MCP tool: {prefixed_name} (original: {tool_name})")
            except Exception as e:
                logger.error(f"Failed to register MCP tool {prefixed_name}: {e}", exc_info=True)
                failed_registrations.append(tool_name)
        
        if failed_registrations:
            logger.warning(f"Failed to register {len(failed_registrations)} tools: {failed_registrations}")
        
        logger.info(f"Successfully registered {len(registered_names)}/{len(tools)} tools from MCP server '{self.server_name}'")
    
    def _create_tool_wrapper(self, original_name: str, tool_def: Dict[str, Any], prefixed_name: str) -> Any:
        """Create a callable wrapper for an MCP tool."""
        from .tooling import Tool
        
        description = tool_def.get("description", "")
        input_schema = tool_def.get("inputSchema", {})
        
        async def mcp_tool_func(**kwargs: Any) -> Any:
            """Async wrapper for MCP tool invocation."""
            if not self._connected:
                await self.connect()
            
            try:
                result = await self._client.call_tool(original_name, kwargs)
                # MCP tools/call returns: {"content": [{"type": "text", "text": "..."}]}
                if isinstance(result, dict):
                    # Check for content array (MCP standard format)
                    if "content" in result:
                        content = result["content"]
                        if isinstance(content, list) and len(content) > 0:
                            # Extract text from first content item
                            first_item = content[0]
                            if isinstance(first_item, dict):
                                # Return text if available, otherwise return the item
                                return first_item.get("text", first_item)
                        return content
                    # If no content field, return result as-is
                    return result
                return result
            except Exception as e:
                logger.error(f"Error calling MCP tool {original_name}: {e}")
                raise
        
        # Create wrapper that handles both sync and async contexts
        async def async_wrapper(**kwargs: Any) -> Any:
            """Async wrapper for MCP tool invocation."""
            return await mcp_tool_func(**kwargs)
        
        def sync_wrapper(**kwargs: Any) -> Any:
            """Sync wrapper that runs async function."""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, return coroutine
                    return mcp_tool_func(**kwargs)
                else:
                    # If no loop running, run synchronously
                    return loop.run_until_complete(mcp_tool_func(**kwargs))
            except RuntimeError:
                # No event loop, create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(mcp_tool_func(**kwargs))
                finally:
                    loop.close()
        
        sync_wrapper.__name__ = prefixed_name
        sync_wrapper.__doc__ = description
        
        # Create Tool instance - use async_wrapper as the func since Agent.call_tool handles async
        # The async_wrapper will be called by Tool.invoke(), and Agent.call_tool() will await the result
        tool_obj = Tool(
            name=prefixed_name,
            func=async_wrapper,  # Use async wrapper - Agent will await it
            description=description,
            parameters_schema=input_schema,
        )
        
        # Log tool creation for debugging
        if isinstance(input_schema, dict):
            schema_type = input_schema.get("type", "unknown")
            properties_count = len(input_schema.get("properties", {}))
            required_count = len(input_schema.get("required", []))
            logger.info(f"Created MCP tool wrapper: {prefixed_name} (original: {original_name}, schema: type={schema_type}, properties={properties_count}, required={required_count})")
        else:
            logger.warning(f"Created MCP tool wrapper: {prefixed_name} (original: {original_name}) with invalid schema: {type(input_schema)}")
        
        return tool_obj
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class MultiMCPToolProvider:
    """
    Provider for tools from multiple MCP servers.
    
    Aggregates tools from multiple MCPToolProvider instances.
    """
    
    def __init__(self, providers: List[MCPToolProvider | Dict[str, Any]]):
        """
        Initialize multi-MCP tool provider.
        
        Args:
            providers: List of MCPToolProvider instances or configuration dicts
        """
        self._providers: List[MCPToolProvider] = []
        
        # Convert dict configs to MCPToolProvider instances
        for provider in providers:
            if isinstance(provider, dict):
                self._providers.append(MCPToolProvider(**provider))
            elif isinstance(provider, MCPToolProvider):
                self._providers.append(provider)
            else:
                raise ValueError(f"Invalid provider type: {type(provider)}")
    
    async def connect(self) -> None:
        """Connect to all MCP servers."""
        results = await asyncio.gather(
            *[provider.connect() for provider in self._providers],
            return_exceptions=True
        )
        
        # Log any connection failures but don't fail completely
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to connect to MCP server {i}: {result}")
    
    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        await asyncio.gather(
            *[provider.disconnect() for provider in self._providers],
            return_exceptions=True
        )
    
    async def register_tools(self, registry: Any) -> None:
        """
        Register tools from all servers into a ToolRegistry.
        
        Args:
            registry: ToolRegistry instance to register tools into
        """
        # Register tools from all providers
        await asyncio.gather(
            *[provider.register_tools(registry) for provider in self._providers],
            return_exceptions=True
        )
    
    def get_providers(self) -> List[MCPToolProvider]:
        """Return list of managed MCPToolProvider instances."""
        return self._providers.copy()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

