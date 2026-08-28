from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from studio_api.models import AuditLog


def record_audit(
    db: Session,
    *,
    org_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: str,
    workspace_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        org_id=org_id,
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action=action,
        details=details or {},
    )
    db.add(entry)
    db.flush()
    return entry
