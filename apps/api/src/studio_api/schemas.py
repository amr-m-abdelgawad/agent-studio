from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class OrgSummary(BaseModel):
    id: uuid.UUID
    name: str


class WorkspaceSummary(BaseModel):
    id: uuid.UUID
    name: str
    role: str


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    org: OrgSummary
    org_role: str
    workspaces: list[WorkspaceSummary] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(min_length=12)


class InviteRequest(BaseModel):
    email: EmailStr
    role: str


class InviteResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    status: str
    expires_at: str
    dev_token: str | None = None


class OkResponse(BaseModel):
    ok: bool = True


class WorkspaceCreateRequest(BaseModel):
    name: str


class WorkspaceMemberResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    role: str


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str | None = None
    members: list[WorkspaceMemberResponse] | None = None


class WorkspaceMemberAddRequest(BaseModel):
    email: EmailStr
    role: str


class WorkspaceMemberPatchRequest(BaseModel):
    role: str


class ApiKeyCreateRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    created_at: str
    secret: str | None = None


class AuditEntryResponse(BaseModel):
    id: uuid.UUID
    action: str
    actor_user_id: uuid.UUID
    workspace_id: uuid.UUID | None
    details: dict
    created_at: str


class PingStartResponse(BaseModel):
    workflow_id: str
    run_id: str


class PingStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    workspace_id: uuid.UUID
