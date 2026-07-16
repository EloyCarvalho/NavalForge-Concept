"""API-specific transport contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from navalforge_core.models import Project


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    algorithm_version: str


class EvaluationRequest(BaseModel):
    project: Project
    include_variants: bool = True


class JobResponse(BaseModel):
    job_id: str
    project_id: str
    status: Literal["queued", "running", "completed", "failed"]
    result: dict[str, Any] | None = None
    error: str | None = None


class ProjectListItem(BaseModel):
    project_id: str
    name: str
    revision: str
    source: str = "database"
    updated_at: datetime | None = None


class ProjectCreateRequest(BaseModel):
    project: Project
    change_summary: str = Field(default="Projeto criado", max_length=500)


class ProjectRevisionRequest(BaseModel):
    project: Project
    expected_revision: str = Field(min_length=1, max_length=40)
    change_summary: str = Field(default="", max_length=500)


class ProjectRevisionItem(BaseModel):
    revision_id: str
    project_id: str
    revision: str
    change_summary: str
    created_at: datetime


class ProjectSaveResponse(BaseModel):
    project: Project
    revision: ProjectRevisionItem


class ReportRequest(BaseModel):
    project: Project
    evaluation: dict[str, Any] | None = None
    format: Literal["pdf", "docx", "xlsx", "csv", "json"] = "pdf"


class ErrorResponse(BaseModel):
    detail: str
    error_code: str = Field(default="NAVALFORGE_ERROR")
