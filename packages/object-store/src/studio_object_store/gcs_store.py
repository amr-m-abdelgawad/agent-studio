from __future__ import annotations

import os

from google.cloud import storage

from studio_object_store import ObjectRef, ObjectStore


class GcsObjectStore(ObjectStore):
    """Google Cloud Storage backend for production."""

    def __init__(self, project_id: str | None = None) -> None:
        self._project_id = project_id or os.environ.get("GCP_PROJECT_ID")
        self._client = storage.Client(project=self._project_id)

    def put_bytes(
        self,
        ref: ObjectRef,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        bucket = self._client.bucket(ref.bucket)
        blob = bucket.blob(ref.key)
        blob.upload_from_string(data, content_type=content_type)

    def get_bytes(self, ref: ObjectRef) -> bytes:
        bucket = self._client.bucket(ref.bucket)
        blob = bucket.blob(ref.key)
        return blob.download_as_bytes()

    def ping(self) -> bool:
        try:
            next(self._client.list_buckets(max_results=1), None)
            return True
        except Exception:
            return False
