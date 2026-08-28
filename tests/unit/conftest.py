from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from studio_api.config import get_settings
from studio_api.db import init_db, reset_db_state
from studio_api.main import app
from studio_api.temporal.client import FakeTemporalClient, set_temporal_client


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    db_path = "test_studio.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("STUDIO_ORG_NAME", "Test Org")
    monkeypatch.setenv("BOOTSTRAP_OWNER_EMAIL", "owner@test.com")
    monkeypatch.setenv("BOOTSTRAP_OWNER_PASSWORD", "owner-password-12")
    monkeypatch.setenv("STUDIO_EMAIL_ADAPTER", "dev")
    monkeypatch.setenv("INVITE_TTL_HOURS", "168")
    monkeypatch.setenv("STUDIO_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_db_state()
    fake_temporal = FakeTemporalClient()
    set_temporal_client(fake_temporal)
    init_db()
    yield
    set_temporal_client(None)
    reset_db_state()
    get_settings.cache_clear()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def fake_temporal() -> FakeTemporalClient:
    from studio_api.temporal.client import get_temporal_client

    client = get_temporal_client()
    assert isinstance(client, FakeTemporalClient)
    return client


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def create_workspace(client: TestClient, name: str = "Main") -> dict:
    response = client.post("/v1/workspaces", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()
