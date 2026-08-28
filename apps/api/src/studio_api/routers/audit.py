from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from studio_api.auth.dependencies import require_tenant_ctx, require_workspace_role
from studio_api.dal.base import require_tenant_dal
from studio_api.db import get_db
from studio_api.models import AuditLog
from studio_api.schemas import AuditEntryResponse

router = APIRouter(prefix="/v1/workspaces/{workspace_id}/audit", tags=["audit"])


@router.get("", response_model=list[AuditEntryResponse])
def list_audit(
    workspace_id: uuid.UUID,
    request: Request,
    action: str | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AuditEntryResponse]:
    tenant = require_tenant_ctx(request)
    require_workspace_role(tenant, "viewer")
    dal = require_tenant_dal(db, tenant)

    query = select(AuditLog).where(AuditLog.workspace_id == dal.workspace_id)
    if action:
        query = query.where(AuditLog.action == action)
    if from_ is not None:
        query = query.where(AuditLog.created_at >= from_)
    if to is not None:
        query = query.where(AuditLog.created_at <= to)
    query = query.order_by(AuditLog.created_at.desc())

    entries = db.scalars(query).all()
    return [
        AuditEntryResponse(
            id=entry.id,
            action=entry.action,
            actor_user_id=entry.actor_user_id,
            workspace_id=entry.workspace_id,
            details=entry.details,
            created_at=entry.created_at.isoformat(),
        )
        for entry in entries
    ]
