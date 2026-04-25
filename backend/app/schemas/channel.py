from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class ChannelCreate(BaseModel):
    tipster_id: int
    channel_name: str = Field(min_length=2, max_length=255)
    channel_url: str = Field(min_length=5, max_length=512)
    channel_external_id: str | None = Field(default=None, max_length=255)
    monitoring_frequency_minutes: int = Field(default=60, ge=15, le=1440)


class ChannelUpdate(BaseModel):
    channel_name: str | None = Field(default=None, min_length=2, max_length=255)
    channel_url: str | None = Field(default=None, min_length=5, max_length=512)
    channel_external_id: str | None = None
    monitoring_frequency_minutes: int | None = Field(default=None, ge=15, le=1440)
    monitoring_status: str | None = None
    is_active: bool | None = None


class ChannelResponse(BaseModel):
    id: int
    tipster_id: int
    channel_name: str
    channel_url: str
    channel_external_id: str | None
    is_active: bool
    monitoring_frequency_minutes: int
    monitoring_status: str
    last_checked_at: datetime | None
    last_video_published_at: datetime | None
    last_video_analyzed_at: datetime | None
    last_successful_analysis_at: datetime | None
    last_failed_analysis_at: datetime | None
    last_irrelevant_video_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
