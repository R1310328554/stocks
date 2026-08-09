#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d backend/.venv ]]; then
  python3 -m venv backend/.venv
  # shellcheck disable=SC1091
  source backend/.venv/bin/activate
  pip install -U pip
  pip install -r backend/requirements.txt
else
  # shellcheck disable=SC1091
  source backend/.venv/bin/activate
fi

export DATA_MODE="${DATA_MODE:-demo}"
export ENABLE_SCHEDULER="${ENABLE_SCHEDULER:-true}"

cd "$ROOT/backend"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload