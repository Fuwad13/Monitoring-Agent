#!/usr/bin/env python3
"""
Celery worker startup script.
Run this to start the background task worker.

Usage:
    python scripts/worker.py

Environment Variables:
    WORKER_CONCURRENCY: Number of worker processes (default: 2)
    WORKER_LOGLEVEL: Logging level (default: info)
    WORKER_QUEUES: Comma-separated list of queues to process (default: all)
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
    """Start Celery worker"""

    # Get worker configuration from environment
    concurrency = os.getenv("WORKER_CONCURRENCY", "2")
    loglevel = os.getenv("WORKER_LOGLEVEL", "info")
    queues = os.getenv("WORKER_QUEUES", "default,monitoring,notifications,priority")

    logger.info("Starting Celery worker...")
    logger.info(f"Concurrency: {concurrency}")
    logger.info(f"Log level: {loglevel}")
    logger.info(f"Queues: {queues}")

    # Start the worker
    celery_app.worker_main(
        [
            "worker",
            f"--concurrency={concurrency}",
            f"--loglevel={loglevel}",
            f"--queues={queues}",
            "--without-gossip",
            "--without-mingle",
            "--without-heartbeat",
        ]
    )


if __name__ == "__main__":
    main()
