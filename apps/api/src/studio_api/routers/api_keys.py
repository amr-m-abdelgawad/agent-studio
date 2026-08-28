from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from studio_api.auth.dependencies import require_tenant_ctx, require_workspace_role
from studio_api.config import get_settings
from studio_api.crypto import generate_api_key, hash_secret
from studio_api.dal.base import require_tenant_dal
from studio_api.db import get_db
from studio_api.errors import APIError
from studio_api.models import ApiKey
from studio_api.schemas import ApiKeyCreateRequest, ApiKeyResponse
from studio_api.services.audit import record_audit
from studio_api.timeutil import utcnow

router = APIRouter(prefix="/v1/workspaces/{workspace_id}/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyResponse, status_code=201)
def create_api_key(
    workspace_id: uuid.UUID,
    body: ApiKeyCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ApiKeyResponse:
    tenant = require_tenant_ctx(request)
    require_workspace_role(tenant, "admin")
    dal = require_tenant_dal(db, tenant)

    settings = get_settings()
    full_key, prefix, _secret = generate_api_key()
    api_key = ApiKey(
        workspace_id=dal.workspace_id,
        created_by_user_id=tenant.user.id,
        name=body.name,
        prefix=prefix,
        secret_hash=hash_secret(full_key, settings.session_secret),
    )
    db.add(api_key)
    record_audit(
        db,
        org_id=dal.org_id,
        workspace_id=dal.workspace_id,
        actor_user_id=tenant.user.id,
        action="api_key_create",
        details={"api_key_id": str(api_key.id), "name": body.name},
    )
    db.commit()
    db.refresh(api_key)
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        created_at=api_key.created_at.isoformat(),
        secret=full_key,
    )


@router.get("", response_model=list[ApiKeyResponse])
def list_api_keys(
    workspace_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> list[ApiKeyResponse]:
    tenant = require_tenant_ctx(request)
    require_workspace_role(tenant, "admin")
    dal = require_tenant_dal(db, tenant)

    keys = db.scalars(
        select(ApiKey)
        .where(ApiKey.workspace_id == dal.workspace_id, ApiKey.revoked_at.is_(None))
        .order_by(ApiKey.created_at.desc())
    ).all()
    return [
        ApiKeyResponse(
            id=key.id,
            name=key.name,
            prefix=key.prefix,
            created_at=key.created_at.isoformat(),
        )
        for key in keys
    ]


@router.delete("/{key_id}", status_code=204)
def revoke_api_key(
    workspace_id: uuid.UUID,
    key_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    tenant = require_tenant_ctx(request)
    require_workspace_role(tenant, "admin")
    dal = require_tenant_dal(db, tenant)

    api_key = db.scalar(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.workspace_id == dal.workspace_id)
    )
    if api_key is None:
        raise APIError("not_found", "API key not found", 404)
    if api_key.revoked_at is not None:
        return

    api_key.revoked_at = utcnow()
    record_audit(
        db,
        org_id=dal.org_id,
        workspace_id=dal.workspace_id,
        actor_user_id=tenant.user.id,
        action="api_key_revoke",
        details={"api_key_id": str(api_key.id), "name": api_key.name},
    )
    db.commit()
