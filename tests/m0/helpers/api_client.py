from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ApiResponse:
    status_code: int
    json: dict[str, Any] | list[Any] | None
    headers: httpx.Headers
    cookies: httpx.Cookies
    text: str


class StudioApiClient:
    """Thin HTTP client for Samy's /v1 identity and workspace APIs."""

    def __init__(self, base_url: str, bearer_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if extra:
            headers.update(extra)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cookies: httpx.Cookies | None = None,
    ) -> ApiResponse:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=30.0, cookies=cookies or httpx.Cookies()) as client:
            response = client.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(headers),
            )
            try:
                body = response.json()
            except Exception:
                body = None
            return ApiResponse(
                status_code=response.status_code,
                json=body,
                headers=response.headers,
                cookies=response.cookies,
                text=response.text,
            )

    def get(self, path: str, **kwargs: Any) -> ApiResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> ApiResponse:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> ApiResponse:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> ApiResponse:
        return self.request("DELETE", path, **kwargs)


def assert_error_contract(response: ApiResponse, expected_status: int) -> dict[str, Any]:
    assert response.status_code == expected_status, response.text
    assert isinstance(response.json, dict), response.text
    assert "error" in response.json, response.text
    error = response.json["error"]
    assert isinstance(error, dict), response.text
    assert isinstance(error.get("code"), str), response.text
    assert isinstance(error.get("message"), str), response.text
    return error
