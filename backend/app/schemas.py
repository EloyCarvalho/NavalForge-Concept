"""API-specific transport contracts."""

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


class ReportRequest(BaseModel):
    project: Project
    evaluation: dict[str, Any] | None = None
    format: Literal["pdf", "docx", "xlsx", "csv", "json"] = "pdf"


class ErrorResponse(BaseModel):
    detail: str
    error_code: str = Field(default="NAVALFORGE_ERROR")
