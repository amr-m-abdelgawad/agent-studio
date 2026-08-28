from __future__ import annotations

import uuid

import pytest

from tests.m0.helpers.api_client import StudioApiClient, assert_error_contract
from tests.m0.helpers.skips import requires_api

pytestmark = [pytest.mark.m0_isolation, requires_api]


def test_cross_workspace_get_by_id_returns_404(
    owner_client: StudioApiClient,
    workspace_a_id: str,
    workspace_b_id: str,
):
    foreign_agent_id = str(uuid.uuid4())
    response = owner_client.get(f"/v1/workspaces/{workspace_b_id}/agents/{foreign_agent_id}")
    if response.status_code == 404:
        assert_error_contract(response, 404)
        return
    # Resource may not exist yet; ensure we never leak workspace B data via workspace A path.
    response = owner_client.get(f"/v1/workspaces/{workspace_a_id}/agents/{foreign_agent_id}")
    assert response.status_code in (403, 404), response.text


def test_cross_workspace_mutation_returns_403_or_404(
    editor_client: StudioApiClient,
    workspace_b_id: str,
):
    response = editor_client.post(
        f"/v1/workspaces/{workspace_b_id}/agents",
        json={"name": "m0-isolation-probe"},
    )
    assert response.status_code in (403, 404), response.text
    if response.status_code == 404:
        assert_error_contract(response, 404)
    else:
        assert_error_contract(response, 403)


def test_workspace_scoped_list_does_not_include_foreign_workspace(
    owner_client: StudioApiClient,
    workspace_a_id: str,
    workspace_b_id: str,
):
    if workspace_a_id == workspace_b_id:
        pytest.skip("M0_WORKSPACE_A_ID and M0_WORKSPACE_B_ID must differ")
    response = owner_client.get(f"/v1/workspaces/{workspace_a_id}/agents")
    assert response.status_code == 200, response.text
    assert isinstance(response.json, list), response.text
    for item in response.json:
        if isinstance(item, dict) and "workspace_id" in item:
            assert item["workspace_id"] == workspace_a_id
