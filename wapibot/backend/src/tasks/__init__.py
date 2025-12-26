"""Celery application configuration.

Initializes Celery app with Redis broker and includes task modules.
"""

from celery import Celery

from core.config import settings

# Initialize Celery app
celery_app = Celery(
    "wapibot_payments",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Auto-discover tasks from included modules
celery_app.conf.include = [
    "tasks.reminder_tasks",
    "tasks.payment_tasks",
]

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit (graceful shutdown)
    worker_prefetch_multiplier=1,  # Prevent task hoarding
)
