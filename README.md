# Agent Studio

M0 infrastructure bootstrap (IN-01 through IN-05). M2 / canvas work is frozen.

## Prerequisites

- Docker Engine with Compose v2
- Make
- Python 3.12 (local lint/unit)
- Node.js >= 22 (frontend milestones; pinned in `.nvmrc`)

## Quick start

```bash
cp .env.example .env
make up
```

`make up` builds and starts:

| Service | Purpose |
|---|---|
| `postgres` | Application database |
| `temporal` | Workflow orchestration |
| `minio` | Object storage stand-in (GCS in prod) |
| `vault` | Secret store stand-in (GCP SM in prod) |
| `api` | HTTP API (`GET /health`, `GET /ready`) |
| `studio-worker-ping` | Temporal ping worker (`PingWorkflow`) |

Verify:

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8080/ready
docker compose -f infra/compose/docker-compose.yml -p agent-studio ps
```

## Ping worker lifecycle

```bash
make ping-stop
make ping-start
```

See `infra/temporal/ping-restart.md` and `infra/temporal/README.md` (Update-With-Start Q9).

## Layout

```
apps/api/              FastAPI service
workers/adk/           Ping worker (google-adk + temporalio pins)
packages/vault/        Vault / GCP Secret Manager adapters
packages/object-store/ MinIO / GCS adapters
infra/compose/         Docker Compose stack
infra/temporal/        Temporal docs and runbooks
tests/m0/              Placeholder only (no Mazen harness in IN-01)
tests/unit/            Minimal unit tests
```

## CI

`.github/workflows/ci.yml` jobs: `compose-validate`, `lint`, `unit`, `ping-image`,
`m0-isolation`, `m0-ping-restart`, `m0-exit`, plus disabled `m1-*` placeholders.

## Origin port

This tree was bootstrapped from the M0-IN-01 spec. The Origin reference port
(`tmp-c9414a9f88f99c07`) was not accessible (403/auth); structure matches spec requirements.
