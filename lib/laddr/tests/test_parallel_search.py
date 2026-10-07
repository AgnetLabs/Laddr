"""Exercise the example through the real registry and HTTP transport."""
import importlib.util
from pathlib import Path

import pytest
from aiohttp import web

from laddr import MCPToolProvider
from laddr.core.mcp_client import HttpMCPTransport, MCPTransportError


spec = importlib.util.spec_from_file_location(
    "parallel_search", Path(__file__).resolve().parents[3] / "examples/parallel_search.py"
)
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


@pytest.mark.asyncio
async def test_native_example_caller_and_headers(monkeypatch):
    observed = []

    async def handler(request):
        message = await request.json()
        observed.append((dict(request.headers), message))
        method = message["method"]
        if method == "initialize":
            result = {"serverInfo": {}, "capabilities": {}}
        elif method == "tools/list":
            assert request.headers["Mcp-Session-Id"] == "local-session"
            result = {"tools": [
                {"name": "web_search", "inputSchema": {"type": "object", "properties": {
                    "objective": {"type": "string"}, "search_queries": {"type": "array"},
                    "session_id": {"type": "string"}}, "required": ["objective", "search_queries"]}},
                {"name": "web_fetch", "inputSchema": {"type": "object", "properties": {
                    "objective": {"type": "string"}, "urls": {"type": "array"},
                    "session_id": {"type": "string"}}, "required": ["objective", "urls"]}},
            ]}
        else:
            assert method == "tools/call"
            result = {"content": [{"type": "text", "text": "TaskGroup waits for tasks; https://docs.python.org/"}]}
        return web.json_response({"jsonrpc": "2.0", "id": message["id"], "result": result},
                                 headers={"Mcp-Session-Id": "local-session"})

    app = web.Application()
    app.router.add_post("/mcp", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    original = example.create_agent
    agents = []

    def local_agent(**kwargs):
        agent = original(**kwargs)
        agent._mcp_providers[0].url = f"http://127.0.0.1:{port}/mcp"
        agents.append(agent)
        return agent

    monkeypatch.setattr(example, "create_agent", local_agent)
    monkeypatch.setenv("PARALLEL_API_KEY", "ignored")
    try:
        result = await example.research("TaskGroup behavior", "Python TaskGroup", "https://docs.python.org/")
        assert "TaskGroup" in result["search"] and "https://docs.python.org/" in result["source"]
        calls = [m["params"] for _, m in observed if m["method"] == "tools/call"]
        assert [p["name"] for p in calls] == ["web_search", "web_fetch"]
        assert calls[0]["arguments"]["session_id"] == calls[1]["arguments"]["session_id"]
        assert all(h["User-Agent"] == "laddr/0.9.6" and "Authorization" not in h for h, _ in observed)
        assert all(h["Accept"] == "application/json, text/event-stream" for h, _ in observed)
        assert not agents[0]._mcp_providers[0].is_connected()
    finally:
        await runner.cleanup()


def test_opt_in_configuration_preserves_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("QUEUE_BACKEND=redis\nLLM_BACKEND=openai\n")
    monkeypatch.setenv("LLM_BACKEND_PARALLEL_SEARCH", "openai")
    agent = example.create_agent()
    provider = agent._mcp_providers[0]
    assert provider.api_key is None and provider.trust_env is False
    assert agent.env_config.queue_backend == "memory"
    assert agent.env_config.database_url == "sqlite:///:memory:"
    assert agent.llm.__class__.__name__ == "NoOpLLM"
    assert not agent.tools.has("parallel_web_search")  # Lazy discovery
    assert MCPToolProvider(url="https://example.org/mcp").trust_env is False
    assert HttpMCPTransport("https://example.org/mcp").trust_env is False


@pytest.mark.asyncio
async def test_http_auth_error_and_disconnect():
    requests = []

    async def reject(request):
        requests.append(dict(request.headers))
        return web.Response(status=401)

    app = web.Application()
    app.router.add_post("/mcp", reject)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    transport = HttpMCPTransport(f"http://127.0.0.1:{port}/mcp", api_key="local-test")
    try:
        await transport.connect()
        with pytest.raises(MCPTransportError, match="401"):
            await transport.request({"jsonrpc": "2.0", "id": "1", "method": "tools/list"})
        assert requests[0]["Authorization"] == "Bearer local-test"
    finally:
        await transport.disconnect()
        await runner.cleanup()
    assert transport._session is None and transport._session_id is None
