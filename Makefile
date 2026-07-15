.PHONY: examples test frontend-build verify up down

examples:
	PYTHONPATH=. python scripts/seed_examples.py
	PYTHONPATH=. python scripts/sync_frontend_assets.py

test:
	PYTHONPATH=. python -m unittest discover -s tests -v

frontend-build:
	cd frontend && npm ci && npm run build

verify: examples test frontend-build
	PYTHONPATH=. python scripts/verify_project.py

up:
	docker compose up --build

down:
	docker compose down
