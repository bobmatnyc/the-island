"""
Pydantic models for news articles database.

Design Decision: Structured News Article Storage
Rationale: Provides comprehensive metadata for news articles with source
provenance, entity linkage, and credibility scoring. Articles link to
existing entities in the archive and timeline events.

Trade-offs:
- Performance: JSON storage for simplicity (<10,000 articles)
- Complexity: Entity linking requires coordination with entity_document_index.json
- Scalability: Migrate to database when articles exceed 10,000
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ArticleLanguage(str, Enum):
    """Supported article languages"""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    OTHER = "other"


class AccessType(str, Enum):
    """Article access status"""

    PUBLIC = "public"
    PAYWALL = "paywall"
    ARCHIVED = "archived"
    REMOVED = "removed"


class ArchiveStatus(str, Enum):
    """Archive preservation status"""

    NOT_ARCHIVED = "not_archived"
    ARCHIVED = "archived"
    ARCHIVE_FAILED = "archive_failed"


class NewsArticle(BaseModel):
    """
    News article model with comprehensive metadata.

    Design Decision: Complete Source Provenance
    Rationale: Track original URL, archive URL, scraping metadata, and
    verification status for transparency and reproducibility.

    Entity Linkage: articles link to entities via entities_mentioned field,
    which should match entity names in ENTITIES_INDEX.json

    Performance:
    - Time Complexity: O(1) for ID lookup
    - Space Complexity: ~2KB per article average

    Scalability: JSON storage suitable for <10,000 articles. Beyond that,
    migrate to PostgreSQL with full-text search and entity relationship tables.
    """

    id: str = Field(..., description="Unique article identifier (UUID or slug)")
    title: str = Field(..., min_length=1, max_length=500, description="Article headline")
    publication: str = Field(..., description="Publication name (e.g., 'New York Times')")
    author: Optional[str] = Field(None, description="Article author(s)")
    published_date: str = Field(..., description="Publication date (YYYY-MM-DD)")

    # URLs
    url: HttpUrl = Field(..., description="Original article URL")
    archive_url: Optional[HttpUrl] = Field(None, description="Archive.org or archive.is URL")

    # Content
    content_excerpt: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Article excerpt or summary (50-2000 chars)",
    )
    word_count: Optional[int] = Field(None, ge=0, description="Full article word count")

    # Entity linkage
    entities_mentioned: list[str] = Field(
        default_factory=list, description="Entity names mentioned (must match ENTITIES_INDEX.json)"
    )
    entity_mention_counts: dict[str, int] = Field(
        default_factory=dict, description="Number of times each entity is mentioned"
    )

    # Timeline linkage
    related_timeline_events: list[str] = Field(
        default_factory=list, description="Timeline event IDs this article relates to"
    )

    # Credibility scoring
    credibility_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Credibility score (0.0-1.0, based on source reputation)"
    )
    credibility_factors: dict[str, str] = Field(
        default_factory=dict,
        description="Factors affecting credibility (e.g., {'source_reputation': 'high'})",
    )

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Article tags/categories")
    language: ArticleLanguage = Field(default=ArticleLanguage.ENGLISH)
    access_type: AccessType = Field(default=AccessType.PUBLIC)

    # Scraping metadata
    scraped_at: Optional[datetime] = Field(None, description="When article was scraped")
    last_verified: Optional[datetime] = Field(None, description="Last verification timestamp")
    archive_status: ArchiveStatus = Field(default=ArchiveStatus.NOT_ARCHIVED)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags and limit count"""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.strip().lower() for tag in v if tag.strip()]

    @field_validator("published_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date is in YYYY-MM-DD format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
        use_enum_values = True


class NewsArticleMetadata(BaseModel):
    """
    Metadata for the news articles index.

    Tracks aggregate statistics and update timestamps.
    """

    total_articles: int = Field(default=0, ge=0)
    date_range: dict[str, Optional[str]] = Field(
        default_factory=lambda: {"earliest": None, "latest": None}
    )
    sources: dict[str, int] = Field(
        default_factory=dict, description="Article count by publication"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class NewsArticlesIndex(BaseModel):
    """
    Complete news articles index structure.

    Root structure for the news_articles_index.json file.
    """

    metadata: NewsArticleMetadata
    articles: list[NewsArticle]


class NewsSearchParams(BaseModel):
    """
    Query parameters for searching/filtering articles.

    All parameters are optional for flexible filtering.
    """

    entity: Optional[str] = Field(None, description="Filter by entity name")
    publication: Optional[str] = Field(None, description="Filter by publication")
    start_date: Optional[str] = Field(
        None, description="Filter articles from this date (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, description="Filter articles until this date (YYYY-MM-DD)"
    )
    tags: Optional[list[str]] = Field(None, description="Filter by tags (OR logic)")
    language: Optional[ArticleLanguage] = Field(None, description="Filter by language")
    access_type: Optional[AccessType] = Field(None, description="Filter by access type")
    min_credibility: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum credibility score"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format if provided"""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class NewsArticleCreate(BaseModel):
    """
    Request model for creating a new article (for ingestion scripts).

    Simplified version without auto-generated fields (id, scraped_at).
    """

    title: str = Field(..., min_length=1, max_length=500)
    publication: str
    author: Optional[str] = None
    published_date: str
    url: HttpUrl
    archive_url: Optional[HttpUrl] = None
    content_excerpt: str = Field(..., min_length=50, max_length=2000)
    word_count: Optional[int] = Field(None, ge=0)
    entities_mentioned: list[str] = Field(default_factory=list)
    entity_mention_counts: dict[str, int] = Field(default_factory=dict)
    related_timeline_events: list[str] = Field(default_factory=list)
    credibility_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    credibility_factors: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    language: ArticleLanguage = Field(default=ArticleLanguage.ENGLISH)
    access_type: AccessType = Field(default=AccessType.PUBLIC)

    @field_validator("published_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date is in YYYY-MM-DD format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class NewsSourcesSummary(BaseModel):
    """
    Summary of news sources for statistics endpoint.
    """

    publication: str
    article_count: int
    date_range: dict[str, Optional[str]]
    average_credibility: Optional[float] = None
