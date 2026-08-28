.PHONY: up down logs ping-stop ping-start compose-validate lint unit

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

unit:
	pytest tests/unit -q
