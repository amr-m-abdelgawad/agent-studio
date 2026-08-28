"""Secret store abstractions.

Compose uses HashiCorp Vault as a stand-in for GCP Secret Manager in production.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretRef:
    name: str
    version: str = "latest"


class SecretStore(ABC):
    @abstractmethod
    def get_secret(self, ref: SecretRef) -> str:
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        raise NotImplementedError
