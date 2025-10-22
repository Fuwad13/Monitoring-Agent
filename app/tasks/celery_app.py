"""
Celery application configuration for background task processing.
"""

from celery import Celery
from kombu import Queue

from app.core.config import settings
from app.core.log import get_logger

logger = get_logger(__name__, settings.LOG_FILE_PATH)

# Create Celery instance
celery_app = Celery(
    "monitoring_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.monitoring",
        "app.tasks.notifications",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,  # 1 hour
    timezone="UTC",
    enable_utc=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Task routing
    task_routes={
        "app.tasks.monitoring.*": {"queue": "monitoring"},
        "app.tasks.notifications.*": {"queue": "notifications"},
    },
    # Queue definitions
    task_default_queue="default",
    task_queues=(
        Queue("default"),
        Queue("monitoring", routing_key="monitoring"),
        Queue("notifications", routing_key="notifications"),
        Queue("priority", routing_key="priority"),
    ),
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        "process-monitoring-targets": {
            "task": "app.tasks.monitoring.process_all_targets",
            "schedule": 60.0,  # Run every minute
            "options": {"queue": "monitoring"},
        },
        "cleanup-old-snapshots": {
            "task": "app.tasks.monitoring.cleanup_old_snapshots",
            "schedule": 86400.0,  # Run daily
            "options": {"queue": "monitoring"},
        },
    },
)

# Task autodiscovery
celery_app.autodiscover_tasks()

logger.info("Celery app configured successfully")


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    logger.info(f"Request: {self.request!r}")
    return f"Debug task executed: {self.request.id}"


# Health check task
@celery_app.task
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "message": "Celery is running"}
