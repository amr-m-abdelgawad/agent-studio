from tests.unit.conftest import create_workspace, login


def _invite_user(client, email: str, role: str, password: str) -> None:
    login(client, "owner@test.com", "owner-password-12")
    token = client.post("/v1/org/invites", json={"email": email, "role": role}).json()["dev_token"]
    client.post("/v1/auth/logout")
    client.post("/v1/auth/accept-invite", json={"token": token, "password": password})
    client.post("/v1/auth/logout")


def test_api_key_secret_only_on_create(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "Keys")
    created = client.post(f"/v1/workspaces/{ws['id']}/api-keys", json={"name": "ci"}).json()
    assert created["secret"].startswith("stk_")
    listed = client.get(f"/v1/workspaces/{ws['id']}/api-keys").json()
    assert all("secret" not in item or item.get("secret") is None for item in listed)


def test_bearer_auth_scoped_to_workspace(client):
    login(client, "owner@test.com", "owner-password-12")
    ws1 = create_workspace(client, "KeyWs1")
    ws2 = create_workspace(client, "KeyWs2")
    created = client.post(
        f"/v1/workspaces/{ws1['id']}/api-keys", json={"name": "one"}
    ).json()
    secret = created["secret"]
    client.post("/v1/auth/logout")

    ok = client.get(
        f"/v1/workspaces/{ws1['id']}/audit",
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert ok.status_code == 200

    cross = client.get(
        f"/v1/workspaces/{ws2['id']}/audit",
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert cross.status_code == 404


def test_revoked_api_key_returns_401(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "Revoke")
    created = client.post(f"/v1/workspaces/{ws['id']}/api-keys", json={"name": "rev"}).json()
    client.delete(f"/v1/workspaces/{ws['id']}/api-keys/{created['id']}")
    client.post("/v1/auth/logout")
    response = client.get(
        f"/v1/workspaces/{ws['id']}/audit",
        headers={"Authorization": f"Bearer {created['secret']}"},
    )
    assert response.status_code == 401


def test_editor_cannot_create_api_keys(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "EditorKeys")
    _invite_user(client, "editor-keys@test.com", "editor", "editor-keys-password")
    login(client, "owner@test.com", "owner-password-12")
    client.post(
        f"/v1/workspaces/{ws['id']}/members",
        json={"email": "editor-keys@test.com", "role": "editor"},
    )
    client.post("/v1/auth/logout")
    login(client, "editor-keys@test.com", "editor-keys-password")
    response = client.post(f"/v1/workspaces/{ws['id']}/api-keys", json={"name": "nope"})
    assert response.status_code == 403


def test_audit_records_role_change_and_login_events(client):
    login(client, "owner@test.com", "owner-password-12")
    ws = create_workspace(client, "Audit")
    _invite_user(client, "audit-viewer@test.com", "viewer", "audit-viewer-password")
    login(client, "owner@test.com", "owner-password-12")
    client.post(
        f"/v1/workspaces/{ws['id']}/members",
        json={"email": "audit-viewer@test.com", "role": "editor"},
    )
    actions = {entry["action"] for entry in client.get(f"/v1/workspaces/{ws['id']}/audit").json()}
    assert "role_change" in actions

    from sqlalchemy import select
    from studio_api.db import get_session_factory
    from studio_api.models import AuditLog

    db = get_session_factory()()
    login_count = db.scalar(select(AuditLog).where(AuditLog.action == "login"))
    assert login_count is not None
    db.close()
