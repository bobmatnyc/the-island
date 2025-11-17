"""
Pydantic models for suggested document sources.

Design Decision: JSON storage with Pydantic validation
Rationale: Simple file-based storage for low-volume suggestions (<1000/month).
Rejected SQLite for this use case to minimize dependencies and complexity.
Future: Migrate to SQLite when volume exceeds 10,000 suggestions.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SourceStatus(str, Enum):
    """Suggestion workflow status states"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SourcePriority(str, Enum):
    """Priority levels for source processing"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuggestedSourceCreate(BaseModel):
    """Request model for creating a new source suggestion"""
    url: str = Field(..., description="URL of the document source")
    description: str = Field(..., min_length=10, max_length=2000, description="Description of the source")
    source_name: Optional[str] = Field(None, max_length=200, description="Name of the source (optional)")
    submitter_email: Optional[str] = Field(None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="Submitter's email (optional)")
    priority: SourcePriority = Field(default=SourcePriority.MEDIUM, description="Suggested priority level")
    document_count_estimate: Optional[int] = Field(None, ge=0, description="Estimated number of documents")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: str) -> str:
        """Ensure URL uses HTTP/HTTPS only"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Limit number of tags and normalize"""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [tag.strip().lower() for tag in v if tag.strip()]


class SuggestedSourceUpdate(BaseModel):
    """Model for updating suggestion status (admin only)"""
    status: Optional[SourceStatus] = None
    priority: Optional[SourcePriority] = None
    review_notes: Optional[str] = Field(None, max_length=2000)
    document_count_estimate: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None


class SuggestedSource(BaseModel):
    """Complete suggested source record with metadata

    Design:
    - id: UUID for unique identification
    - url: Validated HTTP/HTTPS URL
    - status: Workflow state (pending → approved/rejected → processing → completed/failed)
    - priority: Processing priority for approved sources
    - submitted_at: ISO 8601 timestamp
    - reviewed_at: ISO 8601 timestamp when status changed from pending

    Performance:
    - Time Complexity: O(1) for single lookups by ID
    - Space Complexity: ~500 bytes per suggestion average

    Scalability: Current design handles ~10,000 suggestions before JSON parsing
    becomes a bottleneck. For >10,000, migrate to SQLite with indexed queries.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    description: str
    source_name: Optional[str] = None
    submitter_email: Optional[str] = None
    status: SourceStatus = Field(default=SourceStatus.PENDING)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_by: Optional[str] = None  # Username from auth
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None  # Username who approved/rejected
    review_notes: Optional[str] = None
    priority: SourcePriority = Field(default=SourcePriority.MEDIUM)
    document_count_estimate: Optional[int] = None
    tags: List[str] = Field(default_factory=list)

    # Processing metadata
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    documents_ingested: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        use_enum_values = True


class SuggestionStatistics(BaseModel):
    """Statistics for admin dashboard

    Provides counts by status and priority for monitoring workflow.
    """
    total: int
    pending: int
    approved: int
    rejected: int
    processing: int
    completed: int
    failed: int
    by_priority: dict[SourcePriority, int]
    recent_submissions: int  # Last 7 days
