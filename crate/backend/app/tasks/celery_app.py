"""Celery application configuration."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "crate",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # One task at a time (rate limit friendly)
)

celery_app.autodiscover_tasks(["app.tasks"])
