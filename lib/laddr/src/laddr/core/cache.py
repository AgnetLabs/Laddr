"""
Cache backend implementations.

Provides pluggable cache backends: InMemory, Redis.
"""

from __future__ import annotations

import time
from typing import Any


try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None


class InMemoryCache:
    """
    In-memory cache for local dev and testing.
    
    Simple dict-based cache with optional TTL.
    """

    def __init__(self):
        self._cache: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str) -> Any:
        """Get value from cache."""
        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]

        # Check expiration
        if expires_at is not None and time.time() > expires_at:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL (seconds)."""
        expires_at = None
        if ttl is not None:
            expires_at = time.time() + ttl

        self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


class RedisCache:
    """
    Redis-based cache for production.
    
    Uses Redis with TTL support.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        """Lazy connection to Redis."""
        if self._client is None:
            if aioredis is None:
                raise RuntimeError("redis package not installed. Install with: pip install redis")
            self._client = await aioredis.from_url(self.redis_url, decode_responses=False)
        return self._client

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        client = await self._get_client()
        value = await client.get(f"laddr:cache:{key}")

        if value is None:
            return None

        # Deserialize (simple pickle)
        import pickle
        return pickle.loads(value)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL (seconds)."""
        client = await self._get_client()

        # Serialize (simple pickle)
        import pickle
        serialized = pickle.dumps(value)

        if ttl is not None:
            await client.setex(f"laddr:cache:{key}", ttl, serialized)
        else:
            await client.set(f"laddr:cache:{key}", serialized)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        client = await self._get_client()
        await client.delete(f"laddr:cache:{key}")

    async def clear(self) -> None:
        """Clear all cache entries (with laddr:cache: prefix)."""
        client = await self._get_client()
        keys = await client.keys("laddr:cache:*")
        if keys:
            await client.delete(*keys)
