from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from studio_api.auth.dependencies import (
    AuthContext,
    is_org_admin,
    require_auth,
    workspace_role_rank,
)
from studio_api.db import get_db
from studio_api.errors import APIError
from studio_api.models import WORKSPACE_ROLES, User, Workspace, WorkspaceMember
from studio_api.schemas import (
    WorkspaceCreateRequest,
    WorkspaceMemberAddRequest,
    WorkspaceMemberPatchRequest,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)
from studio_api.services.audit import record_audit

router = APIRouter(prefix="/v1/workspaces", tags=["workspaces"])


def _workspace_response(
    db: Session,
    workspace: Workspace,
    viewer: User,
    *,
    include_members: bool = False,
) -> WorkspaceResponse:
    membership = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == viewer.id,
        )
    )
    role = membership.role if membership else None
    members = None
    if include_members:
        rows = db.execute(
            select(WorkspaceMember, User)
            .join(User, User.id == WorkspaceMember.user_id)
            .where(WorkspaceMember.workspace_id == workspace.id)
            .order_by(User.email)
        ).all()
        members = [
            WorkspaceMemberResponse(user_id=user.id, email=user.email, role=member.role)
            for member, user in rows
        ]
    return WorkspaceResponse(id=workspace.id, name=workspace.name, role=role, members=members)


def _get_workspace_or_404(db: Session, workspace_id: uuid.UUID, user: User) -> Workspace:
    workspace = db.scalar(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.org_id == user.org_id)
    )
    if workspace is None:
        raise APIError("not_found", "Workspace not found", 404)
    if not is_org_admin(user):
        membership = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user.id,
            )
        )
        if membership is None:
            raise APIError("not_found", "Workspace not found", 404)
    return workspace


def _requires_workspace_admin(actor_membership: WorkspaceMember | None) -> bool:
    return actor_membership is not None and workspace_role_rank(
        actor_membership.role
    ) >= workspace_role_rank("admin")


def _count_owners(db: Session, workspace_id: uuid.UUID) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.role == "owner")
        )
        or 0
    )


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    body: WorkspaceCreateRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    if auth.user.org_role not in {"owner", "admin"}:
        raise APIError("forbidden", "Insufficient permissions", 403)

    workspace = Workspace(org_id=auth.user.org_id, name=body.name)
    db.add(workspace)
    db.flush()
    db.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=auth.user.id,
            role="owner",
        )
    )
    db.commit()
    db.refresh(workspace)
    return _workspace_response(db, workspace, auth.user, include_members=True)


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[WorkspaceResponse]:
    if is_org_admin(auth.user):
        workspaces = db.scalars(
            select(Workspace).where(Workspace.org_id == auth.user.org_id).order_by(Workspace.name)
        ).all()
    else:
        workspaces = db.scalars(
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == auth.user.id, Workspace.org_id == auth.user.org_id)
            .order_by(Workspace.name)
        ).all()
    return [_workspace_response(db, ws, auth.user) for ws in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: uuid.UUID,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    workspace = _get_workspace_or_404(db, workspace_id, auth.user)
    return _workspace_response(db, workspace, auth.user, include_members=True)


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=201)
def add_workspace_member(
    workspace_id: uuid.UUID,
    body: WorkspaceMemberAddRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> WorkspaceMemberResponse:
    workspace = _get_workspace_or_404(db, workspace_id, auth.user)
    actor_membership = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == auth.user.id,
        )
    )
    if not is_org_admin(auth.user) and not _requires_workspace_admin(actor_membership):
        raise APIError("forbidden", "Insufficient permissions", 403)

    role = body.role.lower()
    if role not in WORKSPACE_ROLES:
        raise APIError("validation_error", "Invalid role", 422)
    if actor_membership and actor_membership.role == "editor" and role == "owner":
        raise APIError("forbidden", "Editors cannot assign owner role", 403)

    target_user = db.scalar(
        select(User).where(User.email == body.email.lower(), User.org_id == auth.user.org_id)
    )
    if target_user is None:
        raise APIError("not_found", "User not found in organization", 404)

    existing = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user.id,
        )
    )
    if existing is not None:
        raise APIError("conflict", "User is already a workspace member", 409)

    member = WorkspaceMember(workspace_id=workspace.id, user_id=target_user.id, role=role)
    db.add(member)
    record_audit(
        db,
        org_id=auth.user.org_id,
        workspace_id=workspace.id,
        actor_user_id=auth.user.id,
        action="role_change",
        details={"user_id": str(target_user.id), "role": role, "operation": "add"},
    )
    db.commit()
    return WorkspaceMemberResponse(user_id=target_user.id, email=target_user.email, role=role)


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
def patch_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    body: WorkspaceMemberPatchRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> WorkspaceMemberResponse:
    workspace = _get_workspace_or_404(db, workspace_id, auth.user)
    actor_membership = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == auth.user.id,
        )
    )
    if not is_org_admin(auth.user) and not _requires_workspace_admin(actor_membership):
        raise APIError("forbidden", "Insufficient permissions", 403)

    role = body.role.lower()
    if role not in WORKSPACE_ROLES:
        raise APIError("validation_error", "Invalid role", 422)
    if actor_membership and actor_membership.role == "editor" and role == "owner":
        raise APIError("forbidden", "Editors cannot assign owner role", 403)

    member = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    if member is None:
        raise APIError("not_found", "Member not found", 404)

    if member.role == "owner" and role != "owner" and _count_owners(db, workspace_id) <= 1:
        raise APIError("forbidden", "Cannot remove the last workspace owner", 403)
    if actor_membership and actor_membership.role == "editor" and member.role == "owner":
        raise APIError("forbidden", "Editors cannot modify owner role", 403)

    old_role = member.role
    member.role = role
    target_user = db.get(User, user_id)
    record_audit(
        db,
        org_id=auth.user.org_id,
        workspace_id=workspace.id,
        actor_user_id=auth.user.id,
        action="role_change",
        details={"user_id": str(user_id), "from_role": old_role, "to_role": role},
    )
    db.commit()
    return WorkspaceMemberResponse(user_id=user_id, email=target_user.email, role=role)


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
def delete_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    workspace = _get_workspace_or_404(db, workspace_id, auth.user)
    actor_membership = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == auth.user.id,
        )
    )
    if not is_org_admin(auth.user) and not _requires_workspace_admin(actor_membership):
        raise APIError("forbidden", "Insufficient permissions", 403)

    member = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    if member is None:
        raise APIError("not_found", "Member not found", 404)
    if member.role == "owner" and _count_owners(db, workspace_id) <= 1:
        raise APIError("forbidden", "Cannot remove the last workspace owner", 403)

    db.delete(member)
    record_audit(
        db,
        org_id=auth.user.org_id,
        workspace_id=workspace.id,
        actor_user_id=auth.user.id,
        action="role_change",
        details={"user_id": str(user_id), "operation": "remove"},
    )
    db.commit()
