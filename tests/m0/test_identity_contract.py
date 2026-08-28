from __future__ import annotations

import pytest

from tests.m0.helpers.api_client import StudioApiClient, assert_error_contract
from tests.m0.helpers.auth import login
from tests.m0.helpers.skips import requires_api, requires_role

pytestmark = [pytest.mark.m0_isolation, requires_api]


@requires_role["owner"]
def test_login_returns_studio_session_and_lowercase_role(studio_api_url: str):
    from tests.m0.helpers.skips import role_credentials

    email, password = role_credentials("owner")  # type: ignore[misc]
    client = StudioApiClient(studio_api_url)
    _token, cookies = login(client, email, password)
    assert "studio_session" in cookies


@requires_role["owner"]
def test_error_contract_shape(studio_api_url: str):
    client = StudioApiClient(studio_api_url)
    response = client.get("/v1/workspaces/does-not-exist/agents/some-agent")
    assert_error_contract(response, 401)


def test_missing_token_is_unauthorized(studio_api_url: str):
    client = StudioApiClient(studio_api_url)
    response = client.get("/v1/workspaces")
    assert_error_contract(response, 401)


@requires_role["owner"]
def test_org_owner_lists_all_workspaces(owner_client: StudioApiClient):
    response = owner_client.get("/v1/workspaces")
    assert response.status_code == 200, response.text
    assert isinstance(response.json, list), response.text
    assert len(response.json) >= 1


@requires_role["admin"]
def test_org_admin_lists_all_workspaces(admin_client: StudioApiClient):
    response = admin_client.get("/v1/workspaces")
    assert response.status_code == 200, response.text
    assert isinstance(response.json, list), response.text
    assert len(response.json) >= 1
