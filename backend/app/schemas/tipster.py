from datetime import datetime
from pydantic import BaseModel, Field


class TipsterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    display_name: str = Field(min_length=2, max_length=255)
    bio: str | None = None
    notes: str | None = None


class TipsterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    bio: str | None = None
    notes: str | None = None
    status: str | None = None


class TipsterResponse(BaseModel):
    id: int
    name: str
    display_name: str
    bio: str | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TipsterWithStats(TipsterResponse):
    total_channels: int = 0
    total_videos: int = 0
    total_ideas: int = 0
    total_actionable_ideas: int = 0
    hit_rate: float | None = None
