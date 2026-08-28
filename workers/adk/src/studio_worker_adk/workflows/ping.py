from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import SearchAttributeKey, SearchAttributePair, TypedSearchAttributes


@dataclass
class PingWorkflowInput:
    message: str
    sleep_seconds: int = 0
    tenant_id: str | None = None


@activity.defn(name="ping_activity")
async def ping_activity(message: str) -> str:
    return f"pong:{message}"


@workflow.defn(name="PingWorkflow")
class PingWorkflow:
    @workflow.run
    async def run(self, input: PingWorkflowInput) -> str:
        if input.tenant_id:
            tenant_attr = SearchAttributeKey.for_keyword("TenantId")
            workflow.upsert_search_attributes(
                TypedSearchAttributes([SearchAttributePair(tenant_attr, input.tenant_id)])
            )
        if input.sleep_seconds > 0:
            await workflow.sleep(timedelta(seconds=input.sleep_seconds))
        return await workflow.execute_activity(
            ping_activity,
            input.message,
            start_to_close_timeout=timedelta(seconds=30),
        )
