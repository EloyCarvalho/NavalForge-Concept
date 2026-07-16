#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[api,dev]'
PYTHONPATH=. python scripts/seed_examples.py
PYTHONPATH=. python scripts/sync_frontend_assets.py
(uvicorn backend.app.main:app --host 0.0.0.0 --port 8000) &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
