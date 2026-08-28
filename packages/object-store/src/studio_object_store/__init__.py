"""Object storage abstractions.

Compose uses MinIO as a stand-in for GCS in production.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectRef:
    bucket: str
    key: str


class ObjectStore(ABC):
    @abstractmethod
    def put_bytes(
        self,
        ref: ObjectRef,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_bytes(self, ref: ObjectRef) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        raise NotImplementedError
