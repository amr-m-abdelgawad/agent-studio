from __future__ import annotations

import os
import shutil
import subprocess

import httpx
import pytest

REQUIRED_ROLES = ("owner", "admin", "editor", "viewer", "runner")


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def api_url() -> str | None:
    return _env("STUDIO_API_URL")


def web_url() -> str | None:
    return _env("STUDIO_WEB_URL")


def role_credentials(role: str) -> tuple[str, str] | None:
    email = _env(f"M0_{role.upper()}_EMAIL")
    password = _env(f"M0_{role.upper()}_PASSWORD")
    if email and password:
        return email, password
    return None


def api_reachable(url: str) -> bool:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{url.rstrip('/')}/health")
            return response.status_code < 500
    except Exception:
        return False


requires_api = pytest.mark.skipif(
    not api_url(),
    reason="STUDIO_API_URL is not set",
)

requires_web = pytest.mark.skipif(
    not web_url(),
    reason="STUDIO_WEB_URL is not set",
)

requires_role = {
    role: pytest.mark.skipif(
        role_credentials(role) is None,
        reason=f"M0_{role.upper()}_EMAIL and M0_{role.upper()}_PASSWORD are required",
    )
    for role in REQUIRED_ROLES
}


def ping_worker_commands_configured() -> bool:
    stop_cmd = _env("PING_WORKER_STOP_CMD")
    start_cmd = _env("PING_WORKER_START_CMD")
    return bool(stop_cmd and start_cmd)


def docker_available() -> bool:
    return shutil.which("docker") is not None


def compose_running() -> bool:
    if not docker_available():
        return False
    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                "infra/compose/docker-compose.yml",
                "-p",
                "agent-studio",
                "ps",
                "--status",
                "running",
                "-q",
                "studio-worker-ping",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


requires_ping_lifecycle = pytest.mark.skipif(
    not ping_worker_commands_configured(),
    reason="PING_WORKER_STOP_CMD and PING_WORKER_START_CMD are required",
)
