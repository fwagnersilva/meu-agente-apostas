from datetime import datetime
from pydantic import BaseModel


class TranscriptSegmentResponse(BaseModel):
    id: int
    start_seconds: float | None
    end_seconds: float | None
    normalized_text: str | None
    segment_type: str

    model_config = {"from_attributes": True}


class VideoTranscriptResponse(BaseModel):
    id: int
    transcript_source: str | None
    language_code: str | None
    has_timestamps: bool
    normalized_transcript_text: str | None
    segments: list[TranscriptSegmentResponse] = []

    model_config = {"from_attributes": True}


class VideoAnalysisResponse(BaseModel):
    id: int
    video_id: int
    analysis_url_slug: str | None
    analyzed_at: datetime | None
    analysis_status: str
    content_scope: str | None
    summary_text: str | None
    games_detected_count: int
    ideas_detected_count: int
    actionable_ideas_count: int
    warnings_count: int
    no_value_count: int
    review_status: str
    reviewed_at: datetime | None
    model_version: str | None
    prompt_version: str | None
    schema_version: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VideoAnalysisDetailResponse(VideoAnalysisResponse):
    """Resposta completa com transcript e segmentos."""
    transcript: VideoTranscriptResponse | None = None
