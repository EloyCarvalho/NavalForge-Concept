# NavalForge Concept 0.1.7 — editable project workspace

Release 0.1.7 converts the connected PWA from a read-only demonstration into an
editable, revisioned project workspace while preserving the three offline cases.

## Delivered

- create an editable project from any demonstrative vessel;
- persist the current project JSON in Neon PostgreSQL;
- preserve immutable P1, P2, … snapshots with date and change summary;
- reject stale saves instead of silently overwriting a newer revision;
- edit project identity, mission, principal dimensions and technical configuration;
- add, edit and remove classified requirements on Android;
- reopen an historical revision as a draft without deleting later history;
- delete a demonstrative project only after an explicit confirmation;
- save and automatically recalculate through the hosted engineering backend;
- generate PDF, DOCX, XLSX, CSV and JSON reports for persisted projects;
- retain offline demonstrations, the Y-up 3D viewer and mandatory requirement gate.

## Data and safety notice

The public workspace does not yet include user authentication or organization
isolation. It is a demonstrative environment: do not enter personal, commercial,
contractual or technically confidential information. Results remain preliminary
and do not represent statutory approval.

## Deployment order

1. Merge the 0.1.7 code and wait for the Render API to report version 0.1.7.
2. Confirm `/ready` returns HTTP 200 and the Neon database is reachable.
3. Upload the generated `NavalForge-PWA-v0.1.7-PROJECTS.zip` to the existing
   Cloudflare Pages project.
4. Open <https://navalforgeconcept.pages.dev>, confirm header v0.1.7, create a
   project, edit one value, save P2 and verify **BACKEND ONLINE**.

The engineering algorithm remains `navalforge-core-0.1.5`; this release changes
workflow, persistence and interface behavior rather than the calculation method.
