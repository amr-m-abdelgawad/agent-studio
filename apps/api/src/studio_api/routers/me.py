from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from studio_api.auth.dependencies import AuthContext, require_auth
from studio_api.auth.session import SESSION_COOKIE, revoke_session
from studio_api.db import get_db
from studio_api.models import User, Workspace, WorkspaceMember
from studio_api.schemas import MeResponse, OkResponse, OrgSummary, WorkspaceSummary
from studio_api.services.audit import record_audit

router = APIRouter(tags=["me"])


def workspace_summaries_for_user(db: Session, user: User) -> list[WorkspaceSummary]:
    rows = db.execute(
        select(Workspace, WorkspaceMember)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id, Workspace.org_id == user.org_id)
        .order_by(Workspace.name)
    ).all()
    return [
        WorkspaceSummary(id=workspace.id, name=workspace.name, role=member.role)
        for workspace, member in rows
    ]


def build_me_response(db: Session, user: User) -> MeResponse:
    from studio_api.models import Organization

    org = db.get(Organization, user.org_id)
    return MeResponse(
        id=user.id,
        email=user.email,
        org=OrgSummary(id=org.id, name=org.name),
        org_role=user.org_role,
        workspaces=workspace_summaries_for_user(db, user),
    )


@router.get("/v1/me", response_model=MeResponse)
def get_me(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> MeResponse:
    return build_me_response(db, auth.user)


@router.post("/v1/auth/logout", response_model=OkResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> OkResponse:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        user = None
        from studio_api.auth.session import get_user_for_session_token

        user = get_user_for_session_token(db, token)
        revoke_session(db, token)
        if user is not None:
            record_audit(
                db,
                org_id=user.org_id,
                actor_user_id=user.id,
                action="logout",
                details={"email": user.email},
            )
        db.commit()
    _clear_session_cookie(response)
    return OkResponse(ok=True)


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path="/")
