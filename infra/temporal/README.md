# Temporal in Agent Studio (M0)

## Namespace and task queue

| Setting | Value |
|---|---|
| Namespace | `studio-dev` |
| Task queue | `studio-default` |
| Worker service | `studio-worker-ping` (compose) |

The ping worker registers `PingWorkflow` and `ping_activity`. Workflow arguments use
`PingWorkflowInput` only — never pass secrets in workflow or activity args.

## PingWorkflowInput

```python
@dataclass
class PingWorkflowInput:
    message: str
    sleep_seconds: int = 0
    tenant_id: str | None = None
```

When `tenant_id` is set, the workflow upserts the `TenantId` keyword search attribute.

## Q9 — Update-With-Start (standing workers)

Agent Studio uses **Update-With-Start** against **standing workers**, not Signal-With-Start.

| Pattern | Agent Studio choice |
|---|---|
| Signal-With-Start | Not used for agent runs |
| Update-With-Start | Preferred: start-or-attach workflow, then send update handler |

Rationale:

1. Standing workers on `studio-default` keep poll loops hot; no cold-start per request.
2. Update handlers provide synchronous request/response semantics for agent turns.
3. Signal-With-Start defers handler registration and complicates idempotency for M1+ agent sessions.

M1+ services will call `client.start_update_with_start_workflow(...)` (exact API TBD in M1) with
workflow id derived from tenant/session keys. M0 only ships the ping worker to validate the
Temporal stack and worker lifecycle.

## Worker lifecycle

See `ping-restart.md` for stop/start commands used by `make ping-stop` and `make ping-start`.

Environment variables (also in `.env.example`):

```bash
PING_WORKER_STOP_CMD=docker compose -f infra/compose/docker-compose.yml -p agent-studio stop studio-worker-ping
PING_WORKER_START_CMD=docker compose -f infra/compose/docker-compose.yml -p agent-studio start studio-worker-ping
```

## Dependency pins (workers/adk)

- Python 3.12
- `google-adk==2.8.0`
- `temporalio[google-adk]>=1.28.0`

CI fails if these drift (see `.github/workflows/ci.yml`).
