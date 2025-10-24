from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field, HttpUrl

class MonitoringTarget(Document):
    """Monitoring target configuration"""
    user_id: str
    url: HttpUrl
    target_type: str  # "linkedin_profile", "linkedin_company", "website"
    check_frequency: int = 3600  # seconds (default: 1 hour)
    is_active: bool = True
    last_checked: Optional[datetime] = None
    last_content_hash: Optional[str] = None
    latest_snapshot_id: Optional[str] = None  # ID of latest snapshot (for LinkedIn targets)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "monitoring_targets"
        indexes = [
            "user_id",
            "url",
            [("user_id", 1), ("url", 1)],  # compound index
        ]


class ChangeDetection(Document):
    """Detected changes log"""
    target_id: str
    user_id: str
    change_type: str  # "content_update", "new_post", "profile_change", etc.
    summary: str
    before_snapshot: Optional[str] = None
    after_snapshot: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    notified: bool = False
    
    class Settings:
        name = "change_detections"
        indexes = [
            "target_id",
            "user_id",
            [("user_id", 1), ("detected_at", -1)],
        ]


class Snapshot(Document):
    """LinkedIn profile/company snapshots"""
    target_id: str  # MonitoringTarget ID
    user_id: str
    target_type: str  # "linkedin_profile" or "linkedin_company"
    url: str
    content: str
    content_hash: str
    previous_snapshot_id: Optional[str] = None 
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "snapshots"
        indexes = [
            "target_id",
            "user_id", 
            "content_hash",
            [("target_id", 1), ("captured_at", -1)], 
            [("user_id", 1), ("captured_at", -1)],
        ]