.PHONY: up down logs ping-stop ping-start compose-validate lint unit m0-exit m0-isolation m0-ping-restart

COMPOSE_FILE := infra/compose/docker-compose.yml
COMPOSE_PROJECT := agent-studio
COMPOSE := docker compose -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT)
PING_WORKER_STOP_CMD ?= docker compose -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT) stop studio-worker-ping
PING_WORKER_START_CMD ?= docker compose -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT) start studio-worker-ping
export PING_WORKER_STOP_CMD
export PING_WORKER_START_CMD

# Bring up Postgres, Temporal, MinIO, Vault, API, and the ping worker.
up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ping-stop:
	$(PING_WORKER_STOP_CMD)

ping-start:
	$(PING_WORKER_START_CMD)

compose-validate:
	$(COMPOSE) config --quiet

lint:
	ruff check apps packages workers
	ruff format --check apps packages workers

migrate:
	cd apps/api && alembic upgrade head

unit:
	python3 -m pytest tests/unit -q

m0-exit:
	bash tests/m0/check-m0-exit.sh
	python3 -m pytest tests/m0 -m m0_exit -q

m0-isolation:
	python3 -m pytest tests/m0 -m m0_isolation -q

m0-ping-restart:
	python3 -m pytest tests/m0 -m m0_ping_restart -q
