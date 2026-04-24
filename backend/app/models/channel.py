from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class YoutubeChannel(Base):
    __tablename__ = "youtube_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipster_id: Mapped[int] = mapped_column(ForeignKey("tipsters.id", ondelete="RESTRICT"), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_url: Mapped[str] = mapped_column(String(512), nullable=False)
    channel_external_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    monitoring_frequency_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_video_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_video_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_analysis_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_analysis_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_irrelevant_video_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # active | paused | error | disabled
    monitoring_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tipster: Mapped["Tipster"] = relationship("Tipster", back_populates="channels")
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="channel")
