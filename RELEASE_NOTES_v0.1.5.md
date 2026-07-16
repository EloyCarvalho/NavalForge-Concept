# NavalForge Concept 0.1.5 — reconstructed release

This release replaces the temporary 0.1.4 workspace package that was removed
by automated maintenance. It was reconstructed as a reproducible repository.

## Verification completed on 15 July 2026

- 21/21 Python core and integration tests passed;
- all three synthetic projects passed their mandatory requirement gates;
- equilibrium residuals met configured mass and LCB/LCG tolerances;
- PDF, DOCX, XLSX, CSV and JSON reports generated for all three projects;
- TypeScript typecheck passed;
- ESLint passed with zero warnings;
- Vite production build passed;
- production service worker received all hashed JS/CSS assets;
- NPM production dependency audit reported zero vulnerabilities;
- real HTTP smoke test returned the app, demo JSON and PDF successfully;
- Python source compiled successfully;
- Docker Compose YAML and required service graph were parsed and verified.

## Environment-conditioned checks

The reconstruction container did not include Docker, FastAPI, SQLAlchemy,
Alembic or Celery and could not access the Python package index. Therefore the
actual Docker images and live FastAPI process were not started in that
container. Dependencies, Dockerfiles, Compose graph, migrations and Python
syntax are included for execution in a normal Docker-enabled environment.

## Demonstration results

| Project | Displacement | GM corrected | Range | Gate |
|---|---:|---:|---:|---|
| Service 7 m | 2,675.5 kg | 0.479 m | 128.7 nmi | mandatory pass with reservations |
| Patrol 10 m | 7,915.7 kg | 0.627 m | 510.3 nmi | mandatory pass with reservations |
| Rescue 12 m | 14,569.3 kg | 0.710 m | 557.6 nmi | mandatory pass with reservations |

These values are synthetic software demonstrations, not validated vessel data.

## Important fixes

- native Three.js Y-up geometry: no upside-down hull correction rotation;
- ISO, side, bow and top camera presets;
- API content-type and status checks prevent HTML/404 responses being parsed as JSON;
- explicit offline fallback, cache version and release indicator;
- mandatory requirement failures remain unmaskable by aggregate scores.
