from __future__ import annotations

import pytest

from tests.m0.helpers.api_client import StudioApiClient, assert_error_contract
from tests.m0.helpers.skips import requires_api

pytestmark = [pytest.mark.m0_isolation, requires_api]


def test_owner_can_create_api_key_once(
    owner_client: StudioApiClient,
    workspace_a_id: str,
):
    response = owner_client.post(
        f"/v1/workspaces/{workspace_a_id}/api-keys",
        json={"name": "m0-harness-key"},
    )
    assert response.status_code in (200, 201), response.text
    assert isinstance(response.json, dict), response.text
    secret = response.json.get("secret") or response.json.get("key")
    assert isinstance(secret, str), response.text
    assert secret.startswith("stk_"), response.text

    key_id = response.json.get("id")
    if key_id:
        get_response = owner_client.get(f"/v1/workspaces/{workspace_a_id}/api-keys/{key_id}")
        assert get_response.status_code == 200, get_response.text
        if isinstance(get_response.json, dict):
            assert "secret" not in get_response.json
            assert "key" not in get_response.json


def test_editor_cannot_manage_api_keys(
    editor_client: StudioApiClient,
    workspace_a_id: str,
):
    response = editor_client.post(
        f"/v1/workspaces/{workspace_a_id}/api-keys",
        json={"name": "editor-forbidden"},
    )
    assert_error_contract(response, 403)


def test_revoked_api_key_returns_invalid_credentials(
    owner_client: StudioApiClient,
    studio_api_url: str,
    workspace_a_id: str,
):
    create = owner_client.post(
        f"/v1/workspaces/{workspace_a_id}/api-keys",
        json={"name": "m0-revoke-key"},
    )
    if create.status_code not in (200, 201):
        pytest.skip("API key creation not available in target environment")
    assert isinstance(create.json, dict)
    secret = create.json.get("secret") or create.json.get("key")
    key_id = create.json.get("id")
    assert isinstance(secret, str) and secret.startswith("stk_")
    assert key_id

    revoke = owner_client.delete(f"/v1/workspaces/{workspace_a_id}/api-keys/{key_id}")
    assert revoke.status_code in (200, 204), revoke.text

    revoked_client = StudioApiClient(studio_api_url, bearer_token=secret)
    denied = revoked_client.get(f"/v1/workspaces/{workspace_a_id}/agents")
    assert denied.status_code == 401, denied.text
    error = assert_error_contract(denied, 401)
    assert error["code"] == "invalid_credentials"


def test_viewer_can_read_audit_log(
    viewer_client: StudioApiClient,
    workspace_a_id: str,
):
    response = viewer_client.get(f"/v1/workspaces/{workspace_a_id}/audit-events")
    assert response.status_code == 200, response.text
    assert isinstance(response.json, list), response.text
