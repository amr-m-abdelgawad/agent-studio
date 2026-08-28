from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from studio_api.auth.dependencies import require_tenant_ctx, require_workspace_role
from studio_api.dal.base import require_tenant_dal
from studio_api.db import get_db
from studio_api.errors import APIError
from studio_api.models import PingRun
from studio_api.schemas import PingStartResponse, PingStatusResponse
from studio_api.temporal.client import get_temporal_client

router = APIRouter(prefix="/v1/workspaces/{workspace_id}/debug", tags=["debug"])


@router.post("/ping", response_model=PingStartResponse)
async def start_ping(
    workspace_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> PingStartResponse:
    tenant = require_tenant_ctx(request)
    require_workspace_role(tenant, "editor")
    dal = require_tenant_dal(db, tenant)

    client = get_temporal_client()
    try:
        result = await client.start_ping_workflow(dal.workspace_id)
    except Exception as exc:
        raise APIError("temporal_unavailable", "Temporal is unavailable", 503) from exc

    ping_run = PingRun(
        workspace_id=dal.workspace_id,
        workflow_id=result.workflow_id,
        run_id=result.run_id,
        started_by_user_id=tenant.user.id,
    )
    db.add(ping_run)
    db.commit()
    return PingStartResponse(workflow_id=result.workflow_id, run_id=result.run_id)


@router.get("/ping/{workflow_id}", response_model=PingStatusResponse)
def get_ping_status(
    workspace_id: uuid.UUID,
    workflow_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PingStatusResponse:
    tenant = require_tenant_ctx(request)
    require_workspace_role(tenant, "viewer")
    dal = require_tenant_dal(db, tenant)

    ping_run = db.scalar(
        select(PingRun).where(
            PingRun.workflow_id == workflow_id,
            PingRun.workspace_id == dal.workspace_id,
        )
    )
    if ping_run is None:
        raise APIError("not_found", "Ping run not found", 404)

    return PingStatusResponse(
        workflow_id=ping_run.workflow_id,
        run_id=ping_run.run_id,
        workspace_id=ping_run.workspace_id,
    )
