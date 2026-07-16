"""Database repository functions kept separate from route handling."""

from __future__ import annotations

import re
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from navalforge_core.models import Project

from .db import CalculationJobRecord, ProjectRecord, ProjectRevisionRecord


class ProjectAlreadyExistsError(ValueError):
    """Raised when a create request reuses an existing project ID."""


class ProjectNotFoundError(ValueError):
    """Raised when a project cannot be found for a revision operation."""


class RevisionConflictError(ValueError):
    """Raised when a stale client tries to overwrite a newer revision."""


_REVISION_PATTERN = re.compile(r"^(?P<prefix>[A-Za-z]+)(?P<number>\d+)$")


def next_revision(current: str) -> str:
    """Increment a human-readable revision while preserving its prefix."""

    match = _REVISION_PATTERN.fullmatch(current.strip())
    if match is None:
        return "P2"
    return f"{match.group('prefix').upper()}{int(match.group('number')) + 1}"


def _snapshot(
    session: Session,
    *,
    project: Project,
    change_summary: str,
) -> ProjectRevisionRecord:
    snapshot = ProjectRevisionRecord(
        revision_id=f"REV-{uuid4().hex.upper()}",
        project_id=project.project_id,
        revision=project.revision,
        change_summary=change_summary.strip() or "Revisão salva pelo usuário",
        project_data=project.model_dump(mode="json"),
    )
    session.add(snapshot)
    return snapshot


def create_project(
    session: Session,
    project: Project,
    change_summary: str = "Projeto criado",
) -> tuple[ProjectRecord, ProjectRevisionRecord]:
    """Create a project and its first immutable revision."""

    if session.get(ProjectRecord, project.project_id) is not None:
        raise ProjectAlreadyExistsError(project.project_id)
    payload = project.model_dump(mode="json")
    record = ProjectRecord(
        project_id=project.project_id,
        name=project.name,
        revision=project.revision,
        project_data=payload,
    )
    session.add(record)
    snapshot = _snapshot(session, project=project, change_summary=change_summary)
    session.commit()
    session.refresh(record)
    session.refresh(snapshot)
    return record, snapshot


def save_project_revision(
    session: Session,
    project: Project,
    expected_revision: str,
    change_summary: str = "",
) -> tuple[ProjectRecord, ProjectRevisionRecord, Project]:
    """Save a new revision using optimistic concurrency control."""

    record = session.scalar(
        select(ProjectRecord)
        .where(ProjectRecord.project_id == project.project_id)
        .with_for_update()
    )
    if record is None:
        raise ProjectNotFoundError(project.project_id)
    if record.revision != expected_revision:
        raise RevisionConflictError(
            f"Expected {expected_revision}, but current revision is {record.revision}"
        )

    existing_snapshots = session.scalar(
        select(ProjectRevisionRecord.revision_id)
        .where(ProjectRevisionRecord.project_id == project.project_id)
        .limit(1)
    )
    if existing_snapshots is None:
        current_project = Project.model_validate(record.project_data)
        _snapshot(
            session,
            project=current_project,
            change_summary="Revisão importada antes da primeira alteração",
        )

    revision = next_revision(record.revision)
    revised_requirements = [
        requirement.model_copy(update={"revision": revision})
        for requirement in project.requirements
    ]
    revised_project = project.model_copy(
        update={"revision": revision, "requirements": revised_requirements}
    )
    record.name = revised_project.name
    record.revision = revision
    record.project_data = revised_project.model_dump(mode="json")
    snapshot = _snapshot(
        session,
        project=revised_project,
        change_summary=change_summary,
    )
    session.commit()
    session.refresh(record)
    session.refresh(snapshot)
    return record, snapshot, revised_project


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


def list_project_revisions(session: Session, project_id: str) -> list[ProjectRevisionRecord]:
    return list(
        session.scalars(
            select(ProjectRevisionRecord)
            .where(ProjectRevisionRecord.project_id == project_id)
            .order_by(ProjectRevisionRecord.created_at.desc())
        )
    )


def get_project_revision(
    session: Session,
    project_id: str,
    revision_id: str,
) -> ProjectRevisionRecord | None:
    return session.scalar(
        select(ProjectRevisionRecord).where(
            ProjectRevisionRecord.project_id == project_id,
            ProjectRevisionRecord.revision_id == revision_id,
        )
    )


def delete_project(session: Session, project_id: str) -> bool:
    """Delete a project and every immutable snapshot belonging to it."""

    record = session.get(ProjectRecord, project_id)
    if record is None:
        return False
    session.execute(
        delete(ProjectRevisionRecord).where(ProjectRevisionRecord.project_id == project_id)
    )
    session.delete(record)
    session.commit()
    return True


def save_job(session: Session, record: CalculationJobRecord) -> CalculationJobRecord:
    session.add(record)
    session.commit()
    session.refresh(record)
    return record
