from datetime import datetime, timezone
from typing import Optional, Dict
from beanie import Document
from pydantic import BaseModel, Field
from pymongo import IndexModel


class Target(Document):
    """Monitoring targets configuration"""

    url: str = Field(..., description="URL to monitor")
    target_type: str = Field(
        ..., description="Type: linkedin_profile, linkedin_company, website"
    )
    user_id: str = Field(..., description="Owner user ID")
    monitoring_frequency: int = Field(
        default=60, description="Check frequency in minutes"
    )
    last_checked: Optional[datetime] = Field(
        default=None, description="Last monitoring timestamp"
    )
    is_active: bool = Field(default=True, description="Whether monitoring is active")
    xpath_selectors: Optional[Dict[str, str]] = Field(
        default=None, description="Custom CSS/XPath selectors"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "targets"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("url", 1)]),
            IndexModel([("target_type", 1)]),
            IndexModel([("is_active", 1)]),
            IndexModel([("last_checked", 1)]),
        ]


class Snapshot(Document):
    """Content snapshots for comparison"""

    target_id: str = Field(..., description="Reference to Target document")
    content_hash: str = Field(..., description="SHA256 hash of content")
    raw_content: str = Field(..., description="Original scraped content")
    processed_content: Dict = Field(
        default_factory=dict, description="Structured/cleaned content"
    )
    metadata: Dict = Field(default_factory=dict, description="Headers, title, etc.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    size_bytes: int = Field(..., description="Content size in bytes")

    class Settings:
        name = "snapshots"
        indexes = [
            IndexModel([("target_id", 1)]),
            IndexModel([("timestamp", -1)]),
            IndexModel([("content_hash", 1)]),
            IndexModel([("target_id", 1), ("timestamp", -1)]),
        ]


class Change(Document):
    """Detected changes with analysis"""

    target_id: str = Field(..., description="Reference to Target document")
    change_type: str = Field(..., description="Type: major, minor, new_content")
    summary: str = Field(..., description="Human-readable change summary")
    diff_data: Dict = Field(
        default_factory=dict, description="Before/after comparison data"
    )
    confidence_score: float = Field(
        default=0.0, description="Confidence in change detection (0-1)"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notification_sent: bool = Field(
        default=False, description="Whether notification was sent"
    )
    before_snapshot_id: Optional[str] = Field(
        default=None, description="Previous snapshot reference"
    )
    after_snapshot_id: str = Field(..., description="Current snapshot reference")

    class Settings:
        name = "changes"
        indexes = [
            IndexModel([("target_id", 1)]),
            IndexModel([("timestamp", -1)]),
            IndexModel([("change_type", 1)]),
            IndexModel([("notification_sent", 1)]),
            IndexModel([("target_id", 1), ("timestamp", -1)]),
        ]


class NotificationLog(Document):
    """Audit trail for notifications"""

    user_id: str = Field(..., description="Reference to User document")
    change_id: str = Field(..., description="Reference to Change document")
    notification_type: str = Field(..., description="Type: email, webhook, push")
    status: str = Field(..., description="Status: sent, failed, pending")
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = Field(
        default=None, description="Error details if failed"
    )
    delivery_metadata: Dict = Field(
        default_factory=dict, description="Delivery details"
    )

    class Settings:
        name = "notification_logs"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("change_id", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("sent_at", -1)]),
            IndexModel([("notification_type", 1)]),
        ]


# Pydantic models for API requests/responses
class TargetCreate(BaseModel):
    """Model for creating a new monitoring target"""

    url: str
    target_type: str
    monitoring_frequency: int = 60
    xpath_selectors: Optional[Dict[str, str]] = None


class TargetUpdate(BaseModel):
    """Model for updating an existing target"""

    monitoring_frequency: Optional[int] = None
    is_active: Optional[bool] = None
    xpath_selectors: Optional[Dict[str, str]] = None


class TargetResponse(BaseModel):
    """Model for target API responses"""

    id: str
    url: str
    target_type: str
    monitoring_frequency: int
    last_checked: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ChangeResponse(BaseModel):
    """Model for change API responses"""

    id: str
    target_id: str
    change_type: str
    summary: str
    confidence_score: float
    timestamp: datetime
    notification_sent: bool


class SnapshotResponse(BaseModel):
    """Model for snapshot API responses"""

    id: str
    target_id: str
    content_hash: str
    timestamp: datetime
    size_bytes: int
    metadata: Dict
