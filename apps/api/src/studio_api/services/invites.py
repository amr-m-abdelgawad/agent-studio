from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from studio_api.config import get_settings
from studio_api.crypto import generate_token, hash_secret
from studio_api.errors import APIError
from studio_api.models import Invite, Organization, User
from studio_api.passwords import hash_password, validate_password_length
from studio_api.services.audit import record_audit
from studio_api.timeutil import utcnow


def bootstrap_org(db: Session) -> tuple[Organization, User] | None:
    settings = get_settings()
    if not settings.studio_org_name or not settings.bootstrap_owner_email:
        return None

    org = db.scalar(select(Organization).limit(1))
    if org is None:
        org = Organization(name=settings.studio_org_name)
        db.add(org)
        db.flush()

    user = db.scalar(select(User).where(User.email == settings.bootstrap_owner_email.lower()))
    if user is None:
        if not settings.bootstrap_owner_password:
            raise APIError("bootstrap_error", "BOOTSTRAP_OWNER_PASSWORD required", 500)
        validate_password_length(settings.bootstrap_owner_password)
        user = User(
            email=settings.bootstrap_owner_email.lower(),
            password_hash=hash_password(settings.bootstrap_owner_password),
            org_id=org.id,
            org_role="owner",
        )
        db.add(user)
        db.flush()

    return org, user


def create_or_resend_invite(
    db: Session,
    *,
    org: Organization,
    inviter: User,
    email: str,
    role: str,
) -> tuple[Invite, str | None]:
    settings = get_settings()
    email = email.lower()
    now = utcnow()
    expires_at = now + timedelta(hours=settings.invite_ttl_hours)

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise APIError("email_taken", "Email already registered", 409)

    invite = db.scalar(
        select(Invite).where(
            Invite.org_id == org.id,
            Invite.email == email,
            Invite.status == "pending",
        )
    )

    raw_token = generate_token()
    token_hash = hash_secret(raw_token, settings.session_secret)

    if invite is not None:
        invite.token_hash = token_hash
        invite.role = role
        invite.expires_at = expires_at
        invite.invited_by_user_id = inviter.id
    else:
        invite = Invite(
            org_id=org.id,
            email=email,
            role=role,
            token_hash=token_hash,
            invited_by_user_id=inviter.id,
            status="pending",
            expires_at=expires_at,
        )
        db.add(invite)

    db.flush()
    record_audit(
        db,
        org_id=org.id,
        actor_user_id=inviter.id,
        action="invite",
        details={"email": email, "role": role},
    )

    dev_token = raw_token if settings.studio_email_adapter == "dev" else None
    return invite, dev_token


def accept_invite(db: Session, token: str, password: str) -> User:
    settings = get_settings()
    validate_password_length(password)
    token_hash = hash_secret(token, settings.session_secret)
    now = utcnow()

    invite = db.scalar(select(Invite).where(Invite.token_hash == token_hash))
    if invite is None:
        raise APIError("invite_invalid", "Invite not found", 404)

    if invite.status == "accepted":
        raise APIError("invite_already_accepted", "Invite already accepted", 409)

    if invite.status != "pending":
        raise APIError("invite_used", "Invite already used", 409)

    if invite.expires_at <= now:
        invite.status = "expired"
        db.flush()
        raise APIError("invite_expired", "Invite has expired", 410)

    existing_user = db.scalar(select(User).where(User.email == invite.email))
    if existing_user is not None:
        raise APIError("email_taken", "Email already registered", 409)

    user = User(
        email=invite.email,
        password_hash=hash_password(password),
        org_id=invite.org_id,
        org_role=invite.role,
    )
    db.add(user)
    invite.status = "accepted"
    invite.accepted_at = now
    db.flush()
    return user
