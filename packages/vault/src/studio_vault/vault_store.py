from __future__ import annotations

import os

import hvac

from studio_vault import SecretRef, SecretStore


class VaultSecretStore(SecretStore):
    """HashiCorp Vault stand-in for local compose."""

    def __init__(self, addr: str | None = None, token: str | None = None) -> None:
        self._client = hvac.Client(url=addr or os.environ.get("VAULT_ADDR", "http://vault:8200"))
        token_value = token or os.environ.get("VAULT_TOKEN", "dev-root-token")
        self._client.token = token_value

    def get_secret(self, ref: SecretRef) -> str:
        response = self._client.secrets.kv.v2.read_secret_version(path=ref.name)
        data = response["data"]["data"]
        value = data.get("value")
        if value is None:
            raise KeyError(f"Secret {ref.name} missing 'value' field")
        return str(value)

    def ping(self) -> bool:
        try:
            return bool(self._client.sys.is_initialized())
        except Exception:
            return False
