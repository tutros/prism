from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class SourceMetadata(BaseModel):
    """Quality and trust metadata for a single source URL."""
    quality: Literal["peer-reviewed", "government", "industry", "news", "blog", "unknown"] = "unknown"
    flagged: bool = False
    last_verified: datetime | None = None


class ComparisonInput(BaseModel):
    option_a: str = Field(..., min_length=1, max_length=200)
    option_b: str = Field(..., min_length=1, max_length=200)
    intent: str = Field(..., min_length=1, max_length=1000)


class Criterion(BaseModel):
    id: str
    name: str
    description: str
    score_a: float = Field(ge=0, le=100)
    score_b: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=100, default=50)
    sources: list[str] = []
    origin: Literal["ai", "user"] = "ai"
    confidence: Literal["high", "medium", "low"] = "low"


class CriterionCreate(BaseModel):
    """Model for creating a new user criterion."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    score_a: float = Field(..., ge=0, le=100)
    score_b: float = Field(..., ge=0, le=100)
    weight: float = Field(default=50, ge=0, le=100)


class CriterionUpdate(BaseModel):
    """Model for updating a criterion (all fields optional)."""
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=1000)
    score_a: float | None = Field(default=None, ge=0, le=100)
    score_b: float | None = Field(default=None, ge=0, le=100)
    weight: float | None = Field(default=None, ge=0, le=100)


class ActionableSuggestionModel(BaseModel):
    """User-facing actionable suggestion."""
    action: str
    affected_criterion: str
    impact: str
    sources: list[str] = []


class FlipAnalysisResponse(BaseModel):
    """Response from flip analysis endpoint."""
    suggestions: list[ActionableSuggestionModel] = []
    sensitivity: dict[str, float] = {}


class ComparisonResult(BaseModel):
    comparison_id: str
    status: Literal["processing", "completed", "error"]
    option_a_name: str
    option_b_name: str
    intent: str
    criteria: list[Criterion] = []
    winner: Literal["a", "b", "tie"] | None = None
    reasoning: str = ""
    created_at: datetime
    completed_at: datetime | None = None
    # Cached research for Go Deeper / Regenerate Weights
    research_a: dict | None = None
    research_b: dict | None = None
    source_metadata: dict[str, SourceMetadata] = {}  # keyed by URL
    tavily_cached_at: str | None = None  # ISO timestamp if Tavily data came from cache
