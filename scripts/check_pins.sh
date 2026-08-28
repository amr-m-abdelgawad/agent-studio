#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "PIN CHECK FAILED: $1" >&2
  exit 1
}

echo "Checking Python pin (.python-version)..."
PY_VERSION="$(cat "$ROOT/.python-version" | tr -d '[:space:]')"
[[ "$PY_VERSION" == "3.12" ]] || fail "Expected Python 3.12, got $PY_VERSION"

echo "Checking Node pin (.nvmrc)..."
NODE_MAJOR="$(cat "$ROOT/.nvmrc" | tr -d '[:space:]')"
[[ "$NODE_MAJOR" -ge 22 ]] || fail "Expected Node >= 22, got $NODE_MAJOR"

echo "Checking google-adk pin (workers/adk/pyproject.toml)..."
grep -q 'google-adk==2.8.0' "$ROOT/workers/adk/pyproject.toml" \
  || fail "google-adk must be pinned to ==2.8.0"

echo "Checking temporalio[google-adk] pin (workers/adk/pyproject.toml)..."
grep -q 'temporalio\[google-adk\]>=1.28.0' "$ROOT/workers/adk/pyproject.toml" \
  || fail "temporalio[google-adk] must be >=1.28.0"

echo "All pin checks passed."
