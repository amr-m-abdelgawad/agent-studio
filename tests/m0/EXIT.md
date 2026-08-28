# M0 exit criteria

Use this checklist before declaring M0 complete. `tests/m0/check-m0-exit.sh` automates the
infra portions; API/UI contract coverage lives under `tests/m0/` pytest markers.

- Compose stack (`make up`) brings up Postgres, Temporal, MinIO, Vault, API, and `studio-worker-ping` with healthy probes.
- API exposes `GET /health` (200) and `GET /ready` (200 when dependencies are healthy, 503 otherwise).
- Ping worker registers on Temporal namespace `studio-dev` and task queue `studio-default` without leaking secrets in workflow args.
- `make ping-stop` / `make ping-start` (or `PING_WORKER_*` env commands) restart only the ping worker per `infra/temporal/ping-restart.md`.
- `/v1` identity contract: `studio_session` on login, lowercase roles, and `{error:{code,message}}` for failures.
- Workspace isolation: cross-workspace GET-by-id returns 404, mutations return 403, missing token returns 401; org Owner/Admin list all workspaces.
- API keys: `stk_` prefix shown once, Editor forbidden, audit log readable by Viewer+, Bearer tokens workspace-scoped, revoked keys return `401 invalid_credentials`.
- Debug ping: `POST/GET /v1/workspaces/{id}/debug/ping` returns immediate `{workflow_id, run_id}` for Owner/Admin/Editor, 403 for Viewer/Runner, 404 cross-workspace, optional `delay_ms`, no secrets in args.
- M0 harness CI jobs (`m0-isolation`, `m0-ping-restart`, `m0-exit`) run against `tests/m0` with markers `m0_isolation`, `m0_ping_restart`, and `m0_exit`.
