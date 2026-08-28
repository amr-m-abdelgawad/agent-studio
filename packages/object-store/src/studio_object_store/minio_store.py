from __future__ import annotations

import io
import os

from minio import Minio

from studio_object_store import ObjectRef, ObjectStore


class MinioObjectStore(ObjectStore):
    """MinIO stand-in for local compose."""

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool = False,
    ) -> None:
        endpoint_raw = endpoint or os.environ.get("MINIO_ENDPOINT", "minio:9000")
        endpoint_host = endpoint_raw.replace("http://", "").replace("https://", "")
        self._client = Minio(
            endpoint=endpoint_host,
            access_key=access_key or os.environ.get("MINIO_ROOT_USER", "minioadmin"),
            secret_key=secret_key or os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin"),
            secure=secure,
        )

    def put_bytes(
        self,
        ref: ObjectRef,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        if not self._client.bucket_exists(ref.bucket):
            self._client.make_bucket(ref.bucket)
        self._client.put_object(
            ref.bucket,
            ref.key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def get_bytes(self, ref: ObjectRef) -> bytes:
        response = self._client.get_object(ref.bucket, ref.key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def ping(self) -> bool:
        try:
            list(self._client.list_buckets())
            return True
        except Exception:
            return False
