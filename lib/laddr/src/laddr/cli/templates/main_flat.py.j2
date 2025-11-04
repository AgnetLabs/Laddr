#!/usr/bin/env python
"""
Laddr Main Entry Point
========================

Automatically detects and runs agents in your project:
- Coordinator mode: If 'coordinator' agent exists, it orchestrates all others
- Sequential mode: Chains agents in sequence (researcher → analyst → writer)
- Single agent: Runs one agent in isolation

Configuration is loaded from environment variables (see .env file).
All infrastructure backends (database, queue, storage) are configurable via env vars.

For storage backend options (MinIO, AWS S3, etc.), see STORAGE_MIGRATION_GUIDE.md

Usage:
    python main.py run '{"query": "your input"}'
    python main.py replay <job_id>
    AGENT_NAME=researcher python main.py run '{"query": "..."}'  # Run specific agent
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from laddr import AgentRunner, LaddrConfig


def _detect_workflow_mode() -> tuple[str, list[str]]:
    """
    Auto-detect workflow mode based on agents present.
    
    Returns:
        (mode, agent_names) where mode is 'coordinator' or 'sequential'
    """
    agents_dir = Path("agents")
    if not agents_dir.exists():
        return ("sequential", [])
    
    agent_files = [f.stem for f in agents_dir.glob("*.py") if f.stem != "__init__"]
    
    # If coordinator exists, use coordinator mode
    if "coordinator" in agent_files:
        return ("coordinator", agent_files)
    
    # Otherwise sequential mode
    return ("sequential", agent_files)


def run() -> None:
    """
    Run agents with automatic workflow detection.
    
    - If coordinator exists: route to coordinator, it delegates to workers
    - If no coordinator: run sequential chain through all agents
    - If single agent: run that agent in isolation
    """
    inputs: Dict[str, Any] = {}
    if len(sys.argv) > 2:
        try:
            inputs = json.loads(sys.argv[2])
        except Exception:
            inputs = {}
    
    # Allow runtime control of execution limits via environment variables or inputs
    if "max_iterations" not in inputs and os.getenv("MAX_ITERATIONS"):
        try:
            inputs["max_iterations"] = int(os.getenv("MAX_ITERATIONS"))
        except ValueError:
            pass
    
    if "max_tool_calls" not in inputs and os.getenv("MAX_TOOL_CALLS"):
        try:
            inputs["max_tool_calls"] = int(os.getenv("MAX_TOOL_CALLS"))
        except ValueError:
            pass
    
    mode, agent_names = _detect_workflow_mode()
    runner = AgentRunner(env_config=LaddrConfig())
    
    # Allow override via AGENT_NAME env var (for isolated agent runs)
    target_agent = os.getenv("AGENT_NAME")
    
    if target_agent:
        # Direct agent execution (worker mode or manual override)
        result = asyncio.run(runner.run(inputs, agent_name=target_agent))
    elif mode == "coordinator" and "coordinator" in agent_names:
        # Coordinator orchestrates
        result = asyncio.run(runner.run(inputs, agent_name="coordinator"))
    elif len(agent_names) > 1:
        # Sequential chain through all agents
        result = asyncio.run(_run_sequential_chain(runner, agent_names, inputs))
    elif len(agent_names) == 1:
        # Single agent isolation
        result = asyncio.run(runner.run(inputs, agent_name=agent_names[0]))
    else:
        result = {"status": "error", "error": "No agents found in agents/ directory"}
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


async def _run_sequential_chain(runner: AgentRunner, agent_names: list[str], inputs: dict) -> dict:
    """
    Run agents sequentially, piping output from one to the next.
    
    All agents share the same job_id for unified tracing in the dashboard.
    
    Args:
        runner: AgentRunner instance
        agent_names: List of agent names in execution order
        inputs: Initial inputs
    
    Returns:
        Final result dict
    """
    import uuid
    
    # Generate shared job_id for all agents in the chain
    job_id = str(uuid.uuid4())
    current_input = inputs
    last_result = None
    
    for agent_name in agent_names:
        try:
            # All agents use the same job_id for unified tracing
            result = await runner.run(current_input, agent_name=agent_name, job_id=job_id)
            
            if result.get("status") == "error":
                return result
            
            # Extract result for next agent
            last_result = result.get("result", result)
            
            # Next agent receives previous output as 'input' key
            if isinstance(last_result, dict):
                current_input = last_result
            else:
                current_input = {"input": last_result}
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Sequential chain failed at {agent_name}: {e}",
                "agent": agent_name,
                "job_id": job_id
            }
    
    return {
        "status": "success",
        "result": last_result,
        "mode": "sequential",
        "agents": agent_names,
        "job_id": job_id
    }


def replay() -> None:
    if len(sys.argv) < 3:
        print("Usage: python main.py replay <job_id>")
        sys.exit(1)
    runner = AgentRunner(env_config=LaddrConfig())
    result = runner.replay(sys.argv[2], reexecute=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        run()
    elif cmd == "replay":
        replay()
    else:
        print(f"Unknown command: {cmd}")
