"""
Celery worker entry point
Run with: celery -A app.worker.celery_app worker --loglevel=info
"""
from app.core.celery_app import celery_app

__all__ = ['celery_app']