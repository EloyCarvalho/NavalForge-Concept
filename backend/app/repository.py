"""Database repository functions kept separate from route handling."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from navalforge_core.models import Project

from .db import CalculationJobRecord, ProjectRecord


def upsert_project(session: Session, project: Project) -> ProjectRecord:
    record = session.get(ProjectRecord, project.project_id)
    payload = project.model_dump(mode="json")
    if record is None:
        record = ProjectRecord(
            project_id=project.project_id,
            name=project.name,
            revision=project.revision,
            project_data=payload,
        )
        session.add(record)
    else:
        record.name = project.name
        record.revision = project.revision
        record.project_data = payload
    session.commit()
    session.refresh(record)
    return record


def list_projects(session: Session) -> list[ProjectRecord]:
    return list(session.scalars(select(ProjectRecord).order_by(ProjectRecord.updated_at.desc())))


def get_project(session: Session, project_id: str) -> ProjectRecord | None:
    return session.get(ProjectRecord, project_id)


def save_job(session: Session, record: CalculationJobRecord) -> CalculationJobRecord:
    session.add(record)
    session.commit()
    session.refresh(record)
    return record
