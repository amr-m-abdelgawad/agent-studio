# Ping worker restart runbook (M0)

Use these commands to simulate worker loss and recovery without tearing down Postgres,
Temporal, or the API.

## Stop the ping worker

```bash
make ping-stop
```

Equivalent:

```bash
docker compose -f infra/compose/docker-compose.yml -p agent-studio stop studio-worker-ping
```

Or via env (used by Makefile):

```bash
eval "$(grep PING_WORKER_STOP_CMD .env.example)"
$PING_WORKER_STOP_CMD
```

## Start the ping worker

```bash
make ping-start
```

Equivalent:

```bash
docker compose -f infra/compose/docker-compose.yml -p agent-studio start studio-worker-ping
```

## Verify

1. `docker compose -f infra/compose/docker-compose.yml -p agent-studio ps studio-worker-ping`
   should show `Exit` after stop and `Up` after start.
2. Temporal UI (if exposed) or worker logs should show polling on `studio-default` after start.
3. M0 harness tests (when added by Mazen) will automate isolation/restart checks; until then
   `tests/m0/` remains a placeholder.

## Notes

- Do not pass secrets in `PingWorkflowInput` args.
- Namespace: `studio-dev`, task queue: `studio-default`.
- Other compose services stay running during ping worker restart.
