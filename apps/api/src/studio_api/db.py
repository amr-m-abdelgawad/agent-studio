from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from studio_api.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _session_factory


def get_db(request: Request) -> Generator[Session, None, None]:
    from studio_api.middleware.request import get_request_db

    yield from get_request_db(request)


def reset_db_state() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def init_db() -> None:
    from studio_api import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
