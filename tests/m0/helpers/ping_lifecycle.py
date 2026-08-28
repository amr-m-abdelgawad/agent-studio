from __future__ import annotations

import os
import shlex
import subprocess
import time


def run_shell_command(command: str, *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        shlex.split(command),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def stop_ping_worker() -> None:
    command = os.environ["PING_WORKER_STOP_CMD"]
    result = run_shell_command(command)
    assert result.returncode == 0, result.stderr or result.stdout


def start_ping_worker() -> None:
    command = os.environ["PING_WORKER_START_CMD"]
    result = run_shell_command(command)
    assert result.returncode == 0, result.stderr or result.stdout


def wait_for_worker_state(expected: str, *, attempts: int = 12, delay_seconds: float = 5.0) -> None:
    ps_cmd = (
        "docker compose -f infra/compose/docker-compose.yml -p agent-studio ps studio-worker-ping"
    )
    for _ in range(attempts):
        result = run_shell_command(ps_cmd)
        output = (result.stdout + result.stderr).lower()
        if expected == "stopped" and "exit" in output:
            return
        if expected == "running" and "up" in output:
            return
        time.sleep(delay_seconds)
    raise AssertionError(f"worker did not reach state {expected!r}: {result.stdout}")
