#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

require_file() {
  if [[ ! -f "$1" ]]; then
    fail "missing required file: $1"
  fi
  pass "found $1"
}

require_file "infra/compose/docker-compose.yml"
require_file "infra/temporal/ping-restart.md"
require_file "tests/m0/EXIT.md"
require_file "Makefile"

if ! grep -q '^ping-stop:' Makefile; then
  fail "Makefile missing ping-stop target"
fi
if ! grep -q '^ping-start:' Makefile; then
  fail "Makefile missing ping-start target"
fi
pass "make ping-stop / ping-start targets present"

if ! grep -q 'PING_WORKER_STOP_CMD' .env.example; then
  fail ".env.example missing PING_WORKER_STOP_CMD"
fi
if ! grep -q 'PING_WORKER_START_CMD' .env.example; then
  fail ".env.example missing PING_WORKER_START_CMD"
fi
pass "ping worker lifecycle env defaults documented"

if command -v docker >/dev/null 2>&1; then
  docker compose -f infra/compose/docker-compose.yml config --quiet
  pass "compose file validates"
else
  pass "docker not available; skipped compose validate"
fi

bullet_count="$(grep -E '^- ' tests/m0/EXIT.md | wc -l | tr -d ' ')"
if [[ "$bullet_count" != "9" ]]; then
  fail "EXIT.md must contain exactly 9 bullets (found $bullet_count)"
fi
pass "EXIT.md contains 9 bullets"

if command -v docker >/dev/null 2>&1; then
  if docker compose -f infra/compose/docker-compose.yml -p agent-studio ps api 2>/dev/null | grep -qi 'up'; then
    if curl -fsS "http://localhost:8080/health" >/dev/null; then
      pass "API /health responds when compose api is up"
    else
      fail "API container is up but /health failed"
    fi
    ready_code="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/ready || true)"
    if [[ "$ready_code" == "200" || "$ready_code" == "503" ]]; then
      pass "API /ready responds with $ready_code"
    else
      fail "unexpected /ready status: $ready_code"
    fi
  else
    pass "compose api not running; skipped live health probes"
  fi
else
  pass "docker not available; skipped live health probes"
fi

pass "M0 exit infrastructure checks complete"
