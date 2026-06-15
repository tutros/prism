from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Decision(BaseModel):
    id: str
    title: str
    options: list[str]
    option_contexts: dict[str, str] = {}
    intent: str
    created_at: datetime


class DecisionInput(BaseModel):
    options: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(..., min_length=2, max_length=10)
    option_contexts: dict[str, str] = {}
    intent: str = Field(..., min_length=1, max_length=1000)
    tier: Literal["quick", "medium", "deep"] | None = None


class HiddenProperty(BaseModel):
    name: str
    category: str
    magnitude: Literal["High", "Medium", "Low"]
    confidence: Literal["high", "medium", "low"]
    description: str


class Criterion(BaseModel):
    id: str
    name: str
    description: str
    scores: dict[str, float]  # keyed by option name, 0-100
    weight: float = Field(ge=0, le=100, default=50)
    sources: list[str] = []
    origin: Literal["ai", "user"] = "ai"
    confidence: Literal["high", "medium", "low"] = "low"


class CriterionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    scores: dict[str, float]
    weight: float = Field(default=50, ge=0, le=100)


class CriterionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=1000)
    scores: dict[str, float] | None = None
    weight: float | None = Field(default=None, ge=0, le=100)


class AnalysisResult(BaseModel):
    analysis_id: str
    decision_id: str
    tier: Literal["quick", "medium", "deep"]
    status: Literal["processing", "completed", "error"]
    options: list[str]
    winner: str | None = None
    reasoning: str = ""
    criteria: list[Criterion] = []
    weights_original: dict[str, float] = {}
    weights_current: dict[str, float] = {}
    research: dict[str, dict] = {}
    hidden_properties: list[HiddenProperty] = []
    created_at: datetime
    completed_at: datetime | None = None
