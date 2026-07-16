# Deployment

## Recommended public demonstration: Cloudflare + Render + Neon

This split keeps the installable PWA on Cloudflare Pages, runs FastAPI in a
Docker web service on Render and persists projects/jobs in Neon PostgreSQL.
Celery and Redis remain disabled in this first public deployment; `/api/v1/jobs`
still works synchronously. Enable a separate worker only when the workload
requires it.

### 1. Create the PostgreSQL database

1. Create a free project at <https://console.neon.tech> in AWS `us-east-1`.
2. Open **Connect**, select the pooled connection and copy its connection string.
3. Keep `sslmode=require` in the URL. Never commit this value to GitHub.

The API accepts the standard `postgresql://` URL returned by Neon and converts
it internally to SQLAlchemy's psycopg 3 dialect.

### 2. Deploy the API from GitHub

The root `render.yaml` is a Render Blueprint configured for the Virginia region,
the backend Dockerfile, `/ready` health checks and the production PWA origin.

1. Sign in at <https://dashboard.render.com> with GitHub.
2. Choose **New > Blueprint** and select `EloyCarvalho/NavalForge-Concept`.
3. Enter the Neon pooled URL when Render asks for `DATABASE_URL`.
4. Apply the Blueprint and wait for the service to report **Live**.
5. Verify `https://<service>.onrender.com/health`, `/ready` and `/docs`.

The current public API is <https://navalforge-concept-api.onrender.com>; its
database-aware readiness endpoint is
<https://navalforge-concept-api.onrender.com/ready>.

The free Render service can sleep after inactivity, so its first request can be
slow. Its filesystem is ephemeral; PostgreSQL data remains in Neon, while a
generated report file exists only long enough to be downloaded.

### 3. Connect the PWA

Rebuild the frontend with the exact Render origin (without a trailing slash):

```bash
cd frontend
npm ci
VITE_API_URL=https://navalforge-concept-api.onrender.com npm run build
```

Publish `frontend/dist` as a new Cloudflare Pages production deployment. The API
permits both `https://navalforgeconcept.pages.dev` and the legacy
`https://navalforge3d14.pages.dev` origin through CORS. If the PWA
domain changes, update `CORS_ORIGINS` in Render and redeploy.

### Production limitations of the free demonstration

- no authentication or confidential customer data;
- one web process and synchronous jobs, without Celery/Redis;
- cold start after Render inactivity;
- 0.5 GB Neon storage and provider free-tier quotas;
- generated files use ephemeral storage;
- no SLA, formal approval or normative validation.

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

Publish the contents of `frontend/dist`. The public 0.1.6 package uses
`https://navalforge-concept-api.onrender.com`; leave `VITE_API_URL` empty only
when intentionally building the offline demonstration. CORS must list the PWA
origin.

## Database migrations

```bash
alembic upgrade head
```

The API also creates missing tables on startup for the demonstrative deployment.
Use explicit Alembic migrations for controlled environments.
