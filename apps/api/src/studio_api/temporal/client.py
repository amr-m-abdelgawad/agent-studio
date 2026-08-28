from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class WorkflowStartResult:
    workflow_id: str
    run_id: str


class TemporalClientProtocol(Protocol):
    async def start_ping_workflow(self, workspace_id: uuid.UUID) -> WorkflowStartResult: ...


class FakeTemporalClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def start_ping_workflow(self, workspace_id: uuid.UUID) -> WorkflowStartResult:
        workflow_id = f"ping-{workspace_id}"
        run_id = str(uuid.uuid4())
        self.calls.append(
            {
                "workspace_id": str(workspace_id),
                "message": "ping",
                "sleep_seconds": 0,
                "tenant_id": str(workspace_id),
            }
        )
        return WorkflowStartResult(workflow_id=workflow_id, run_id=run_id)


class LiveTemporalClient:
    def __init__(self) -> None:
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from studio_api.config import get_settings
            from temporalio.client import Client

            settings = get_settings()
            self._client = await Client.connect(
                settings.temporal_host,
                namespace=settings.temporal_namespace,
            )
        return self._client

    async def start_ping_workflow(self, workspace_id: uuid.UUID) -> WorkflowStartResult:
        from studio_api.config import get_settings
        from studio_worker_adk.workflows.ping import PingWorkflow, PingWorkflowInput

        settings = get_settings()
        client = await self._get_client()
        workflow_id = f"ping-{workspace_id}-{uuid.uuid4()}"
        handle = await client.start_workflow(
            PingWorkflow.run,
            PingWorkflowInput(
                message="ping",
                sleep_seconds=0,
                tenant_id=str(workspace_id),
            ),
            id=workflow_id,
            task_queue=settings.temporal_task_queue,
        )
        return WorkflowStartResult(
            workflow_id=handle.id,
            run_id=handle.result_run_id or handle.first_execution_run_id,
        )


_client: TemporalClientProtocol | None = None


def get_temporal_client() -> TemporalClientProtocol:
    global _client
    if _client is None:
        import os

        if os.environ.get("TEMPORAL_ADDRESS"):
            _client = LiveTemporalClient()
        else:
            _client = FakeTemporalClient()
    return _client


def set_temporal_client(client: TemporalClientProtocol | None) -> None:
    global _client
    _client = client
