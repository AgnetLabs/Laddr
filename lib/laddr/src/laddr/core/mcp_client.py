"""
MCP (Model Context Protocol) Client for federated tool ecosystems.

Implements JSON-RPC 2.0 based MCP protocol with support for multiple transports:
- stdio: Command-based local servers
- streamable-http: HTTP-based remote servers
- sse: Server-Sent Events based servers
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    pass


class MCPTransportError(MCPError):
    """Transport layer error."""
    pass


class MCPProtocolError(MCPError):
    """MCP protocol error."""
    pass


class MCPTransport(ABC):
    """Abstract base class for MCP transport implementations."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass
    
    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        """Send a JSON-RPC message to the server."""
        pass
    
    @abstractmethod
    async def receive(self) -> Dict[str, Any]:
        """Receive a JSON-RPC message from the server."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        pass


class StdioMCPTransport(MCPTransport):
    """Stdio transport for command-based local MCP servers."""
    
    def __init__(self, command: str):
        """
        Initialize stdio transport.
        
        Args:
            command: Command string to execute (e.g., "npx -y @modelcontextprotocol/server-filesystem /path")
        """
        self.command = command
        self.process: Optional[subprocess.Popen] = None
        self._async_process: Optional[asyncio.subprocess.Process] = None
        self._connected = False
        self._use_async = True  # Use asyncio subprocess for better I/O handling
    
    async def connect(self) -> None:
        """Start the subprocess and establish connection."""
        if self._connected:
            return
        
        try:
            # Split command into parts
            cmd_parts = self.command.split()
            # Inherit environment variables (important for MCP servers that need API keys)
            env = os.environ.copy()
            
            # Log environment variables that MCP servers typically need (for debugging)
            mcp_env_vars = ['SERVICE_ACCOUNT_PATH', 'GOOGLE_APPLICATION_CREDENTIALS', 
                          'DRIVE_FOLDER_ID', 'CREDENTIALS_CONFIG', 'CREDENTIALS_PATH']
            env_info = {k: 'SET' if env.get(k) else 'NOT SET' for k in mcp_env_vars}
            logger.debug(f"MCP server environment: {env_info}")
            
            # Use asyncio subprocess for better async I/O handling
            try:
                self._async_process = await asyncio.create_subprocess_exec(
                    *cmd_parts,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    text=True
                )
                
                # Give the process a moment to start
                await asyncio.sleep(0.2)
                
                # Check if process exited immediately
                if self._async_process.returncode is not None:
                    # Process exited - read stderr
                    stderr_output = ""
                    if self._async_process.stderr:
                        try:
                            stderr_data = await asyncio.wait_for(
                                self._async_process.stderr.read(), timeout=0.5
                            )
                            stderr_output = stderr_data
                        except Exception:
                            pass
                    
                    exit_code = self._async_process.returncode
                    error_msg = (
                        f"MCP server process exited immediately with code {exit_code}. "
                        f"Command: {self.command}. "
                        f"Error output: {stderr_output[:1000] if stderr_output else 'No error output'}"
                    )
                    logger.error(f"MCP server startup failed: {error_msg}")
                    raise MCPTransportError(error_msg)
                
                self._connected = True
                logger.info(f"Connected to MCP server via stdio: {self.command}")
            except Exception as e:
                # Fallback to synchronous subprocess if async fails
                logger.debug(f"Async subprocess failed, using sync: {e}")
                self.process = subprocess.Popen(
                    cmd_parts,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=0,
                    env=env
                )
                self._use_async = False
                
                await asyncio.sleep(0.2)
                if self.process.poll() is not None:
                    stderr_output = ""
                    if self.process.stderr:
                        try:
                            stderr_output = self.process.stderr.read()
                        except Exception:
                            pass
                    raise MCPTransportError(
                        f"MCP server process exited immediately with code {self.process.returncode}. "
                        f"Command: {self.command}. "
                        f"Error: {stderr_output[:1000] if stderr_output else 'No error output'}"
                    )
                self._connected = True
                logger.info(f"Connected to MCP server via stdio (sync): {self.command}")
        except MCPTransportError:
            raise
        except Exception as e:
            raise MCPTransportError(f"Failed to start MCP server process: {e}")
    
    async def disconnect(self) -> None:
        """Terminate the subprocess."""
        if self._use_async and self._async_process:
            try:
                if self._async_process.returncode is None:
                    self._async_process.terminate()
                    try:
                        await asyncio.wait_for(self._async_process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        self._async_process.kill()
                        await self._async_process.wait()
            except Exception as e:
                logger.warning(f"Error disconnecting async stdio transport: {e}")
            finally:
                self._async_process = None
                self._connected = False
        elif self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.warning(f"Error disconnecting stdio transport: {e}")
            finally:
                self.process = None
                self._connected = False
    
    async def send(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message via stdin."""
        if not self._connected:
            raise MCPTransportError("Not connected to MCP server")
        
        try:
            json_str = json.dumps(message) + "\n"
            if self._use_async and self._async_process and self._async_process.stdin:
                self._async_process.stdin.write(json_str)
                await self._async_process.stdin.drain()
            elif self.process and self.process.stdin:
                self.process.stdin.write(json_str)
                self.process.stdin.flush()
            else:
                raise MCPTransportError("No process or stdin available")
        except Exception as e:
            raise MCPTransportError(f"Failed to send message: {e}")
    
    async def receive(self) -> Dict[str, Any]:
        """Receive JSON-RPC message from stdout."""
        if not self._connected:
            raise MCPTransportError("Not connected to MCP server")
        
        try:
            # Use async subprocess if available
            if self._use_async and self._async_process:
                # Check if process exited
                if self._async_process.returncode is not None:
                    stderr_output = ""
                    if self._async_process.stderr:
                        try:
                            stderr_data = await asyncio.wait_for(
                                self._async_process.stderr.read(), timeout=0.5
                            )
                            stderr_output = stderr_data
                        except Exception:
                            pass
                    raise MCPTransportError(
                        f"Connection closed by server. Exit code: {self._async_process.returncode}. "
                        f"Command: {self.command}. "
                        f"Error: {stderr_output[:1000] if stderr_output else 'No error output'}"
                    )
                
                # Read line from stdout with timeout
                if not self._async_process.stdout:
                    raise MCPTransportError("No stdout available")
                
                try:
                    line = await asyncio.wait_for(
                        self._async_process.stdout.readline(), timeout=10.0
                    )
                except asyncio.TimeoutError:
                    raise MCPTransportError("Timeout waiting for MCP server response")
                
                if not line:
                    # Check if process exited
                    if self._async_process.returncode is not None:
                        raise MCPTransportError(
                            f"Connection closed by server. Exit code: {self._async_process.returncode}"
                        )
                    raise MCPTransportError("Connection closed by server - no data received")
                
                line = line.strip()
                if not line:
                    # Empty line, try reading again
                    return await self.receive()
                
                return json.loads(line)
            
            # Fallback to sync subprocess
            if not self.process:
                raise MCPTransportError("No process available")
            
            # Check if process has exited
            if self.process.poll() is not None:
                stderr_output = ""
                if self.process.stderr:
                    try:
                        stderr_output = self.process.stderr.read()
                    except Exception:
                        pass
                raise MCPTransportError(
                    f"Connection closed by server. Exit code: {self.process.returncode}. "
                    f"Error: {stderr_output[:1000] if stderr_output else 'No error output'}"
                )
            
            # Read line from stdout
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None:
                    raise MCPTransportError(
                        f"Connection closed by server. Exit code: {self.process.returncode}"
                    )
                raise MCPTransportError("Connection closed by server - no data received")
            
            line = line.strip()
            if not line:
                return await self.receive()
            
            return json.loads(line)
        except json.JSONDecodeError as e:
            raise MCPProtocolError(f"Invalid JSON response: {e}")
        except MCPTransportError:
            raise
        except Exception as e:
            raise MCPTransportError(f"Failed to receive message: {e}")
    
    def is_connected(self) -> bool:
        """Check if process is running and connected."""
        if self._use_async and self._async_process:
            return self._async_process.returncode is None and self._connected
        elif self.process:
            return self.process.poll() is None and self._connected
        return False


class HttpMCPTransport(MCPTransport):
    """HTTP transport for streamable-http MCP servers."""
    
    def __init__(self, url: str, api_key: Optional[str] = None):
        """
        Initialize HTTP transport.
        
        Args:
            url: Server URL (e.g., "https://docs.agno.com/mcp")
            api_key: Optional API key for authentication
        """
        self.url = url.rstrip('/')
        self.api_key = api_key
        self._connected = False
        self._session: Optional[Any] = None
    
    async def connect(self) -> None:
        """Establish HTTP connection."""
        if self._connected:
            return
        
        try:
            # Try aiohttp first, fallback to httpx
            try:
                import aiohttp  # type: ignore
                self._session = aiohttp.ClientSession()
                self._is_aiohttp = True
            except ImportError:
                try:
                    import httpx  # type: ignore
                    self._session = httpx.AsyncClient()
                    self._is_aiohttp = False
                except ImportError:
                    raise MCPTransportError("aiohttp or httpx required for HTTP transport. Install with: pip install aiohttp")
            
            self._connected = True
            logger.info(f"Connected to MCP server via HTTP: {self.url}")
        except Exception as e:
            raise MCPTransportError(f"Failed to connect to HTTP MCP server: {e}")
    
    async def disconnect(self) -> None:
        """Close HTTP connection."""
        if self._session:
            try:
                if hasattr(self._session, 'close'):
                    await self._session.close()
            except Exception as e:
                logger.warning(f"Error disconnecting HTTP transport: {e}")
            finally:
                self._session = None
                self._connected = False
    
    async def send(self, message: Dict[str, Any]) -> None:
        """HTTP transport doesn't use send - messages are sent via POST requests."""
        # HTTP transport uses request/response pattern, not persistent connection
        pass
    
    async def receive(self) -> Dict[str, Any]:
        """HTTP transport doesn't use receive - responses come from POST requests."""
        # HTTP transport uses request/response pattern
        raise NotImplementedError("HTTP transport uses request() method instead")
    
    async def request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send request and receive response via HTTP POST."""
        if not self._connected or not self._session:
            raise MCPTransportError("Not connected to MCP server")
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            if getattr(self, '_is_aiohttp', True):
                # aiohttp
                async with self._session.post(self.url, json=message, headers=headers) as resp:  # type: ignore
                    resp.raise_for_status()
                    return await resp.json()
            else:
                # httpx
                resp = await self._session.post(self.url, json=message, headers=headers)  # type: ignore
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            raise MCPTransportError(f"HTTP request failed: {e}")
    
    def is_connected(self) -> bool:
        """Check if HTTP session is active."""
        return self._connected and self._session is not None


class SSEMCPTransport(MCPTransport):
    """SSE (Server-Sent Events) transport for MCP servers."""
    
    def __init__(self, url: str, api_key: Optional[str] = None):
        """
        Initialize SSE transport.
        
        Args:
            url: Server URL
            api_key: Optional API key for authentication
        """
        self.url = url.rstrip('/')
        self.api_key = api_key
        self._connected = False
        self._session: Optional[Any] = None
        self._event_source: Optional[Any] = None
        self._is_aiohttp = True
    
    async def connect(self) -> None:
        """Establish SSE connection."""
        if self._connected:
            return
        
        try:
            import aiohttp  # type: ignore
            self._session = aiohttp.ClientSession()
            self._is_aiohttp = True
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # SSE endpoint is typically /sse or /events
            sse_url = f"{self.url}/sse" if not self.url.endswith('/sse') else self.url
            self._event_source = await self._session.get(sse_url, headers=headers)  # type: ignore
            self._connected = True
            logger.info(f"Connected to MCP server via SSE: {self.url}")
        except ImportError:
            raise MCPTransportError("aiohttp required for SSE transport. Install with: pip install aiohttp")
        except Exception as e:
            raise MCPTransportError(f"Failed to connect to SSE MCP server: {e}")
    
    async def disconnect(self) -> None:
        """Close SSE connection."""
        if self._event_source:
            try:
                self._event_source.close()
            except Exception:
                pass
            self._event_source = None
        
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.warning(f"Error disconnecting SSE transport: {e}")
            finally:
                self._session = None
                self._connected = False
    
    async def send(self, message: Dict[str, Any]) -> None:
        """Send message via HTTP POST (SSE is one-way for events, use POST for requests)."""
        if not self._connected or not self._session:
            raise MCPTransportError("Not connected to MCP server")
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with self._session.post(self.url, json=message, headers=headers) as resp:  # type: ignore
                resp.raise_for_status()
        except Exception as e:
            raise MCPTransportError(f"SSE send failed: {e}")
    
    async def receive(self) -> Dict[str, Any]:
        """Receive event from SSE stream."""
        if not self._connected or not self._event_source:
            raise MCPTransportError("Not connected to MCP server")
        
        try:
            # Read SSE event
            async for line in self._event_source.content:  # type: ignore
                line_str = line.decode('utf-8').strip()
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    return json.loads(data_str)
        except Exception as e:
            raise MCPTransportError(f"SSE receive failed: {e}")
    
    async def request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send request and receive response via HTTP POST."""
        if not self._connected or not self._session:
            raise MCPTransportError("Not connected to MCP server")
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with self._session.post(self.url, json=message, headers=headers) as resp:  # type: ignore
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            raise MCPTransportError(f"SSE request failed: {e}")
    
    def is_connected(self) -> bool:
        """Check if SSE connection is active."""
        return self._connected and self._session is not None and self._event_source is not None


class MCPClient:
    """MCP client for communicating with MCP servers."""
    
    def __init__(self, transport: MCPTransport):
        """
        Initialize MCP client.
        
        Args:
            transport: MCP transport instance
        """
        self.transport = transport
        self._initialized = False
        self._capabilities: Dict[str, Any] = {}
        self._server_info: Dict[str, Any] = {}
        self._request_id = 0
        self._pending_requests: Dict[str, asyncio.Future] = {}
    
    async def connect(self) -> None:
        """Connect to MCP server and initialize protocol."""
        if self.transport.is_connected():
            return
        
        await self.transport.connect()
        await self._initialize()
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        
        await self.transport.disconnect()
        self._initialized = False
    
    async def _initialize(self) -> None:
        """Initialize MCP protocol handshake."""
        if self._initialized:
            return
        
        # Send initialize request
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "laddr",
                    "version": "0.8.2"
                }
            }
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise MCPProtocolError(f"Initialize failed: {response['error']}")
        
        self._server_info = response.get("result", {}).get("serverInfo", {})
        self._capabilities = response.get("result", {}).get("capabilities", {})
        self._initialized = True
        
        # Send initialized notification
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_notification(notification)
    
    def _next_request_id(self) -> str:
        """Generate next request ID."""
        self._request_id += 1
        return str(self._request_id)
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request and wait for response."""
        request_id = request["id"]
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # Send request
            if isinstance(self.transport, HttpMCPTransport) or isinstance(self.transport, SSEMCPTransport):
                # HTTP/SSE use request/response pattern
                response = await self.transport.request(request)
                future.set_result(response)
            else:
                # Stdio uses persistent connection
                await self.transport.send(request)
                # Receive response
                response = await self.transport.receive()
                future.set_result(response)
            
            result = await future
            return result
        except Exception as e:
            future.cancel()
            raise MCPProtocolError(f"Request failed: {e}")
        finally:
            self._pending_requests.pop(request_id, None)
    
    async def _send_notification(self, notification: Dict[str, Any]) -> None:
        """Send JSON-RPC notification (no response expected)."""
        if isinstance(self.transport, HttpMCPTransport) or isinstance(self.transport, SSEMCPTransport):
            # HTTP/SSE: notifications are sent but no response expected
            await self.transport.send(notification)
        else:
            # Stdio: send notification
            await self.transport.send(notification)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        if not self._initialized:
            await self._initialize()
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/list",
            "params": {}
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise MCPProtocolError(f"tools/list failed: {response['error']}")
        
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self._initialized:
            await self._initialize()
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            error = response["error"]
            error_msg = error.get("message", "Unknown error")
            error_code = error.get("code", -1)
            raise MCPProtocolError(f"tools/call failed (code {error_code}): {error_msg}")
        
        result = response.get("result", {})
        # MCP tools/call returns result with content array
        return result
