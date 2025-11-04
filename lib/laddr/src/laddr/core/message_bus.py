"""
Message Bus implementation with pluggable backends.

Provides RedisBus (production) and MemoryBus (testing/dev) implementations.
All agent communication and task distribution happens through this abstraction.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import json
import time
from typing import Any
import uuid


try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer  # type: ignore
except ImportError:  # optional dependency
    AIOKafkaProducer = None  # type: ignore
    AIOKafkaConsumer = None  # type: ignore


@dataclass
class TaskMessage:
    """Message sent to an agent's task queue."""

    task_id: str
    agent_name: str
    payload: dict[str, Any]
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "payload": self.payload,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskMessage:
        return cls(
            task_id=data["task_id"],
            agent_name=data["agent_name"],
            payload=data["payload"],
            created_at=data.get("created_at", time.time()),
        )


@dataclass
class ResponseMessage:
    """Response from an agent after processing a task."""

    task_id: str
    status: str  # "success" | "error" | "pending"
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ResponseMessage:
        return cls(
            task_id=data["task_id"],
            status=data["status"],
            result=data.get("result"),
            error=data.get("error"),
            created_at=data.get("created_at", time.time()),
        )


class RedisBus:
    """
    Redis-based message bus for production use.
    
    Uses Redis Streams for task queues and pub/sub for responses.
    Agents are registered in a hash with metadata and heartbeats.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client = None
        self._cancel_prefix = "laddr:cancel:"

    async def _get_client(self) -> Any:
        """Lazy connection to Redis."""
        if self._client is None:
            if aioredis is None:
                raise RuntimeError("redis package not installed. Install with: pip install redis")
            self._client = await aioredis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def register_agent(self, name: str, metadata: dict) -> bool:
        """
        Register an agent with metadata.
        
        Metadata should include: role, goal, tools, status, host_url (optional).
        """
        client = await self._get_client()
        metadata["last_heartbeat"] = time.time()
        metadata["status"] = metadata.get("status", "active")

        await client.hset(
            "laddr:agents:registry",
            name,
            json.dumps(metadata)
        )
        return True

    async def publish_task(self, agent_name: str, task: dict) -> str:
        """
        Publish a task to an agent's queue.
        
        Returns task_id for tracking.
        """
        client = await self._get_client()
        task_id = str(uuid.uuid4())

        message = TaskMessage(
            task_id=task_id,
            agent_name=agent_name,
            payload=task
        )

        # Add to agent's stream
        await client.xadd(
            f"laddr:tasks:{agent_name}",
            {"data": json.dumps(message.to_dict())}
        )

        return task_id

    async def publish_response(self, task_id: str, response: dict) -> bool:
        """
        Publish a response for a task.
        
        Stores in hash and publishes to response channel for waiters.
        If large-response offload is configured, store payload in storage and
        publish a small pointer instead.
        """
        client = await self._get_client()

        # Optionally offload large responses to storage
        try:
            storage = getattr(self, "_storage", None)
            bucket = getattr(self, "_storage_bucket", None) or "laddr"
            threshold_kb = getattr(self, "_storage_threshold_kb", None)

            payload_bytes = json.dumps(response).encode("utf-8")
            # If threshold is 0, store all responses; otherwise check size
            should_offload = (
                storage and 
                threshold_kb is not None and 
                (threshold_kb == 0 or len(payload_bytes) > threshold_kb * 1024)
            )
            
            print(f"[STORAGE] Checking offload: storage={storage is not None}, threshold={threshold_kb}, size={len(payload_bytes)}, should_offload={should_offload}")
            
            if should_offload:
                # Build a key with date prefix for grouping
                date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
                key = f"responses/{date_prefix}/{task_id}.json"
                metadata = {"content-type": "application/json"}
                try:
                    print(f"[STORAGE] Offloading to {bucket}/{key} (size={len(payload_bytes)} bytes)")
                    await storage.ensure_bucket(bucket)
                    await storage.put_object(bucket, key, payload_bytes, metadata=metadata)
                    print(f"[STORAGE] ✓ Successfully offloaded to {bucket}/{key}")
                    response = {
                        "task_id": task_id,
                        "offloaded": True,
                        "bucket": bucket,
                        "key": key,
                        "size_bytes": len(payload_bytes),
                    }
                except Exception as e:
                    # Fallback: keep inline if storage fails
                    print(f"[STORAGE] ✗ Failed to offload: {e}")
                    import traceback
                    traceback.print_exc()
                    pass
        except Exception as e:
            print(f"[STORAGE] Error in offload logic: {e}")
            pass

        # Store response
        await client.setex(
            f"laddr:response:{task_id}",
            300,  # 5 minute TTL
            json.dumps(response)
        )

        # Notify waiters via pub/sub
        await client.publish(
            f"laddr:response:{task_id}",
            json.dumps(response)
        )

        return True

    async def consume_tasks(self, agent_name: str, block_ms: int, count: int) -> list[dict]:
        """
        Consume tasks from agent's queue using consumer groups.
        
        Ensures each task is delivered to only ONE worker in a multi-worker setup.
        Blocks up to block_ms milliseconds waiting for tasks.
        Returns up to count tasks.
        """
        client = await self._get_client()
        stream_name = f"laddr:tasks:{agent_name}"
        group_name = f"{agent_name}_workers"
        consumer_name = f"worker_{uuid.uuid4().hex[:8]}"  # Unique consumer ID per call

        # Ensure consumer group exists (idempotent operation)
        try:
            await client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except Exception:
            # Group already exists, ignore error
            pass

        # Read from stream using consumer group (guarantees single delivery)
        try:
            result = await client.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: ">"},  # ">" means undelivered messages
                count=count,
                block=block_ms
            )

            if not result:
                return []

            tasks = []
            for stream, messages in result:
                for msg_id, msg_data in messages:
                    data = json.loads(msg_data["data"])
                    tasks.append(data)

                    # ACK the message so it's not re-delivered
                    await client.xack(stream_name, group_name, msg_id)
                    
                    # Optional: Clean up acknowledged messages to prevent stream growth
                    await client.xdel(stream_name, msg_id)

            return tasks
        except Exception:
            return []

    async def wait_for_response(self, task_id: str, timeout_sec: int) -> dict | None:
        """
        Wait for a response to a task (for synchronous chat endpoints).
        
        Uses pub/sub to listen for response, with fallback to polling.
        """
        client = await self._get_client()

        # First check if response already exists
        existing = await client.get(f"laddr:response:{task_id}")
        if existing:
            return json.loads(existing)

        # Subscribe to response channel
        pubsub = client.pubsub()
        await pubsub.subscribe(f"laddr:response:{task_id}")

        try:
            start = time.time()
            while time.time() - start < timeout_sec:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    return json.loads(message["data"])

                # Fallback: check storage
                existing = await client.get(f"laddr:response:{task_id}")
                if existing:
                    return json.loads(existing)

            return None
        finally:
            await pubsub.unsubscribe(f"laddr:response:{task_id}")
            await pubsub.close()

    async def get_registered_agents(self) -> dict[str, dict]:
        """Get all registered agents with metadata."""
        client = await self._get_client()

        agents_raw = await client.hgetall("laddr:agents:registry")
        agents = {}

        for name, metadata_json in agents_raw.items():
            agents[name] = json.loads(metadata_json)

        return agents

    async def list_agents(self) -> list[dict]:
        """Return a list of agent summaries for planning/delegation."""
        registry = await self.get_registered_agents()
        agents_list: list[dict] = []
        for name, meta in registry.items():
            agents_list.append({
                "name": name,
                "role": meta.get("role"),
                "goal": meta.get("goal"),
                "status": meta.get("status", "unknown"),
            })
        return agents_list

    async def get_queue_depth(self, agent_name: str) -> int:
        """Get number of pending tasks for an agent."""
        client = await self._get_client()

        try:
            length = await client.xlen(f"laddr:tasks:{agent_name}")
            return length
        except Exception:
            return 0

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception:
            return False

    async def cancel_job(self, job_id: str) -> bool:
        """Mark a job as canceled with a TTL flag in Redis."""
        client = await self._get_client()
        key = f"{self._cancel_prefix}{job_id}"
        try:
            await client.setex(key, 3600, "1")
            return True
        except Exception:
            return False

    async def is_canceled(self, job_id: str) -> bool:
        """Check whether a cancel flag is present for a job."""
        client = await self._get_client()
        key = f"{self._cancel_prefix}{job_id}"
        try:
            val = await client.get(key)
            return bool(val)
        except Exception:
            return False


class MemoryBus:
    """
    In-memory message bus for testing and quick local dev.
    
    Not suitable for production or distributed systems.
    """

    def __init__(self):
        self._agents: dict[str, dict] = {}
        self._tasks: dict[str, list[dict]] = {}
        self._responses: dict[str, dict] = {}
        self._waiters: dict[str, list[asyncio.Future]] = {}
        self._canceled: set[str] = set()

    async def register_agent(self, name: str, metadata: dict) -> bool:
        """Register an agent with metadata."""
        metadata["last_heartbeat"] = time.time()
        metadata["status"] = metadata.get("status", "active")
        self._agents[name] = metadata

        if name not in self._tasks:
            self._tasks[name] = []

        return True

    async def publish_task(self, agent_name: str, task: dict) -> str:
        """Publish a task to an agent's in-memory queue."""
        task_id = str(uuid.uuid4())
        message = TaskMessage(
            task_id=task_id, agent_name=agent_name, payload=task
        ).to_dict()
        self._tasks.setdefault(agent_name, []).append(message)
        return task_id

    async def publish_response(self, task_id: str, response: dict) -> bool:
        """Publish a response for a task, notifying any waiters; supports optional offload metadata."""
        # Optional offload: emulate RedisBus behavior by rewriting payload to pointer if needed
        try:
            storage = getattr(self, "_storage", None)
            bucket = getattr(self, "_storage_bucket", None) or "laddr"
            threshold_kb = getattr(self, "_storage_threshold_kb", None)
            payload_bytes = json.dumps(response).encode("utf-8")
            # If threshold is 0, store all responses; otherwise check size
            should_offload = (
                storage and 
                threshold_kb is not None and 
                (threshold_kb == 0 or len(payload_bytes) > threshold_kb * 1024)
            )
            
            if should_offload:
                date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
                key = f"responses/{date_prefix}/{task_id}.json"
                metadata = {"content-type": "application/json"}
                try:
                    await storage.ensure_bucket(bucket)
                    await storage.put_object(bucket, key, payload_bytes, metadata=metadata)
                    response = {
                        "task_id": task_id,
                        "offloaded": True,
                        "bucket": bucket,
                        "key": key,
                        "size_bytes": len(payload_bytes),
                    }
                except Exception:
                    pass
        except Exception:
            pass

        self._responses[task_id] = response
        # Notify waiters
        if task_id in self._waiters:
            for fut in self._waiters[task_id]:
                if not fut.done():
                    fut.set_result(response)
            del self._waiters[task_id]
        return True

    async def consume_tasks(self, agent_name: str, block_ms: int, count: int) -> list[dict]:
        """Consume tasks from an agent's queue, simulating blocking behavior."""
        queue = self._tasks.get(agent_name, [])
        if not queue:
            if block_ms > 0:
                await asyncio.sleep(block_ms / 1000.0)
            return []
        tasks = queue[:count]
        self._tasks[agent_name] = queue[count:]
        return tasks

    async def wait_for_response(self, task_id: str, timeout_sec: int) -> dict | None:
        """Wait for a response published via publish_response."""
        if task_id in self._responses:
            return self._responses[task_id]
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._waiters.setdefault(task_id, []).append(fut)
        try:
            return await asyncio.wait_for(fut, timeout=timeout_sec)
        except asyncio.TimeoutError:
            return None

    async def get_registered_agents(self) -> dict[str, dict]:
        return dict(self._agents)

    async def list_agents(self) -> list[dict]:
        """Return a list of agent summaries for planning/delegation."""
        registry = await self.get_registered_agents()
        return [
            {
                "name": name,
                "role": meta.get("role"),
                "goal": meta.get("goal"),
                "status": meta.get("status", "unknown"),
            }
            for name, meta in registry.items()
        ]

    async def get_queue_depth(self, agent_name: str) -> int:
        return len(self._tasks.get(agent_name, []))

    async def health_check(self) -> bool:
        return True

    async def cancel_job(self, job_id: str) -> bool:
        self._canceled.add(job_id)
        return True

    async def is_canceled(self, job_id: str) -> bool:
        return job_id in self._canceled


class KafkaBus:
    """
    Kafka-based message bus (experimental / enterprise option).

    Uses topics per agent: laddr.tasks.<agent_name>
    Responses published to: laddr.responses
    Agent registry is memory-only in this minimal implementation.
    """

    def __init__(self, bootstrap_servers: str):
        if AIOKafkaProducer is None or AIOKafkaConsumer is None:
            raise RuntimeError("aiokafka is not installed. Install with: pip install aiokafka")
        self.bootstrap_servers = bootstrap_servers
        self._producer = None
        self._consumers: dict[str, Any] = {}  # Cache consumers per agent
        self._agents: dict[str, dict] = {}
        self._waiters: dict[str, list[asyncio.Future]] = {}
        self._canceled: set[str] = set()

    async def _get_producer(self) -> Any:
        if self._producer is None:
            print(f"[KafkaBus] Creating Kafka producer for {self.bootstrap_servers}")
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                acks='all',  # Wait for all replicas to acknowledge
                max_request_size=10485760,  # 10MB max message size
            )
            await self._producer.start()
            print(f"[KafkaBus] Producer started successfully")
        return self._producer

    async def _get_consumer(self, agent_name: str) -> Any:
        """Get or create a persistent consumer for the agent."""
        if agent_name not in self._consumers:
            print(f"[KafkaBus] Creating consumer for agent: {agent_name}")
            consumer = AIOKafkaConsumer(
                f"laddr.tasks.{agent_name}",
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"laddr-{agent_name}-workers",
                enable_auto_commit=True,  # Auto-commit offsets
                auto_offset_reset="earliest",  # Start from beginning if no committed offset
                max_poll_records=10,
            )
            await consumer.start()
            print(f"[KafkaBus] Consumer started for agent: {agent_name}")
            self._consumers[agent_name] = consumer
        return self._consumers[agent_name]

    async def register_agent(self, name: str, metadata: dict) -> bool:
        metadata["last_heartbeat"] = time.time()
        metadata["status"] = metadata.get("status", "active")
        self._agents[name] = metadata
        return True

    async def publish_task(self, agent_name: str, task: dict) -> str:
        try:
            print(f"[KafkaBus] Publishing task to agent: {agent_name}")
            producer = await self._get_producer()
            print(f"[KafkaBus] Producer obtained")
            task_id = str(uuid.uuid4())
            message = TaskMessage(task_id=task_id, agent_name=agent_name, payload=task).to_dict()
            data = json.dumps(message).encode("utf-8")
            topic = f"laddr.tasks.{agent_name}"
            print(f"[KafkaBus] Sending to topic: {topic}, task_id: {task_id}")
            await producer.send_and_wait(topic, data)
            print(f"[KafkaBus] Task published successfully: {task_id}")
            return task_id
        except Exception as e:
            print(f"[KafkaBus] ERROR publishing task: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def publish_response(self, task_id: str, response: dict) -> bool:
        print(f"[KafkaBus] Publishing response for task: {task_id}")
        
        # Optional offload similar to other buses
        try:
            storage = getattr(self, "_storage", None)
            bucket = getattr(self, "_storage_bucket", None) or "laddr"
            threshold_kb = getattr(self, "_storage_threshold_kb", None)
            payload_bytes = json.dumps(response).encode("utf-8")
            # If threshold is 0, store all responses; otherwise check size
            should_offload = (
                storage and 
                threshold_kb is not None and 
                (threshold_kb == 0 or len(payload_bytes) > threshold_kb * 1024)
            )
            
            if should_offload:
                print(f"[KafkaBus] Offloading response to storage (size: {len(payload_bytes)} bytes)")
                date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
                key = f"responses/{date_prefix}/{task_id}.json"
                metadata = {"content-type": "application/json"}
                try:
                    await storage.ensure_bucket(bucket)
                    await storage.put_object(bucket, key, payload_bytes, metadata=metadata)
                    print(f"[KafkaBus] Response offloaded to {bucket}/{key}")
                    response = {
                        "task_id": task_id,
                        "offloaded": True,
                        "bucket": bucket,
                        "key": key,
                        "size_bytes": len(payload_bytes),
                    }
                except Exception as e:
                    print(f"[KafkaBus] ERROR offloading response: {e}")
                    pass
        except Exception as e:
            print(f"[KafkaBus] ERROR in publish_response storage check: {e}")
            pass

        # Notify in-memory waiters
        if task_id in self._waiters:
            for fut in self._waiters[task_id]:
                if not fut.done():
                    fut.set_result(response)
            del self._waiters[task_id]

        # Fire-and-forget to responses topic for external consumers
        try:
            print(f"[KafkaBus] Publishing to laddr.responses topic...")
            producer = await self._get_producer()
            await producer.send_and_wait("laddr.responses", json.dumps(response).encode("utf-8"))
            print(f"[KafkaBus] Response published to Kafka successfully")
        except Exception as e:
            print(f"[KafkaBus] ERROR publishing response to Kafka: {e}")
            pass
        return True

    async def consume_tasks(self, agent_name: str, block_ms: int, count: int) -> list[dict]:
        consumer = await self._get_consumer(agent_name)
        tasks: list[dict] = []
        try:
            result = await consumer.getmany(timeout_ms=block_ms, max_records=count)
            for tp, messages in result.items():
                for msg in messages:
                    try:
                        data = json.loads(msg.value.decode("utf-8"))
                        tasks.append(data)
                    except Exception:
                        continue
            # commit offsets for consumed messages
            if tasks:
                await consumer.commit()
        except Exception as e:
            # Log error but don't crash the worker
            print(f"Error consuming tasks: {e}")
        return tasks

    async def wait_for_response(self, task_id: str, timeout_sec: int) -> dict | None:
        """
        Wait for a response from Kafka responses topic.
        For Kafka, we need to actually poll the topic since in-memory waiters
        don't work across processes.
        """
        print(f"[KafkaBus] Waiting for response to task: {task_id}, timeout: {timeout_sec}s")
        
        # Create a dedicated consumer for this response
        # Use a unique group ID so we read all messages
        consumer = AIOKafkaConsumer(
            "laddr.responses",
            bootstrap_servers=self.bootstrap_servers,
            group_id=f"wait-{task_id}",  # Unique group per wait
            auto_offset_reset="earliest",  # Read all messages
            enable_auto_commit=False,
            consumer_timeout_ms=1000,  # Poll every second
        )
        
        try:
            await consumer.start()
            print(f"[KafkaBus] Consumer started, polling for response...")
            
            start_time = asyncio.get_event_loop().time()
            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout_sec:
                    print(f"[KafkaBus] Timeout waiting for response to {task_id}")
                    return None
                
                # Poll for messages
                try:
                    result = await consumer.getmany(timeout_ms=2000, max_records=100)
                    for tp, messages in result.items():
                        for msg in messages:
                            try:
                                data = json.loads(msg.value.decode("utf-8"))
                                response_task_id = data.get("task_id")
                                
                                if response_task_id == task_id:
                                    print(f"[KafkaBus] Found response for task {task_id}")
                                    
                                    # Check if response was offloaded to storage
                                    if data.get("offloaded"):
                                        print(f"[KafkaBus] Response offloaded, retrieving from storage...")
                                        # Retrieve from storage
                                        storage = getattr(self, "_storage", None)
                                        if storage:
                                            bucket = data.get("bucket", "laddr")
                                            key = data.get("key")
                                            if key:
                                                try:
                                                    stored_data = await storage.get_object(bucket, key)
                                                    actual_response = json.loads(stored_data.decode("utf-8"))
                                                    print(f"[KafkaBus] Retrieved response from storage")
                                                    return actual_response
                                                except Exception as e:
                                                    print(f"[KafkaBus] Error retrieving from storage: {e}")
                                                    return data  # Return offload metadata as fallback
                                        return data
                                    else:
                                        # Response is inline
                                        return data
                            except Exception as e:
                                print(f"[KafkaBus] Error parsing message: {e}")
                                continue
                except asyncio.TimeoutError:
                    # No messages in this poll, continue waiting
                    pass
                
                # Small sleep to avoid tight loop
                await asyncio.sleep(0.1)
                
        finally:
            await consumer.stop()
            print(f"[KafkaBus] Consumer stopped for task {task_id}")

    async def get_registered_agents(self) -> dict[str, dict]:
        """
        Get registered agents by discovering Kafka topics.
        Topics follow the pattern: laddr.tasks.<agent_name>
        """
        try:
            from aiokafka.admin import AIOKafkaAdminClient
            admin = AIOKafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            await admin.start()
            try:
                topics = await admin.list_topics()
                # Extract agent names from topic names
                prefix = "laddr.tasks."
                for topic in topics:
                    if topic.startswith(prefix):
                        agent_name = topic[len(prefix):]
                        if agent_name not in self._agents:
                            # Register discovered agent with default metadata
                            self._agents[agent_name] = {
                                "role": "agent",
                                "goal": f"Process tasks for {agent_name}",
                                "status": "active",
                                "last_heartbeat": time.time(),
                                "tools": []
                            }
            finally:
                await admin.close()
        except Exception:
            # If discovery fails, return what we have in memory
            pass
        return dict(self._agents)

    async def list_agents(self) -> list[dict]:
        """Return a list of agent summaries for planning/delegation."""
        registry = await self.get_registered_agents()
        return [
            {
                "name": name,
                "role": meta.get("role"),
                "goal": meta.get("goal"),
                "status": meta.get("status", "unknown"),
            }
            for name, meta in registry.items()
        ]

    async def get_queue_depth(self, agent_name: str) -> int:
        # Not tracked in this minimal implementation
        return 0

    async def health_check(self) -> bool:
        # Producer init check
        try:
            await self._get_producer()
            return True
        except Exception:
            return False

    async def cancel_job(self, job_id: str) -> bool:
        self._canceled.add(job_id)
        return True

    async def is_canceled(self, job_id: str) -> bool:
        return job_id in self._canceled
