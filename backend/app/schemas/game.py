from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str | None = None


class CompetitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str | None = None


class IdeaConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    condition_type: str
    text: str
    is_inferred: bool


class IdeaReasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    text: str


class IdeaLabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str


class IdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    video_id: int
    tipster_id: int
    idea_type: str
    market_type: str
    selection_label: str | None
    sentiment_direction: str
    confidence_band: str
    confidence_expression_text: str | None
    belief_text: str | None
    fear_text: str | None
    entry_text: str | None
    avoid_text: str | None
    rationale_text: str | None
    condition_text: str | None
    source_excerpt: str | None
    source_timestamp_start: float | None
    source_timestamp_end: float | None
    is_actionable: bool
    needs_review: bool
    extraction_confidence: float
    review_status: str
    conditions: list[IdeaConditionResponse] = []
    reasons: list[IdeaReasonResponse] = []
    labels: list[IdeaLabelResponse] = []
    created_at: datetime


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    home_team: TeamResponse | None = None
    away_team: TeamResponse | None = None
    competition: CompetitionResponse | None = None
    scheduled_at: datetime | None
    status: str
    created_at: datetime


class GameDetailResponse(GameResponse):
    ideas: list[IdeaResponse] = []
