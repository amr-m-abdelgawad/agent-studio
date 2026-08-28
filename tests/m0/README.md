# M0 QA harness

Contract and integration tests for Agent Studio M0. API tests target **Samy's** `/v1`
identity and workspace APIs via `STUDIO_API_URL` (those routes are not implemented in this
branch). Playwright UI tests target Alaa's web app via `STUDIO_WEB_URL`.

## Layout

```
tests/m0/
  EXIT.md                 # nine M0 exit bullets
  check-m0-exit.sh        # infra exit gate (compose, Makefile, EXIT.md)
  conftest.py             # shared fixtures
  helpers/                # API client, auth, ping lifecycle, skip guards
  test_identity_contract.py
  test_workspace_isolation.py
  test_api_keys.py
  test_debug_ping.py
  test_ping_restart.py
  test_ui_navigation.py
  test_exit.py
```

## Pytest markers

| Marker | CI job | Scope |
|---|---|---|
| `m0_isolation` | `m0-isolation` | Identity, RBAC, workspace isolation, API keys, audit, debug ping auth |
| `m0_ping_restart` | `m0-ping-restart` | Worker stop/start via `PING_WORKER_*` and ping recovery |
| `m0_exit` | `m0-exit` | EXIT.md + `check-m0-exit.sh` gate |

## Environment

| Variable | Purpose |
|---|---|
| `STUDIO_API_URL` | Base URL for Samy's API (required for API tests) |
| `STUDIO_WEB_URL` | Base URL for Alaa's web UI (required for Playwright) |
| `M0_WORKSPACE_A_ID` / `M0_WORKSPACE_B_ID` | Two distinct workspaces for isolation checks |
| `M0_OWNER_EMAIL` / `M0_OWNER_PASSWORD` | Org owner credentials |
| `M0_ADMIN_EMAIL` / `M0_ADMIN_PASSWORD` | Org admin credentials |
| `M0_EDITOR_EMAIL` / `M0_EDITOR_PASSWORD` | Workspace editor credentials |
| `M0_VIEWER_EMAIL` / `M0_VIEWER_PASSWORD` | Workspace viewer credentials |
| `M0_RUNNER_EMAIL` / `M0_RUNNER_PASSWORD` | Workspace runner credentials |
| `PING_WORKER_STOP_CMD` | Defaults to `make ping-stop` compose command |
| `PING_WORKER_START_CMD` | Defaults to `make ping-start` compose command |

Copy defaults from `.env.example` and export role/workspace values from your M0 seed data.

## Local commands

```bash
pip install -e ".[m0]"
playwright install chromium

# Infra exit gate only (no external API required)
bash tests/m0/check-m0-exit.sh
pytest tests/m0 -m m0_exit -q

# Full API contract suite (requires STUDIO_API_URL + role fixtures)
export STUDIO_API_URL=https://studio-api.example.com
pytest tests/m0 -m m0_isolation -q

# Ping restart (requires compose + STUDIO_API_URL + ping worker commands)
make up
export STUDIO_API_URL=https://studio-api.example.com
pytest tests/m0 -m m0_ping_restart -q

# UI navigation (requires STUDIO_WEB_URL + role fixtures)
export STUDIO_WEB_URL=https://studio.example.com
pytest tests/m0 -m m0_isolation tests/m0/test_ui_navigation.py -q
```

## Contracts exercised

- `/v1` identity: `studio_session`, lowercase roles, `{error:{code,message}}`
- Isolation: cross-workspace GET-by-id `404`, mutations `403`, missing token `401`; org Owner/Admin list all workspaces
- API keys: `stk_` prefix shown once; Editor `403`; audit Viewer+; Bearer workspace-scoped; revoked `401 invalid_credentials`
- Debug ping: `POST/GET /v1/workspaces/{id}/debug/ping` immediate `{workflow_id, run_id}`; Owner/Admin/Editor allowed; Viewer/Runner `403`; cross-workspace `404`; optional `delay_ms`; no secrets in args
- UI test ids: `login-email`, `login-password`, `login-submit`, `login-error`, `invite-password`, `invite-submit`, `invite-error`, `nav-agents`, `nav-runs`, `nav-invite`, `empty-agents`, `logout`, `workspace-switcher` (invite hidden for editor/viewer/runner)

## Out of scope

- Canvas / M2 features
- ADK spawn workflows beyond the ping worker
- Implementing Samy's API routes (tests only)

See `infra/temporal/ping-restart.md` for the worker restart runbook.
