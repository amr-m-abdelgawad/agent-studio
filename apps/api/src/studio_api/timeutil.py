from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)
