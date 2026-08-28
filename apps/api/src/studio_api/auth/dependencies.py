from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from studio_api.auth.session import SESSION_COOKIE, AuthContext, get_user_for_session_token
from studio_api.config import get_settings
from studio_api.crypto import verify_secret
from studio_api.db import get_db
from studio_api.errors import APIError
from studio_api.models import ApiKey, User, Workspace


@dataclass
class TenantCtx:
    workspace_id: uuid.UUID
    org_id: uuid.UUID
    user: User
    workspace_role: str | None
    via_api_key: bool = False


def _get_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


def get_optional_auth(
    request: Request,
    db: Session = Depends(get_db),
) -> AuthContext | None:
    bearer = _get_bearer_token(request)
    if bearer and bearer.startswith("stk_"):
        return _auth_from_api_key_header(db, bearer, workspace_id=None)

    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    user = get_user_for_session_token(db, token)
    if user is None:
        return None
    return AuthContext(user=user)


def require_auth(
    auth: AuthContext | None = Depends(get_optional_auth),
) -> AuthContext:
    if auth is None:
        raise APIError("unauthorized", "Authentication required", 401)
    return auth


def _auth_from_api_key_header(
    db: Session,
    bearer: str,
    workspace_id: uuid.UUID | None,
) -> AuthContext | None:
    settings = get_settings()
    prefix = bearer[:12] if len(bearer) >= 12 else bearer
    api_key = db.scalar(select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.revoked_at.is_(None)))
    if api_key is None:
        return None
    if not verify_secret(bearer, settings.session_secret, api_key.secret_hash):
        return None
    if workspace_id is not None and api_key.workspace_id != workspace_id:
        return None
    user = db.get(User, api_key.created_by_user_id)
    if user is None:
        return None
    return AuthContext(
        user=user,
        workspace_id=api_key.workspace_id,
        via_api_key=True,
    )


def api_key_workspace_mismatch(db: Session, bearer: str, workspace_id: uuid.UUID) -> bool:
    settings = get_settings()
    prefix = bearer[:12] if len(bearer) >= 12 else bearer
    api_key = db.scalar(select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.revoked_at.is_(None)))
    if api_key is None:
        return False
    if not verify_secret(bearer, settings.session_secret, api_key.secret_hash):
        return False
    return api_key.workspace_id != workspace_id


def get_tenant_ctx(request: Request) -> TenantCtx | None:
    return getattr(request.state, "tenant_ctx", None)


def require_tenant_ctx(request: Request) -> TenantCtx:
    ctx = get_tenant_ctx(request)
    if ctx is None:
        raise APIError("not_found", "Workspace not found", 404)
    return ctx


def is_org_admin(user: User) -> bool:
    return user.org_role in {"owner", "admin"}


def workspace_role_rank(role: str) -> int:
    order = {"viewer": 1, "runner": 2, "editor": 3, "admin": 4, "owner": 5}
    return order.get(role, 0)


def require_workspace_role(ctx: TenantCtx, minimum: str) -> None:
    if is_org_admin(ctx.user):
        return
    if ctx.workspace_role is None:
        raise APIError("forbidden", "Insufficient permissions", 403)
    if workspace_role_rank(ctx.workspace_role) < workspace_role_rank(minimum):
        raise APIError("forbidden", "Insufficient permissions", 403)


def get_workspace_for_org(
    db: Session, workspace_id: uuid.UUID, org_id: uuid.UUID
) -> Workspace | None:
    return db.scalar(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.org_id == org_id)
    )
