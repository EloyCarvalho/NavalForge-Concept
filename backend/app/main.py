"""NavalForge Concept REST API."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from navalforge_core.constants import ALGORITHM_VERSION
from navalforge_core.evaluator import evaluate_project
from navalforge_core.models import EvaluationResult, Project
from navalforge_core.propulsion import load_engine_database
from navalforge_core.reports import (
    export_csv,
    export_docx,
    export_json,
    export_pdf,
    export_xlsx,
)

from .config import get_settings
from .db import CalculationJobRecord, get_session, init_db
from .repository import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    RevisionConflictError,
    create_project,
    delete_project,
    get_project,
    get_project_revision,
    list_project_revisions,
    list_projects,
    save_job,
    save_project_revision,
)
from .schemas import (
    EvaluationRequest,
    HealthResponse,
    JobResponse,
    ProjectCreateRequest,
    ProjectListItem,
    ProjectRevisionItem,
    ProjectRevisionRequest,
    ProjectSaveResponse,
    ReportRequest,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("navalforge.api")
settings = get_settings()
SessionDep = Annotated[Session, Depends(get_session)]
ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info("NavalForge API %s started in %s", settings.app_version, settings.environment)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Audit-ready preliminary calculations for planing monohulls.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "health": "/health",
        "readiness": "/ready",
        "documentation": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        algorithm_version=ALGORITHM_VERSION,
    )


@app.get("/ready", response_model=HealthResponse, tags=["system"])
def readiness(session: SessionDep) -> HealthResponse:
    """Confirm both the API process and its database are ready."""

    session.execute(text("SELECT 1"))
    return health()


@app.get(f"{settings.api_prefix}/projects/demo", tags=["projects"])
def demo_projects() -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for path in sorted(EXAMPLES.glob("nf-demo-*.json")):
        projects.append(json.loads(path.read_text(encoding="utf-8")))
    return projects


@app.get(
    f"{settings.api_prefix}/projects",
    response_model=list[ProjectListItem],
    tags=["projects"],
)
def project_list(session: SessionDep) -> list[ProjectListItem]:
    records = list_projects(session)
    return [
        ProjectListItem(
            project_id=record.project_id,
            name=record.name,
            revision=record.revision,
            updated_at=record.updated_at,
        )
        for record in records
    ]


@app.post(
    f"{settings.api_prefix}/projects",
    response_model=ProjectSaveResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["projects"],
)
def project_create(payload: ProjectCreateRequest, session: SessionDep) -> ProjectSaveResponse:
    try:
        _, snapshot = create_project(
            session,
            payload.project,
            change_summary=payload.change_summary,
        )
    except ProjectAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Project ID already exists") from exc
    return ProjectSaveResponse(
        project=payload.project,
        revision=ProjectRevisionItem.model_validate(snapshot, from_attributes=True),
    )


@app.get(f"{settings.api_prefix}/projects/{{project_id}}", response_model=Project, tags=["projects"])
def project_get(project_id: str, session: SessionDep) -> Project:
    record = get_project(session, project_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project.model_validate(record.project_data)


@app.put(f"{settings.api_prefix}/projects/{{project_id}}", response_model=Project, tags=["projects"])
def project_put(
    project_id: str,
    project: Project,
    session: SessionDep,
) -> Project:
    if project_id != project.project_id:
        raise HTTPException(status_code=409, detail="Path and payload project IDs differ")
    record = get_project(session, project_id)
    if record is None:
        create_project(session, project, change_summary="Projeto criado pela rota legada")
        return project
    try:
        _, _, revised_project = save_project_revision(
            session,
            project,
            expected_revision=project.revision,
            change_summary="Atualização pela rota legada",
        )
    except RevisionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="Project changed in another session; reload before saving",
        ) from exc
    return revised_project


@app.post(
    f"{settings.api_prefix}/projects/{{project_id}}/revisions",
    response_model=ProjectSaveResponse,
    tags=["projects"],
)
def project_revision_create(
    project_id: str,
    payload: ProjectRevisionRequest,
    session: SessionDep,
) -> ProjectSaveResponse:
    if project_id != payload.project.project_id:
        raise HTTPException(status_code=409, detail="Path and payload project IDs differ")
    try:
        _, snapshot, revised_project = save_project_revision(
            session,
            payload.project,
            expected_revision=payload.expected_revision,
            change_summary=payload.change_summary,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except RevisionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="Project changed in another session; reload before saving",
        ) from exc
    return ProjectSaveResponse(
        project=revised_project,
        revision=ProjectRevisionItem.model_validate(snapshot, from_attributes=True),
    )


@app.get(
    f"{settings.api_prefix}/projects/{{project_id}}/revisions",
    response_model=list[ProjectRevisionItem],
    tags=["projects"],
)
def project_revision_list(
    project_id: str,
    session: SessionDep,
) -> list[ProjectRevisionItem]:
    if get_project(session, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return [
        ProjectRevisionItem.model_validate(record, from_attributes=True)
        for record in list_project_revisions(session, project_id)
    ]


@app.get(
    f"{settings.api_prefix}/projects/{{project_id}}/revisions/{{revision_id}}",
    response_model=Project,
    tags=["projects"],
)
def project_revision_get(
    project_id: str,
    revision_id: str,
    session: SessionDep,
) -> Project:
    record = get_project_revision(session, project_id, revision_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Project revision not found")
    return Project.model_validate(record.project_data)


@app.delete(
    f"{settings.api_prefix}/projects/{{project_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["projects"],
)
def project_delete(project_id: str, session: SessionDep) -> Response:
    if not delete_project(session, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(f"{settings.api_prefix}/evaluate", response_model=EvaluationResult, tags=["calculations"])
def evaluate(payload: EvaluationRequest) -> EvaluationResult:
    try:
        return evaluate_project(payload.project, include_variants=payload.include_variants)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Project evaluation failed")
        raise HTTPException(status_code=500, detail="Project evaluation failed; inspect API logs") from exc


@app.post(
    f"{settings.api_prefix}/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["jobs"],
)
def create_job(payload: EvaluationRequest, session: SessionDep) -> JobResponse:
    job_id = f"JOB-{uuid4().hex.upper()}"
    record = CalculationJobRecord(
        job_id=job_id,
        project_id=payload.project.project_id,
        status="running",
        request_data=payload.model_dump(mode="json"),
    )
    save_job(session, record)
    try:
        if settings.celery_enabled:
            from .tasks import evaluate_project_task

            evaluate_project_task.apply_async(
                args=[payload.project.model_dump(mode="json"), payload.include_variants],
                task_id=job_id,
            )
            record.status = "queued"
            record.result_data = None
        else:
            result = evaluate_project(
                payload.project, include_variants=payload.include_variants
            ).model_dump(mode="json")
            record.status = "completed"
            record.result_data = result
        session.commit()
    except Exception as exc:
        record.status = "failed"
        record.error = str(exc)
        session.commit()
    return JobResponse(
        job_id=record.job_id,
        project_id=record.project_id,
        status=record.status,
        result=record.result_data,
        error=record.error,
    )


@app.get(f"{settings.api_prefix}/jobs/{{job_id}}", response_model=JobResponse, tags=["jobs"])
def get_job(job_id: str, session: SessionDep) -> JobResponse:
    record = session.get(CalculationJobRecord, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if settings.celery_enabled and record.status in {"queued", "running"}:
        from .tasks import celery_app

        task = celery_app.AsyncResult(job_id)
        if task.state == "STARTED":
            record.status = "running"
        elif task.successful():
            record.status = "completed"
            record.result_data = task.result
        elif task.failed():
            record.status = "failed"
            record.error = str(task.result)
        session.commit()
    return JobResponse(
        job_id=record.job_id,
        project_id=record.project_id,
        status=record.status,
        result=record.result_data,
        error=record.error,
    )


@app.get(f"{settings.api_prefix}/engines", tags=["databases"])
def engines() -> list[dict[str, Any]]:
    return load_engine_database()


@app.post(f"{settings.api_prefix}/reports", tags=["reports"])
def report(payload: ReportRequest) -> FileResponse:
    result = (
        EvaluationResult.model_validate(payload.evaluation)
        if payload.evaluation
        else evaluate_project(payload.project, include_variants=True)
    )
    directory = Path(settings.storage_dir) / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{payload.project.project_id}-{uuid4().hex[:8]}.{payload.format}"
    exporters = {
        "pdf": lambda: export_pdf(payload.project, result, path),
        "docx": lambda: export_docx(payload.project, result, path),
        "xlsx": lambda: export_xlsx(result, path),
        "csv": lambda: export_csv(result, path),
        "json": lambda: export_json(result, path),
    }
    exporters[payload.format]()
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "json": "application/json",
    }
    return FileResponse(path, media_type=media_types[payload.format], filename=path.name)
