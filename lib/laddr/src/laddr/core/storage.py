"""
Artifact storage abstraction with S3-compatible backends.

Supports both AWS S3 and MinIO (self-hosted S3-compatible storage).
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import io


class S3Storage:
    """
    S3-compatible storage backend for AWS S3 and MinIO.
    
    This class uses the minio Python package which is fully compatible with:
    - AWS S3 (cloud)
    - MinIO (self-hosted)
    - Any S3-compatible storage service
    
    For AWS S3:
        endpoint: "s3.amazonaws.com" or "s3.<region>.amazonaws.com"
        access_key: AWS Access Key ID
        secret_key: AWS Secret Access Key
        secure: True (use HTTPS)
    
    For MinIO:
        endpoint: "localhost:9000" or "minio:9000"
        access_key: MinIO access key (default: minioadmin)
        secret_key: MinIO secret key
        secure: False (or True for HTTPS)
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        region: str | None = None
    ):
        """
        Initialize S3-compatible storage.
        
        Args:
            endpoint: S3 endpoint (e.g., "s3.amazonaws.com" or "minio:9000")
            access_key: Access key (AWS Access Key ID or MinIO access key)
            secret_key: Secret key (AWS Secret Access Key or MinIO secret key)
            secure: Use HTTPS (True for AWS S3, False for local MinIO)
            region: AWS region (optional, e.g., "us-east-1")
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.region = region
        self._client = None

    def _get_client(self):
        """Get synchronous S3-compatible client."""
        if self._client is None:
            try:
                from minio import Minio
                self._client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure,
                    region=self.region
                )
            except ImportError:
                raise RuntimeError(
                    "minio package not installed. Install with: pip install minio"
                )
        return self._client

    async def ensure_bucket(self, bucket: str):
        """
        Ensure bucket exists, create if not.
        
        Automatically creates the bucket if it doesn't exist.
        For AWS S3, uses the region specified during initialization.
        
        Args:
            bucket: Bucket name to ensure exists
        
        Raises:
            RuntimeError: If bucket creation fails
        """
        def _ensure():
            client = self._get_client()
            if not client.bucket_exists(bucket):
                try:
                    # Create bucket with region if specified (required for AWS S3)
                    if self.region:
                        client.make_bucket(bucket, location=self.region)
                    else:
                        client.make_bucket(bucket)
                    print(f"✓ Created storage bucket: {bucket}")
                except Exception as e:
                    raise RuntimeError(
                        f"Bucket '{bucket}' does not exist and could not be created. "
                        f"Error: {e}. Check permissions and configuration."
                    )

        await asyncio.get_event_loop().run_in_executor(None, _ensure)

    async def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        metadata: dict | None = None
    ) -> bool:
        """
        Store object in S3-compatible storage.
        
        Args:
            bucket: Bucket name
            key: Object key/path
            data: Data bytes
            metadata: Optional metadata
        
        Returns:
            True if successful
        """
        await self.ensure_bucket(bucket)

        def _put():
            client = self._get_client()
            # MinIO signing can fail if content-type is passed inside metadata,
            # so map common keys to the dedicated content_type parameter and
            # pass only non-reserved metadata keys.
            content_type = None
            meta = None
            if metadata:
                # Extract content type from common variations
                content_type = (
                    metadata.get("content-type")
                    or metadata.get("Content-Type")
                    or metadata.get("content_type")
                )
                # Filter out content-type keys from metadata dict
                meta = {k: v for k, v in metadata.items() if k.lower() not in ("content-type", "content_type")}

            client.put_object(
                bucket,
                key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=meta,
            )
            return True

        return await asyncio.get_event_loop().run_in_executor(None, _put)

    async def get_object(self, bucket: str, key: str) -> bytes:
        """
        Retrieve object from S3-compatible storage.
        
        Args:
            bucket: Bucket name
            key: Object key/path
        
        Returns:
            Object data as bytes
        """
        def _get():
            client = self._get_client()
            response = client.get_object(bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            return data

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000
    ) -> list[dict]:
        """
        List objects in bucket.
        
        Args:
            bucket: Bucket name
            prefix: Optional prefix filter
            max_keys: Max number of objects
        
        Returns:
            List of object metadata dicts
        """
        def _list():
            client = self._get_client()
            objects = []

            for obj in client.list_objects(bucket, prefix=prefix):
                objects.append({
                    "key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "etag": obj.etag
                })

                if len(objects) >= max_keys:
                    break

            return objects

        return await asyncio.get_event_loop().run_in_executor(None, _list)

    async def delete_object(self, bucket: str, key: str) -> bool:
        """
        Delete object from S3-compatible storage.
        
        Args:
            bucket: Bucket name
            key: Object key/path
        
        Returns:
            True if successful
        """
        def _delete():
            client = self._get_client()
            client.remove_object(bucket, key)
            return True

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def object_exists(self, bucket: str, key: str) -> bool:
        """
        Check if object exists.
        
        Args:
            bucket: Bucket name
            key: Object key/path
        
        Returns:
            True if object exists
        """
        def _exists():
            client = self._get_client()
            try:
                client.stat_object(bucket, key)
                return True
            except Exception:
                return False

        return await asyncio.get_event_loop().run_in_executor(None, _exists)


# Backward compatibility alias
MinIOStorage = S3Storage


class InMemoryStorage:
    """In-memory storage backend for testing."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: dict[str, dict[str, tuple[bytes, dict]]] = {}

    async def ensure_bucket(self, bucket: str):
        """Ensure bucket exists."""
        if bucket not in self._storage:
            self._storage[bucket] = {}

    async def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        metadata: dict | None = None
    ) -> bool:
        """Store object in memory."""
        await self.ensure_bucket(bucket)
        self._storage[bucket][key] = (data, metadata or {})
        return True

    async def get_object(self, bucket: str, key: str) -> bytes:
        """Retrieve object from memory."""
        if bucket not in self._storage or key not in self._storage[bucket]:
            raise FileNotFoundError(f"Object {bucket}/{key} not found")
        return self._storage[bucket][key][0]

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000
    ) -> list[dict]:
        """List objects in memory."""
        if bucket not in self._storage:
            return []

        objects = []
        for key, (data, metadata) in self._storage[bucket].items():
            if key.startswith(prefix):
                objects.append({
                    "key": key,
                    "size": len(data),
                    "last_modified": datetime.utcnow().isoformat(),
                    "etag": str(hash(data))
                })

                if len(objects) >= max_keys:
                    break

        return objects

    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object from memory."""
        if bucket in self._storage and key in self._storage[bucket]:
            del self._storage[bucket][key]
            return True
        return False

    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if object exists."""
        return bucket in self._storage and key in self._storage[bucket]
