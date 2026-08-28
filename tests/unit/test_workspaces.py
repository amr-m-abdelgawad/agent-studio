from tests.unit.conftest import create_workspace, login


def _invite_user(client, email: str, role: str, password: str) -> None:
    login(client, "owner@test.com", "owner-password-12")
    token = client.post("/v1/org/invites", json={"email": email, "role": role}).json()["dev_token"]
    client.post("/v1/auth/logout")
    client.post("/v1/auth/accept-invite", json={"token": token, "password": password})
    client.post("/v1/auth/logout")


def test_viewer_cannot_create_workspace(client):
    _invite_user(client, "viewer-ws@test.com", "viewer", "viewer-ws-password")
    login(client, "viewer-ws@test.com", "viewer-ws-password")
    response = client.post("/v1/workspaces", json={"name": "Blocked"})
    assert response.status_code == 403


def test_workspace_404_for_non_member(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "Private")
    _invite_user(client, "outsider@test.com", "editor", "outsider-password-1")
    login(client, "outsider@test.com", "outsider-password-1")
    response = client.get(f"/v1/workspaces/{ws['id']}")
    assert response.status_code == 404


def test_org_admin_can_get_any_workspace(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "AdminView")
    _invite_user(client, "admin-ws@test.com", "admin", "admin-ws-password-1")
    login(client, "admin-ws@test.com", "admin-ws-password-1")
    response = client.get(f"/v1/workspaces/{ws['id']}")
    assert response.status_code == 200
    assert response.json()["members"]


def test_editor_cannot_self_promote_to_owner(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "Promote")
    _invite_user(client, "editor-promote@test.com", "editor", "editor-promote-pass")
    login(client, "owner@test.com", "owner-password-12")
    client.post(
        f"/v1/workspaces/{ws['id']}/members",
        json={"email": "editor-promote@test.com", "role": "editor"},
    )
    client.post("/v1/auth/logout")
    login(client, "editor-promote@test.com", "editor-promote-pass")
    me = client.get("/v1/me").json()
    user_id = me["id"]
    response = client.patch(
        f"/v1/workspaces/{ws['id']}/members/{user_id}",
        json={"role": "owner"},
    )
    assert response.status_code == 403


def test_me_lists_workspaces(client):
    login(client, "owner@test.com", "owner-password-12")
    create_workspace(client, "One")
    me = client.get("/v1/me").json()
    assert any(ws["name"] == "One" for ws in me["workspaces"])
