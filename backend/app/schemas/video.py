from datetime import datetime
from pydantic import BaseModel


class VideoResponse(BaseModel):
    id: int
    channel_id: int
    youtube_video_id: str
    youtube_url: str
    title: str
    description: str | None
    thumbnail_url: str | None
    published_at: datetime | None
    fetched_at: datetime | None
    duration_seconds: int | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VideoListResponse(BaseModel):
    id: int
    channel_id: int
    youtube_video_id: str
    youtube_url: str
    title: str
    thumbnail_url: str | None
    published_at: datetime | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
