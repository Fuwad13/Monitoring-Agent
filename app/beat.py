"""
Celery beat scheduler entry point
Run with: celery -A app.beat.celery_app beat --loglevel=info
"""
from app.core.celery_app import celery_app

__all__ = ['celery_app']