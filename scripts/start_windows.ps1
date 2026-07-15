$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
py -3.12 -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[api,dev]"
$env:PYTHONPATH = "."
python scripts\seed_examples.py
python scripts\sync_frontend_assets.py
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\Activate.ps1; uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
Set-Location frontend
npm install
$env:VITE_API_URL = "http://localhost:8000"
npm run dev
