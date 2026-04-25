from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class ReviewActionRequest(BaseModel):
    action_type: str  # approve | edit | reject | split | merge | reassign_game
    notes: str | None = None
    edited_data: dict[str, Any] | None = None


class IdeaReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idea_id: int
    reviewer_user_id: int
    action_type: str
    review_notes: str | None
    created_at: datetime
