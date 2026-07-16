# NavalForge Concept 0.1.6 — live backend release

Release date: 2026-07-16

## Outcome

The installable PWA now calls the public FastAPI service on Render and uses the
Neon PostgreSQL database. The three generated demonstration results remain
available as an explicit offline fallback.

Public endpoints:

- PWA: <https://navalforgeconcept.pages.dev>
- API: <https://navalforge-concept-api.onrender.com>
- database-aware readiness: <https://navalforge-concept-api.onrender.com/ready>
- OpenAPI documentation: <https://navalforge-concept-api.onrender.com/docs>

## What changed

- `VITE_API_URL` is embedded in the Cloudflare distribution;
- **Executar projeto** sends the selected project to `/api/v1/evaluate`;
- a successful response changes the interface seal to **BACKEND ONLINE**;
- network, CORS or backend failures fall back to the named offline result;
- app/API/package and service-worker cache are versioned as 0.1.6;
- the calculation method is unchanged and remains identified as
  `navalforge-core-0.1.5`;
- public deployment and Android update instructions are documented.

## Verification evidence

- 25 Python tests passed with 92.14% coverage;
- Ruff, TypeScript and ESLint passed;
- Vite production build passed with the Render URL embedded;
- Docker Compose parsed successfully;
- the API image built and passed `/health` and `/ready` in a container;
- the live Render/Neon readiness check passed;
- CORS accepts `https://navalforgeconcept.pages.dev` and the legacy
  `https://navalforge3d14.pages.dev` origin;
- the live API evaluated `NF-DEMO-SERVICE-7M`, generated 9 variants, passed the
  mandatory gate and returned NF-ECO, NF-BALANCED and NF-PERFORMANCE;
- the production dependency audit reported zero vulnerabilities;
- the Cloudflare ZIP passed its integrity test.

Artifact:

- `NavalForge-PWA-v0.1.6-LIVE.zip`
- size: 1,986,192 bytes
- SHA-256: `9d4d3e893983bfde05f489ccd06d8976f55b0d0cce66d5539448cf995d5fa63d`

## Publish on Cloudflare from Android

1. Open the existing `navalforge3d14` Pages project.
2. Choose **Deployments**, the overflow menu and **Create deployment**.
3. Keep **Production** selected.
4. Upload `NavalForge-PWA-v0.1.6-LIVE.zip` and choose **Save and deploy**.
5. Open <https://navalforgeconcept.pages.dev> and confirm the header shows v0.1.6.
6. Select a project and touch **Executar projeto**; wait for **BACKEND ONLINE**.

The first request can take longer when the free Render service is sleeping.
If Android keeps the prior package, uninstall the old PWA and clear the stored
site data for the previous Pages domain before reinstalling.

## Technical limitations

This is a free public demonstration without authentication or an SLA. Do not
upload confidential customer data. Calculations, structural estimates, GZ and
planing predictions are preliminary and do not replace the responsible
engineer, validated input data, detailed analysis, statutory criteria,
classification approval or homologated software.
