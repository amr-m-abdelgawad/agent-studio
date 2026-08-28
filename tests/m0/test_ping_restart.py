from __future__ import annotations

import time

import pytest

from tests.m0.helpers.ping_lifecycle import (
    start_ping_worker,
    stop_ping_worker,
    wait_for_worker_state,
)
from tests.m0.helpers.skips import requires_api, requires_ping_lifecycle

pytestmark = [pytest.mark.m0_ping_restart, requires_api, requires_ping_lifecycle]


def test_ping_survives_worker_restart(
    owner_client,
    workspace_a_id: str,
):
    before = owner_client.post(
        f"/v1/workspaces/{workspace_a_id}/debug/ping",
        json={"message": "before-restart", "delay_ms": 0},
    )
    assert before.status_code in (200, 202), before.text

    stop_ping_worker()
    wait_for_worker_state("stopped")

    during = owner_client.post(
        f"/v1/workspaces/{workspace_a_id}/debug/ping",
        json={"message": "during-stop", "delay_ms": 5000},
    )
    assert during.status_code in (200, 202), during.text
    assert isinstance(during.json, dict)
    workflow_id = during.json["workflow_id"]
    run_id = during.json["run_id"]

    start_ping_worker()
    wait_for_worker_state("running")

    deadline = time.time() + 120
    last_response = None
    while time.time() < deadline:
        last_response = owner_client.get(
            f"/v1/workspaces/{workspace_a_id}/debug/ping/{workflow_id}/runs/{run_id}",
        )
        if last_response.status_code == 200 and isinstance(last_response.json, dict):
            status = last_response.json.get("status")
            if status in ("completed", "COMPLETED", "succeeded", "SUCCEEDED"):
                break
        time.sleep(5)

    assert last_response is not None, "no poll response"
    assert last_response.status_code == 200, last_response.text
