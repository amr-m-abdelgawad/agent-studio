from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from studio_api.auth.dependencies import AuthContext, is_org_admin, require_auth
from studio_api.db import get_db
from studio_api.errors import APIError
from studio_api.models import ORG_ROLES, Organization
from studio_api.schemas import InviteRequest, InviteResponse
from studio_api.services.invites import create_or_resend_invite

router = APIRouter(prefix="/v1/org", tags=["org"])


@router.post("/invites", response_model=InviteResponse, status_code=201)
def create_invite(
    body: InviteRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> InviteResponse:
    if not is_org_admin(auth.user):
        raise APIError("forbidden", "Only org owner or admin can invite", 403)

    role = body.role.lower()
    if role not in ORG_ROLES:
        raise APIError("validation_error", "Invalid role", 422)

    org = db.get(Organization, auth.user.org_id)
    if org is None:
        raise APIError("internal_error", "Organization missing", 500)

    invite, dev_token = create_or_resend_invite(
        db,
        org=org,
        inviter=auth.user,
        email=body.email,
        role=role,
    )
    db.commit()
    return InviteResponse(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        status=invite.status,
        expires_at=invite.expires_at.isoformat(),
        dev_token=dev_token,
    )
