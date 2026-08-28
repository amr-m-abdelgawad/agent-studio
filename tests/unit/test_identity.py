from sqlalchemy import select
from studio_api.db import get_session_factory
from studio_api.models import User

from tests.unit.conftest import login


def test_unauthenticated_me_is_401(client):
    response = client.get("/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_invalid_login_is_401(client):
    response = client.post(
        "/v1/auth/login",
        json={"email": "owner@test.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_logout_is_idempotent(client):
    login(client, "owner@test.com", "owner-password-12")
    first = client.post("/v1/auth/logout")
    second = client.post("/v1/auth/logout")
    assert first.status_code == 200
    assert second.status_code == 200
    assert client.get("/v1/me").status_code == 401


def test_owner_can_invite_and_accept(client):
    login(client, "owner@test.com", "owner-password-12")
    invite = client.post(
        "/v1/org/invites",
        json={"email": "editor@test.com", "role": "editor"},
    )
    assert invite.status_code == 201
    body = invite.json()
    assert body["dev_token"]
    assert "secret" not in body

    client.post("/v1/auth/logout")
    accepted = client.post(
        "/v1/auth/accept-invite",
        json={"token": body["dev_token"], "password": "editor-password"},
    )
    assert accepted.status_code == 201
    me = accepted.json()
    assert me["email"] == "editor@test.com"
    assert me["org_role"] == "editor"


def test_resend_pending_invite_rotates_token(client):
    login(client, "owner@test.com", "owner-password-12")
    first = client.post(
        "/v1/org/invites",
        json={"email": "viewer@test.com", "role": "viewer"},
    ).json()["dev_token"]
    second = client.post(
        "/v1/org/invites",
        json={"email": "viewer@test.com", "role": "viewer"},
    ).json()["dev_token"]
    assert first != second

    bad = client.post(
        "/v1/auth/accept-invite",
        json={"token": first, "password": "viewer-password"},
    )
    assert bad.status_code == 404

    good = client.post(
        "/v1/auth/accept-invite",
        json={"token": second, "password": "viewer-password"},
    )
    assert good.status_code == 201


def test_non_admin_cannot_invite(client):
    login(client, "owner@test.com", "owner-password-12")
    owner_invite = client.post(
        "/v1/org/invites",
        json={"email": "editor2@test.com", "role": "editor"},
    )
    token = owner_invite.json()["dev_token"]
    client.post(
        "/v1/auth/accept-invite",
        json={"token": token, "password": "editor2-password"},
    )
    client.post("/v1/auth/logout")
    login(client, "editor2@test.com", "editor2-password")
    denied = client.post(
        "/v1/org/invites",
        json={"email": "blocked@test.com", "role": "viewer"},
    )
    assert denied.status_code == 403


def test_password_too_short_on_accept(client):
    login(client, "owner@test.com", "owner-password-12")
    token = client.post(
        "/v1/org/invites",
        json={"email": "short@test.com", "role": "viewer"},
    ).json()["dev_token"]
    client.post("/v1/auth/logout")
    response = client.post(
        "/v1/auth/accept-invite",
        json={"token": token, "password": "short"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "password_too_short"


def test_expired_invite_returns_410(client, monkeypatch):
    login(client, "owner@test.com", "owner-password-12")
    token = client.post(
        "/v1/org/invites",
        json={"email": "expired@test.com", "role": "viewer"},
    ).json()["dev_token"]
    client.post("/v1/auth/logout")

    from datetime import timedelta

    from studio_api.models import Invite
    from studio_api.timeutil import utcnow

    db = get_session_factory()()
    invite = db.scalar(select(Invite).where(Invite.email == "expired@test.com"))
    invite.expires_at = utcnow() - timedelta(hours=1)
    db.commit()
    db.close()

    response = client.post(
        "/v1/auth/accept-invite",
        json={"token": token, "password": "expired-password"},
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "invite_expired"


def test_accepted_invite_returns_409(client):
    login(client, "owner@test.com", "owner-password-12")
    token = client.post(
        "/v1/org/invites",
        json={"email": "once@test.com", "role": "viewer"},
    ).json()["dev_token"]
    client.post("/v1/auth/logout")
    client.post(
        "/v1/auth/accept-invite",
        json={"token": token, "password": "once-password-1"},
    )
    client.post("/v1/auth/logout")
    again = client.post(
        "/v1/auth/accept-invite",
        json={"token": token, "password": "once-password-2"},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] in {"invite_used", "invite_already_accepted"}


def test_email_taken_blocks_new_invite(client):
    login(client, "owner@test.com", "owner-password-12")
    token = client.post(
        "/v1/org/invites",
        json={"email": "dup@test.com", "role": "viewer"},
    ).json()["dev_token"]
    client.post("/v1/auth/logout")
    client.post(
        "/v1/auth/accept-invite",
        json={"token": token, "password": "dup-password-1"},
    )
    client.post("/v1/auth/logout")

    login(client, "owner@test.com", "owner-password-12")
    response = client.post(
        "/v1/org/invites",
        json={"email": "dup@test.com", "role": "viewer"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


def test_passwords_use_argon2id(client):
    db = get_session_factory()()
    user = db.scalar(select(User).where(User.email == "owner@test.com"))
    assert user.password_hash.startswith("$argon2id$")
    db.close()
