import pytest

from tests.unit.conftest import create_workspace, login


def _invite_user(client, email: str, role: str, password: str) -> None:
    login(client, "owner@test.com", "owner-password-12")
    token = client.post("/v1/org/invites", json={"email": email, "role": role}).json()["dev_token"]
    client.post("/v1/auth/logout")
    client.post("/v1/auth/accept-invite", json={"token": token, "password": password})
    client.post("/v1/auth/logout")


def test_ping_returns_immediate_ids(client, fake_temporal):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "Ping")
    response = client.post(f"/v1/workspaces/{ws['id']}/debug/ping")
    assert response.status_code == 200
    body = response.json()
    assert body["workflow_id"]
    assert body["run_id"]
    assert len(fake_temporal.calls) == 1
    assert fake_temporal.calls[0]["message"] == "ping"
    assert fake_temporal.calls[0]["sleep_seconds"] == 0
    assert fake_temporal.calls[0]["tenant_id"] == ws["id"]


def test_cross_workspace_ping_status_is_404(client):
    login(client, "owner@test.com", "owner-password-12")
    ws1 = create_workspace(client, "Ping1")
    ws2 = create_workspace(client, "Ping2")
    started = client.post(f"/v1/workspaces/{ws1['id']}/debug/ping").json()
    response = client.get(f"/v1/workspaces/{ws2['id']}/debug/ping/{started['workflow_id']}")
    assert response.status_code == 404


def test_viewer_cannot_start_ping(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "PingViewer")
    _invite_user(client, "viewer-ping@test.com", "viewer", "viewer-ping-password")
    login(client, "owner@test.com", "owner-password-12")
    client.post(
        f"/v1/workspaces/{ws['id']}/members",
        json={"email": "viewer-ping@test.com", "role": "viewer"},
    )
    client.post("/v1/auth/logout")
    login(client, "viewer-ping@test.com", "viewer-ping-password")
    response = client.post(f"/v1/workspaces/{ws['id']}/debug/ping")
    assert response.status_code == 403


@pytest.mark.temporal
def test_live_temporal_ping():
    pytest.skip("Requires TEMPORAL_ADDRESS")
