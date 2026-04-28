from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("youtube_channels.id", ondelete="RESTRICT"), nullable=False)
    youtube_video_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    youtube_url: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # discovered | queued | processing | analyzed | failed
    status: Mapped[str] = mapped_column(String(50), default="discovered", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channel: Mapped["YoutubeChannel"] = relationship("YoutubeChannel", back_populates="videos")
    analyses: Mapped[list["VideoAnalysis"]] = relationship("VideoAnalysis", back_populates="video", cascade="all, delete-orphan")
    transcript: Mapped["VideoTranscript | None"] = relationship("VideoTranscript", back_populates="video", uselist=False, cascade="all, delete-orphan")
    ideas: Mapped[list["GameIdea"]] = relationship("GameIdea", back_populates="video", cascade="all, delete-orphan")


class VideoAnalysis(Base):
    __tablename__ = "video_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="RESTRICT"), nullable=False, index=True)
    analysis_url_slug: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    # pending | processing | analyzed_with_matches | analyzed_without_matches
    # analyzed_without_actionable_ideas | irrelevant | failed
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    # daily_games | future_games | general_analysis | methodology |
    # bankroll_management | trading_education | promotional | mixed | unknown
    content_scope: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    games_detected_count: Mapped[int] = mapped_column(Integer, default=0)
    ideas_detected_count: Mapped[int] = mapped_column(Integer, default=0)
    actionable_ideas_count: Mapped[int] = mapped_column(Integer, default=0)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0)
    no_value_count: Mapped[int] = mapped_column(Integer, default=0)
    # pending | reviewed | partially_reviewed | rejected
    review_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    reviewer_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    schema_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    normalized_output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    video: Mapped[Video] = relationship("Video", back_populates="analyses")
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewer_user_id])
    ideas: Mapped[list["GameIdea"]] = relationship("GameIdea", back_populates="video_analysis", cascade="all, delete-orphan")
    reviews: Mapped[list["VideoAnalysisReview"]] = relationship("VideoAnalysisReview", back_populates="video_analysis", cascade="all, delete-orphan")
