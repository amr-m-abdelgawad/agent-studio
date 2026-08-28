from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from studio_api.auth.session import SESSION_COOKIE, create_session
from studio_api.config import get_settings
from studio_api.db import get_db
from studio_api.errors import APIError
from studio_api.models import User
from studio_api.passwords import verify_password
from studio_api.routers.me import build_me_response
from studio_api.schemas import AcceptInviteRequest, LoginRequest, MeResponse
from studio_api.services.audit import record_audit
from studio_api.services.invites import accept_invite

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=settings.studio_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/login", response_model=MeResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> MeResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise APIError("invalid_credentials", "Invalid email or password", 401)

    token = create_session(db, user)
    record_audit(
        db,
        org_id=user.org_id,
        actor_user_id=user.id,
        action="login",
        details={"email": user.email},
    )
    db.commit()
    _set_session_cookie(response, token)
    return build_me_response(db, user)


@router.post("/accept-invite", response_model=MeResponse, status_code=201)
def accept_invite_endpoint(
    body: AcceptInviteRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> MeResponse:
    user = accept_invite(db, body.token, body.password)
    token = create_session(db, user)
    db.commit()
    _set_session_cookie(response, token)
    return build_me_response(db, user)
