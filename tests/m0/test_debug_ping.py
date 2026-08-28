from __future__ import annotations

import pytest

from tests.m0.helpers.api_client import StudioApiClient, assert_error_contract
from tests.m0.helpers.skips import requires_api

pytestmark = [pytest.mark.m0_isolation, requires_api]

FORBIDDEN_ARG_KEYS = {"secret", "password", "token", "api_key", "vault_token"}


def _assert_ping_body(body: dict) -> tuple[str, str]:
    workflow_id = body.get("workflow_id")
    run_id = body.get("run_id")
    assert isinstance(workflow_id, str) and workflow_id, body
    assert isinstance(run_id, str) and run_id, body
    return workflow_id, run_id


def _assert_no_secrets(payload: dict) -> None:
    lowered = {key.lower() for key in payload}
    assert not lowered.intersection(FORBIDDEN_ARG_KEYS), payload


@pytest.mark.parametrize(
    "client_fixture",
    ["owner_client", "admin_client", "editor_client"],
)
def test_allowed_roles_can_trigger_debug_ping(
    request: pytest.FixtureRequest,
    client_fixture: str,
    workspace_a_id: str,
):
    client: StudioApiClient = request.getfixturevalue(client_fixture)
    response = client.post(
        f"/v1/workspaces/{workspace_a_id}/debug/ping",
        json={"message": "m0-harness", "delay_ms": 0},
    )
    assert response.status_code in (200, 202), response.text
    assert isinstance(response.json, dict), response.text
    _assert_no_secrets(response.json)
    _assert_ping_body(response.json)


@pytest.mark.parametrize(
    "client_fixture",
    ["viewer_client", "runner_client"],
)
def test_viewer_and_runner_cannot_trigger_debug_ping(
    request: pytest.FixtureRequest,
    client_fixture: str,
    workspace_a_id: str,
):
    client: StudioApiClient = request.getfixturevalue(client_fixture)
    response = client.post(
        f"/v1/workspaces/{workspace_a_id}/debug/ping",
        json={"message": "forbidden"},
    )
    assert_error_contract(response, 403)


def test_cross_workspace_debug_ping_returns_404(
    owner_client: StudioApiClient,
    workspace_b_id: str,
):
    response = owner_client.post(
        f"/v1/workspaces/{workspace_b_id}/debug/ping",
        json={"message": "cross-workspace"},
    )
    assert_error_contract(response, 404)


def test_debug_ping_get_by_run_id(
    owner_client: StudioApiClient,
    workspace_a_id: str,
):
    created = owner_client.post(
        f"/v1/workspaces/{workspace_a_id}/debug/ping",
        json={"message": "m0-get", "delay_ms": 0},
    )
    assert created.status_code in (200, 202), created.text
    assert isinstance(created.json, dict)
    workflow_id, run_id = _assert_ping_body(created.json)

    fetched = owner_client.get(
        f"/v1/workspaces/{workspace_a_id}/debug/ping/{workflow_id}/runs/{run_id}",
    )
    assert fetched.status_code == 200, fetched.text
    assert isinstance(fetched.json, dict), fetched.text
    _assert_ping_body(fetched.json)
