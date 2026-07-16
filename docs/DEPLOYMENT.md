# Deployment

## Integrated Docker deployment

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
```

The stack contains PostgreSQL, Redis, FastAPI, a Celery worker and Nginx serving
the PWA. Nginx proxies same-origin `/api/` requests to the backend.

Change every default credential before exposing the stack. Put TLS and access
control in front of production deployments. Do not place confidential hull or
customer data in a public static deployment.

## Static PWA

```bash
cd frontend
npm ci
npm run build
```

Publish the contents of `frontend/dist`. Leave `VITE_API_URL` empty for the
offline demonstration. Set it to an HTTPS backend origin to enable live
calculations. CORS must list the PWA origin.

## Database migrations

```bash
alembic upgrade head
```

The API also creates missing tables on startup for the demonstrative deployment.
Use explicit Alembic migrations for controlled environments.
