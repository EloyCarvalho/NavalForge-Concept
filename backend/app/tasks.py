"""Celery calculation task with the same core evaluator used by the API."""

from celery import Celery

from navalforge_core.evaluator import evaluate_project
from navalforge_core.models import Project

from .config import get_settings


settings = get_settings()
celery_app = Celery(
    "navalforge",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
)


@celery_app.task(name="navalforge.evaluate_project")
def evaluate_project_task(project_data: dict, include_variants: bool = True) -> dict:
    project = Project.model_validate(project_data)
    return evaluate_project(project, include_variants=include_variants).model_dump(mode="json")
