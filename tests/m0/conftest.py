from __future__ import annotations

import os

import pytest

from tests.m0.helpers.api_client import StudioApiClient
from tests.m0.helpers.auth import client_for_role
from tests.m0.helpers.skips import api_url, role_credentials


@pytest.fixture(scope="session")
def studio_api_url() -> str:
    url = api_url()
    if not url:
        pytest.skip("STUDIO_API_URL is not set")
    return url


@pytest.fixture(scope="session")
def workspace_a_id() -> str:
    workspace_id = os.environ.get("M0_WORKSPACE_A_ID", "").strip()
    if not workspace_id:
        pytest.skip("M0_WORKSPACE_A_ID is not set")
    return workspace_id


@pytest.fixture(scope="session")
def workspace_b_id() -> str:
    workspace_id = os.environ.get("M0_WORKSPACE_B_ID", "").strip()
    if not workspace_id:
        pytest.skip("M0_WORKSPACE_B_ID is not set")
    return workspace_id


@pytest.fixture(scope="session")
def owner_client(studio_api_url: str) -> StudioApiClient:
    creds = role_credentials("owner")
    if not creds:
        pytest.skip("M0_OWNER_EMAIL and M0_OWNER_PASSWORD are required")
    client, _token = client_for_role(studio_api_url, creds[0], creds[1])
    return client


@pytest.fixture(scope="session")
def admin_client(studio_api_url: str) -> StudioApiClient:
    creds = role_credentials("admin")
    if not creds:
        pytest.skip("M0_ADMIN_EMAIL and M0_ADMIN_PASSWORD are required")
    client, _token = client_for_role(studio_api_url, creds[0], creds[1])
    return client


@pytest.fixture(scope="session")
def editor_client(studio_api_url: str) -> StudioApiClient:
    creds = role_credentials("editor")
    if not creds:
        pytest.skip("M0_EDITOR_EMAIL and M0_EDITOR_PASSWORD are required")
    client, _token = client_for_role(studio_api_url, creds[0], creds[1])
    return client


@pytest.fixture(scope="session")
def viewer_client(studio_api_url: str) -> StudioApiClient:
    creds = role_credentials("viewer")
    if not creds:
        pytest.skip("M0_VIEWER_EMAIL and M0_VIEWER_PASSWORD are required")
    client, _token = client_for_role(studio_api_url, creds[0], creds[1])
    return client


@pytest.fixture(scope="session")
def runner_client(studio_api_url: str) -> StudioApiClient:
    creds = role_credentials("runner")
    if not creds:
        pytest.skip("M0_RUNNER_EMAIL and M0_RUNNER_PASSWORD are required")
    client, _token = client_for_role(studio_api_url, creds[0], creds[1])
    return client
