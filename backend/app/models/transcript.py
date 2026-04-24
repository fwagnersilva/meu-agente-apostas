from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class VideoTranscript(Base):
    __tablename__ = "video_transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False)
    # youtube_api | whisper | manual
    transcript_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    raw_transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_timestamps: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    video: Mapped["Video"] = relationship("Video", back_populates="transcript")
    segments: Mapped[list["TranscriptSegment"]] = relationship("TranscriptSegment", back_populates="transcript")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    transcript_id: Mapped[int] = mapped_column(ForeignKey("video_transcripts.id", ondelete="CASCADE"), nullable=False)
    start_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    end_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # intro | match_analysis | methodology | promotional | closing | unknown
    segment_type: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transcript: Mapped[VideoTranscript] = relationship("VideoTranscript", back_populates="segments")
    ideas: Mapped[list["GameIdea"]] = relationship("GameIdea", back_populates="segment")
