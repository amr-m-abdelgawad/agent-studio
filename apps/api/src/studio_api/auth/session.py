from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from studio_api.config import get_settings
from studio_api.crypto import generate_token, hash_secret
from studio_api.models import Session as SessionModel
from studio_api.models import User
from studio_api.timeutil import utcnow

SESSION_COOKIE = "studio_session"
SESSION_TTL_DAYS = 30


@dataclass
class AuthContext:
    user: User
    workspace_id: uuid.UUID | None = None
    via_api_key: bool = False


def create_session(db: Session, user: User) -> str:
    settings = get_settings()
    token = generate_token()
    token_hash = hash_secret(token, settings.session_secret)
    expires_at = utcnow() + timedelta(days=SESSION_TTL_DAYS)
    session = SessionModel(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session)
    db.flush()
    return token


def revoke_session(db: Session, token: str) -> None:
    settings = get_settings()
    token_hash = hash_secret(token, settings.session_secret)
    session = db.scalar(
        select(SessionModel).where(
            SessionModel.token_hash == token_hash,
            SessionModel.revoked_at.is_(None),
        )
    )
    if session is not None:
        session.revoked_at = utcnow()


def get_user_for_session_token(db: Session, token: str) -> User | None:
    settings = get_settings()
    token_hash = hash_secret(token, settings.session_secret)
    now = utcnow()
    session = db.scalar(
        select(SessionModel)
        .where(
            SessionModel.token_hash == token_hash,
            SessionModel.revoked_at.is_(None),
            SessionModel.expires_at > now,
        )
        .limit(1)
    )
    if session is None:
        return None
    return db.get(User, session.user_id)
