from datetime import datetime, timezone
from typing import Dict
from beanie import Document
from pydantic import Field, EmailStr
from pymongo import IndexModel


class User(Document):
    """User model for authentication and preferences"""

    username: str = Field(..., unique=True, min_length=3, max_length=50)
    email: EmailStr = Field(..., unique=True)
    full_name: str = Field(..., min_length=1, max_length=100)
    password_hash: str
    is_active: bool = Field(default=True)
    preferences: Dict = Field(
        default_factory=lambda: {
            "notifications_enabled": True,
            "email_notifications": True,
            "email_on_changes": True,
            "email_on_insights": True,
            "email_summary": "weekly",  # daily, weekly, monthly, never
            "monitoring_frequency": 60,  # in minutes
            "min_importance_score": 5,  # Only notify for changes with score >= 5
        }
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", 1)], unique=True),
            IndexModel([("username", 1)], unique=True),
            IndexModel([("created_at", -1)]),
        ]
