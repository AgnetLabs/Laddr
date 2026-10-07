"""Search and read a source through Laddr's native agent tool path."""

import argparse
import asyncio
import json
from uuid import uuid4

from laddr import AgentConfig, CoreAgent, LaddrConfig, MCPToolProvider
from laddr.core.llm import NoOpLLM


def create_agent(*, trust_env: bool = False) -> CoreAgent:
    """Build an isolated local example without a search key or LLM service."""
    provider = MCPToolProvider(
        url="https://search.parallel.ai/mcp",
        transport="streamable-http",
        server_name="parallel",
        trust_env=trust_env,
    )
    config = LaddrConfig(
        _env_file=None,
        queue_backend="memory",
        db_backend="sqlite",
        database_url="sqlite:///:memory:",
        llm_backend="noop",
        cache_backend="inmemory",
        storage_endpoint="",
        enable_tracing=False,
        enable_metrics=False,
        langfuse_enabled=False,
        enable_large_response_storage=False,
    )
    return CoreAgent(
        AgentConfig(name="parallel_search", role="researcher", goal="Read web sources"),
        config,
        tools=[provider],
        llm=NoOpLLM(),
    )


async def research(
    objective: str, query: str, url: str, *, trust_env: bool = False
) -> dict:
    """Execute explicit search/fetch calls, rather than an autonomous LLM loop."""
    agent = create_agent(trust_env=trust_env)
    session_id = uuid4().hex
    try:
        search = await agent.call_tool(
            "parallel_web_search",
            {
                "objective": objective,
                "search_queries": [query],
                "session_id": session_id,
            },
            use_cache=False,
        )
        source = await agent.call_tool(
            "parallel_web_fetch",
            {"objective": objective, "urls": [url], "session_id": session_id},
            use_cache=False,
        )
        return {"search": search, "source": source}
    finally:
        await agent.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--objective",
        default="Explain how Python TaskGroup waits for tasks and handles failures.",
    )
    parser.add_argument(
        "--query", default="Python asyncio TaskGroup exception handling"
    )
    parser.add_argument(
        "--url", default="https://docs.python.org/3/library/asyncio-task.html"
    )
    parser.add_argument(
        "--trust-env",
        action="store_true",
        help="Use environment HTTP(S) proxy settings for MCP requests.",
    )
    args = parser.parse_args()
    result = asyncio.run(
        research(args.objective, args.query, args.url, trust_env=args.trust_env)
    )
    print(json.dumps(result, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
