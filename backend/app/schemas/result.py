from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class GameResultCreate(BaseModel):
    game_id: int
    home_score: int | None = None
    away_score: int | None = None
    both_teams_scored: bool | None = None
    total_goals: int | None = None
    corners_total: int | None = None
    cards_total: int | None = None
    result_source: str | None = None


class GameResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    home_score: int | None
    away_score: int | None
    both_teams_scored: bool | None
    total_goals: int | None
    corners_total: int | None
    cards_total: int | None
    result_source: str | None
    is_manual: bool
    created_at: datetime


class IdeaEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idea_id: int
    evaluation_type: str
    evaluation_status: str
    is_hit: bool | None
    is_partial_hit: bool | None
    manual_required: bool
    evaluation_notes: str | None
    evaluated_at: datetime | None
    created_at: datetime
