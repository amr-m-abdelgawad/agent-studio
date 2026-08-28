from __future__ import annotations

import re
import uuid
from collections.abc import Generator

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from studio_api.auth.dependencies import (
    TenantCtx,
    _auth_from_api_key_header,
    api_key_workspace_mismatch,
    is_org_admin,
)
from studio_api.auth.session import SESSION_COOKIE, get_user_for_session_token
from studio_api.db import get_session_factory
from studio_api.errors import APIError, error_response
from studio_api.models import Workspace, WorkspaceMember

WORKSPACE_PATH_RE = re.compile(r"^/v1/workspaces/(?P<workspace_id>[0-9a-fA-F-]{36})(?:/|$)")


async def _apply_tenant_context(request: Request, db: Session) -> Response | None:
    match = WORKSPACE_PATH_RE.match(request.url.path)
    if not match:
        return None

    workspace_id = uuid.UUID(match.group("workspace_id"))
    auth_header = request.headers.get("Authorization")
    auth_ctx = None
    if auth_header and auth_header.startswith("Bearer stk_"):
        bearer = auth_header[7:].strip()
        auth_ctx = _auth_from_api_key_header(db, bearer, workspace_id)
        if auth_ctx is None:
            if api_key_workspace_mismatch(db, bearer, workspace_id):
                return error_response("not_found", "Workspace not found", 404)
            return error_response("unauthorized", "Invalid or revoked API key", 401)
    else:
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            user = get_user_for_session_token(db, token)
            if user is not None:
                from studio_api.auth.session import AuthContext

                auth_ctx = AuthContext(user=user)

    if auth_ctx is None:
        return error_response("unauthorized", "Authentication required", 401)

    user = auth_ctx.user
    workspace = db.scalar(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.org_id == user.org_id)
    )
    if workspace is None:
        return error_response("not_found", "Workspace not found", 404)

    membership = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    workspace_role = membership.role if membership else None
    if membership is None and not is_org_admin(user):
        return error_response("not_found", "Workspace not found", 404)

    if auth_ctx.via_api_key and auth_ctx.workspace_id != workspace_id:
        return error_response("not_found", "Workspace not found", 404)

    request.state.tenant_ctx = TenantCtx(
        workspace_id=workspace_id,
        org_id=workspace.org_id,
        user=user,
        workspace_role=workspace_role,
        via_api_key=auth_ctx.via_api_key,
    )
    return None


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        session = get_session_factory()()
        request.state.db = session
        try:
            tenant_error = await _apply_tenant_context(request, session)
            if tenant_error is not None:
                session.rollback()
                return tenant_error
            response = await call_next(request)
            session.commit()
            return response
        except APIError as exc:
            session.rollback()
            return error_response(exc.code, exc.message, exc.status_code)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_request_db(request: Request) -> Generator[Session, None, None]:
    if hasattr(request.state, "db") and request.state.db is not None:
        yield request.state.db
        return
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
