#!/usr/bin/env python3
"""
Celery beat scheduler startup script.
Run this to start the periodic task scheduler.

Usage:
    python scripts/scheduler.py

This will start Celery beat which handles:
- Periodic target monitoring
- Snapshot cleanup
- Other scheduled maintenance tasks
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.tasks.celery_app import celery_app
from app.core.log import get_logger
from app.core.config import settings

logger = get_logger(__name__, settings.LOG_FILE_PATH)


def main():
    """Start Celery beat scheduler"""

    # Create temp directory for Windows compatibility
    temp_dir = project_root / "temp"
    temp_dir.mkdir(exist_ok=True)

    # Get scheduler configuration from environment with Windows-compatible defaults
    loglevel = os.getenv("SCHEDULER_LOGLEVEL", "info")
    pidfile = os.getenv("SCHEDULER_PIDFILE", str(temp_dir / "celerybeat.pid"))
    schedule_file = os.getenv(
        "SCHEDULER_SCHEDULE_FILE", str(temp_dir / "celerybeat-schedule")
    )

    logger.info("Starting Celery beat scheduler...")
    logger.info(f"Log level: {loglevel}")
    logger.info(f"PID file: {pidfile}")
    logger.info(f"Schedule file: {schedule_file}")

    # Start the scheduler
    celery_app.start(
        [
            "beat",
            f"--loglevel={loglevel}",
            f"--pidfile={pidfile}",
            f"--schedule={schedule_file}",
        ]
    )


if __name__ == "__main__":
    main()
