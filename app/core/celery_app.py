import platform
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "monitoring_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.modules.monitoring.tasks"],
)

# Windows-specific configuration
if platform.system() == "Windows":
    celery_app.conf.update(
        worker_pool="solo",
        worker_concurrency=1,
    )

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-monitoring-targets": {
            "task": "app.modules.monitoring.tasks.check_all_targets",
            "schedule": 60.0,  # Run every 60 seconds
        },
    },
)
