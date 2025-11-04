"""
Database layer with SQLAlchemy models and high-level API.

Provides Job, Trace, Memory, and AgentRegistry models.
All metrics and traces are stored internally (no external services).
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Job(Base):
    """Job execution record (legacy terminology)."""

    __tablename__ = "jobs"

    job_id = Column(String(36), primary_key=True)
    pipeline_name = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    inputs = Column(JSON, nullable=False)
    outputs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class PromptExecution(Base):
    """Prompt execution record (new terminology for pipeline/job)."""

    __tablename__ = "prompt_executions"

    prompt_id = Column(String(36), primary_key=True)
    prompt_name = Column(String(255), nullable=False)  # Agent/prompt name
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    inputs = Column(JSON, nullable=False)
    outputs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Trace(Base):
    """Trace event for observability with hierarchical span support."""

    __tablename__ = "traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # task_start, task_complete, tool_call, etc.
    parent_id = Column(Integer, nullable=True, index=True)  # For hierarchical traces (span parent)
    payload = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class Memory(Base):
    """Agent memory storage."""

    __tablename__ = "memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(255), nullable=False, index=True)
    job_id = Column(String(36), nullable=True, index=True)  # Optional: job-specific memory
    key = Column(String(255), nullable=False)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentRegistry(Base):
    """Agent registration and metadata."""

    __tablename__ = "agent_registry"

    agent_name = Column(String(255), primary_key=True)
    meta = Column(JSON, nullable=False)  # role, goal, tools, status, host_url, etc.
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseService:
    """
    High-level database API.
    
    Provides methods for job management, tracing, memory, and agent registry.
    Supports both Postgres and SQLite.
    """

    def __init__(self, database_url: str):
        """
        Initialize database service.
        
        Args:
            database_url: SQLAlchemy connection string
                         e.g., "postgresql://user:pass@host:5432/db"
                         or "sqlite:///./laddr.db" for local dev
        """
        # Fallback to SQLite if URL is None or connection fails
        if not database_url:
            logger.warning("DATABASE_URL not set, using local SQLite")
            database_url = "sqlite:///laddr.db"
        
        try:
            self.engine = create_engine(database_url, echo=False)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Connected to database: {database_url.split('@')[-1] if '@' in database_url else database_url}")
        except Exception as e:
            db_type = database_url.split('://')[0] if '://' in database_url else 'unknown'
            logger.warning(f"Failed to connect to {db_type} database: {e}")
            logger.info("Falling back to SQLite database")
            database_url = "sqlite:///laddr.db"
            self.engine = create_engine(database_url, echo=False)
        
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    def create_tables(self):
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Job management

    def create_job(self, job_id: str | None, pipeline: str, inputs: dict) -> str:
        """Create a new job record, or reuse existing if job_id already exists (for sequential chains)."""
        if job_id is None:
            job_id = str(uuid.uuid4())

        with self.get_session() as session:
            # Check if job already exists (for sequential mode where agents share job_id)
            existing_job = session.query(Job).filter_by(job_id=job_id).first()
            if existing_job:
                # Job already exists (e.g., from first agent in sequential chain)
                # Just return the job_id without creating a duplicate
                return job_id
            
            # Create new job
            job = Job(
                job_id=job_id,
                pipeline_name=pipeline,
                status="pending",
                inputs=inputs
            )
            session.add(job)

        return job_id

    def save_result(self, job_id: str, outputs: dict, status: str = "completed") -> None:
        """Save job result."""
        with self.get_session() as session:
            job = session.query(Job).filter_by(job_id=job_id).first()
            if job:
                job.outputs = outputs
                job.status = status
                job.completed_at = datetime.utcnow()

    def get_result(self, job_id: str) -> dict | None:
        """Get job result."""
        with self.get_session() as session:
            job = session.query(Job).filter_by(job_id=job_id).first()
            if not job:
                return None

            def _iso_z(dt: datetime | None) -> str | None:
                if not dt:
                    return None
                # stored as naive UTC; normalize to Z-suffixed ISO for clients
                return dt.isoformat() + "Z"

            return {
                "job_id": job.job_id,
                "pipeline_name": job.pipeline_name,
                "status": job.status,
                "inputs": job.inputs,
                "outputs": job.outputs,
                "created_at": _iso_z(job.created_at),
                "completed_at": _iso_z(job.completed_at),
            }

    def list_jobs(self, limit: int = 50) -> list[dict]:
        """List recent jobs."""
        with self.get_session() as session:
            jobs = session.query(Job).order_by(Job.created_at.desc()).limit(limit).all()

            def _iso_z(dt: datetime | None) -> str | None:
                return dt.isoformat() + "Z" if dt else None

            return [
                {
                    "job_id": job.job_id,
                    "pipeline_name": job.pipeline_name,
                    "status": job.status,
                    "created_at": _iso_z(job.created_at),
                }
                for job in jobs
            ]

    # Prompt execution management (new terminology)

    def create_prompt(self, prompt_id: str | None, prompt_name: str, inputs: dict) -> str:
        """Create a new prompt execution record."""
        if prompt_id is None:
            prompt_id = str(uuid.uuid4())

        with self.get_session() as session:
            prompt = PromptExecution(
                prompt_id=prompt_id,
                prompt_name=prompt_name,
                status="pending",
                inputs=inputs
            )
            session.add(prompt)

        return prompt_id

    def save_prompt_result(self, prompt_id: str, outputs: dict, status: str = "completed") -> None:
        """Save prompt execution result."""
        with self.get_session() as session:
            prompt = session.query(PromptExecution).filter_by(prompt_id=prompt_id).first()
            if prompt:
                prompt.outputs = outputs
                prompt.status = status
                prompt.completed_at = datetime.utcnow()

    def update_prompt_status(self, prompt_id: str, status: str) -> None:
        """Update prompt execution status only; set completed_at for terminal states."""
        terminal = {"completed", "failed", "error", "canceled"}
        with self.get_session() as session:
            prompt = session.query(PromptExecution).filter_by(prompt_id=prompt_id).first()
            if prompt:
                prompt.status = status
                if status in terminal and prompt.completed_at is None:
                    prompt.completed_at = datetime.utcnow()

    def get_prompt_result(self, prompt_id: str) -> dict | None:
        """Get prompt execution result."""
        with self.get_session() as session:
            prompt = session.query(PromptExecution).filter_by(prompt_id=prompt_id).first()
            if not prompt:
                return None

            def _iso_z(dt: datetime | None) -> str | None:
                return dt.isoformat() + "Z" if dt else None

            return {
                "prompt_id": prompt.prompt_id,
                "prompt_name": prompt.prompt_name,
                "status": prompt.status,
                "inputs": prompt.inputs,
                "outputs": prompt.outputs,
                "created_at": _iso_z(prompt.created_at),
                "completed_at": _iso_z(prompt.completed_at),
            }

    def list_prompts(self, limit: int = 50) -> list[dict]:
        """List recent prompt executions."""
        with self.get_session() as session:
            prompts = session.query(PromptExecution).order_by(PromptExecution.created_at.desc()).limit(limit).all()

            def _iso_z(dt: datetime | None) -> str | None:
                return dt.isoformat() + "Z" if dt else None

            return [
                {
                    "prompt_id": prompt.prompt_id,
                    "prompt_name": prompt.prompt_name,
                    "status": prompt.status,
                    "created_at": _iso_z(prompt.created_at),
                }
                for prompt in prompts
            ]

    def get_job_traces(self, job_id: str) -> list[dict]:
        """Get all traces for a job."""
        with self.get_session() as session:
            traces = session.query(Trace).filter_by(job_id=job_id).order_by(Trace.timestamp).all()

            def _iso_z(dt: datetime | None) -> str | None:
                return dt.isoformat() + "Z" if dt else None

            return [
                {
                    "id": trace.id,
                    "job_id": trace.job_id,
                    "agent_name": trace.agent_name,
                    "event_type": trace.event_type,
                    "payload": trace.payload,
                    "timestamp": _iso_z(trace.timestamp),
                }
                for trace in traces
            ]

    # Tracing

    def append_trace(self, job_id: str, agent_name: str, event_type: str, payload: dict) -> None:
        """Append a trace event."""
        with self.get_session() as session:
            trace = Trace(
                job_id=job_id,
                agent_name=agent_name,
                event_type=event_type,
                payload=payload
            )
            session.add(trace)

    def list_traces(self, agent: str | None = None, limit: int = 100) -> list[dict]:
        """List recent traces, optionally filtered by agent."""
        with self.get_session() as session:
            query = session.query(Trace)

            if agent:
                query = query.filter_by(agent_name=agent)

            traces = query.order_by(Trace.timestamp.desc()).limit(limit).all()

            def _iso_z(dt: datetime | None) -> str | None:
                return dt.isoformat() + "Z" if dt else None

            return [
                {
                    "id": trace.id,
                    "job_id": trace.job_id,
                    "agent_name": trace.agent_name,
                    "event_type": trace.event_type,
                    "payload": trace.payload,
                    "timestamp": _iso_z(trace.timestamp),
                }
                for trace in traces
            ]

    def get_trace(self, trace_id: str) -> dict | None:
        """Get a single trace event by id with full payload."""
        with self.get_session() as session:
            trace = session.query(Trace).filter_by(id=trace_id).first()
            if not trace:
                return None
            def _iso_z(dt: datetime | None) -> str | None:
                return dt.isoformat() + "Z" if dt else None
            return {
                "id": trace.id,
                "job_id": trace.job_id,
                "agent_name": trace.agent_name,
                "event_type": trace.event_type,
                "payload": trace.payload,
                "timestamp": _iso_z(trace.timestamp),
            }

    # Memory

    def memory_put(self, agent_name: str, key: str, value: Any, job_id: str | None = None) -> None:
        """Store a memory entry."""
        with self.get_session() as session:
            # Check if exists
            existing = session.query(Memory).filter_by(
                agent_name=agent_name,
                key=key,
                job_id=job_id
            ).first()

            if existing:
                existing.value = value
                existing.updated_at = datetime.utcnow()
            else:
                memory = Memory(
                    agent_name=agent_name,
                    job_id=job_id,
                    key=key,
                    value=value
                )
                session.add(memory)

    def memory_get(self, agent_name: str, key: str, job_id: str | None = None) -> Any:
        """Retrieve a memory entry."""
        with self.get_session() as session:
            memory = session.query(Memory).filter_by(
                agent_name=agent_name,
                key=key,
                job_id=job_id
            ).first()

            return memory.value if memory else None

    def memory_list(self, agent_name: str, job_id: str | None = None) -> dict[str, Any]:
        """List all memory entries for an agent."""
        with self.get_session() as session:
            query = session.query(Memory).filter_by(agent_name=agent_name)

            if job_id:
                query = query.filter_by(job_id=job_id)

            memories = query.all()

            return {mem.key: mem.value for mem in memories}

    # Agent registry

    def register_agent(self, agent_name: str, metadata: dict) -> None:
        """Register or update an agent in the registry."""
        with self.get_session() as session:
            existing = session.query(AgentRegistry).filter_by(agent_name=agent_name).first()

            if existing:
                existing.meta = metadata
                existing.last_seen = datetime.utcnow()
            else:
                registry = AgentRegistry(
                    agent_name=agent_name,
                    meta=metadata
                )
                session.add(registry)

    def list_agents(self) -> list[dict]:
        """List all registered agents with trace counts and last execution time."""
        with self.get_session() as session:
            agents = session.query(AgentRegistry).all()

            def _iso_z(dt: datetime | None) -> str | None:
                return dt.isoformat() + "Z" if dt else None

            result = []
            for agent in agents:
                # Get trace count for this agent
                trace_count = session.query(Trace).filter_by(agent_name=agent.agent_name).count()
                
                # Get last execution time (most recent trace)
                last_trace = (
                    session.query(Trace)
                    .filter_by(agent_name=agent.agent_name)
                    .order_by(Trace.timestamp.desc())
                    .first()
                )
                last_executed = _iso_z(last_trace.timestamp) if last_trace else None
                
                result.append({
                    "agent_name": agent.agent_name,
                    "metadata": agent.meta,
                    "last_seen": _iso_z(agent.last_seen),
                    "trace_count": trace_count,
                    "last_executed": last_executed,
                })
            
            return result

    # Metrics (aggregated from traces and jobs)

    def get_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics."""
        with self.get_session() as session:
            # Count both legacy Jobs and new PromptExecutions
            total_jobs = session.query(Job).count()
            total_prompts = session.query(PromptExecution).count()
            total_executions = total_jobs + total_prompts
            
            completed_jobs = session.query(Job).filter_by(status="completed").count()
            completed_prompts = session.query(PromptExecution).filter_by(status="completed").count()
            total_completed = completed_jobs + completed_prompts
            
            failed_jobs = session.query(Job).filter_by(status="failed").count()
            failed_prompts = session.query(PromptExecution).filter_by(status="failed").count()
            total_failed = failed_jobs + failed_prompts

            # Calculate average latency from both Jobs and PromptExecutions
            latencies = []
            
            # Get latencies from completed jobs
            completed = session.query(Job).filter_by(status="completed").all()
            for job in completed:
                if job.created_at and job.completed_at:
                    delta = (job.completed_at - job.created_at).total_seconds()
                    latencies.append(delta)
            
            # Get latencies from completed prompts
            completed_prompts_list = session.query(PromptExecution).filter_by(status="completed").all()
            for prompt in completed_prompts_list:
                if prompt.created_at and prompt.completed_at:
                    delta = (prompt.completed_at - prompt.created_at).total_seconds()
                    latencies.append(delta)

            avg_latency_sec = sum(latencies) / len(latencies) if latencies else 0

            # Active agents (from registry)
            active_agents = session.query(AgentRegistry).count()

            # Tool calls (from traces)
            tool_calls = session.query(Trace).filter_by(event_type="tool_call").count()

            # Cache hits (from traces)
            cache_hits = session.query(Trace).filter_by(event_type="cache_hit").count()

            # Total tokens from llm_usage traces
            llm_usage_traces = session.query(Trace).filter_by(event_type="llm_usage").all()
            total_tokens = 0
            for trace in llm_usage_traces:
                payload = trace.payload or {}
                total_tokens += int(payload.get("total_tokens") or 0)

            return {
                "total_jobs": total_executions,
                "completed_jobs": total_completed,
                "failed_jobs": total_failed,
                "avg_latency_ms": int(avg_latency_sec * 1000),
                "active_agents_count": active_agents,
                "tool_calls": tool_calls,
                "cache_hits": cache_hits,
                "total_tokens": total_tokens,
            }

    # Token usage metrics aggregated from llm_usage traces
    def get_token_usage(self, job_id: str) -> dict:
        """Aggregate token usage for a job from llm_usage traces."""
        with self.get_session() as session:
            traces = (
                session.query(Trace)
                .filter_by(job_id=job_id, event_type="llm_usage")
                .all()
            )
            total_prompt = 0
            total_completion = 0
            total = 0
            breakdown: dict[tuple[str | None, str | None], dict] = {}
            for tr in traces:
                payload = tr.payload or {}
                pt = int(payload.get("prompt_tokens") or 0)
                ct = int(payload.get("completion_tokens") or 0)
                tt = int(payload.get("total_tokens") or (pt + ct))
                prov = payload.get("provider")
                model = payload.get("model")
                total_prompt += pt
                total_completion += ct
                total += tt
                key = (prov, model)
                if key not in breakdown:
                    breakdown[key] = {
                        "provider": prov,
                        "model": model,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "calls": 0,
                    }
                breakdown[key]["prompt_tokens"] += pt
                breakdown[key]["completion_tokens"] += ct
                breakdown[key]["total_tokens"] += tt
                breakdown[key]["calls"] += 1

            return {
                "prompt_tokens": total_prompt,
                "completion_tokens": total_completion,
                "total_tokens": total,
                "by_model": list(breakdown.values()),
            }
