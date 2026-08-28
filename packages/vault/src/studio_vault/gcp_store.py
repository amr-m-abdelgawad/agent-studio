from __future__ import annotations

import os

from google.cloud import secretmanager

from studio_vault import SecretRef, SecretStore


class GcpSecretStore(SecretStore):
    """GCP Secret Manager backend for production."""

    def __init__(self, project_id: str | None = None) -> None:
        self._project_id = project_id or os.environ.get("GCP_PROJECT_ID", "")
        self._client = secretmanager.SecretManagerServiceClient()

    def get_secret(self, ref: SecretRef) -> str:
        if not self._project_id:
            raise RuntimeError("GCP_PROJECT_ID is required for GcpSecretStore")
        name = (
            f"projects/{self._project_id}/secrets/{ref.name}/versions/{ref.version}"
        )
        response = self._client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8")

    def ping(self) -> bool:
        return bool(self._project_id)
