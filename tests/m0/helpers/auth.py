from __future__ import annotations

import httpx

from tests.m0.helpers.api_client import StudioApiClient


def login(
    api: StudioApiClient,
    email: str,
    password: str,
) -> tuple[str, httpx.Cookies]:
    response = api.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json, dict), response.text
    session_name = response.json.get("session")
    assert session_name == "studio_session", response.text
    role = response.json.get("role")
    if role is not None:
        assert role == role.lower(), f"role must be lowercase, got {role!r}"
    token = response.json.get("access_token") or response.json.get("token")
    assert isinstance(token, str) and token, response.text
    return token, response.cookies


def client_for_role(base_url: str, email: str, password: str) -> tuple[StudioApiClient, str]:
    bootstrap = StudioApiClient(base_url)
    token, _cookies = login(bootstrap, email, password)
    return StudioApiClient(base_url, bearer_token=token), token
