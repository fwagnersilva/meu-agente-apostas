from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class IdeaReview(Base):
    """Histórico de revisões humanas de ideias."""
    __tablename__ = "idea_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False)
    reviewer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # approve | edit | reject | split | merge | reassign_game
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    idea: Mapped["GameIdea"] = relationship("GameIdea", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User")


class VideoAnalysisReview(Base):
    """Revisão no nível da análise do vídeo."""
    __tablename__ = "video_analysis_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_analysis_id: Mapped[int] = mapped_column(ForeignKey("video_analyses.id", ondelete="CASCADE"), nullable=False)
    reviewer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    video_analysis: Mapped["VideoAnalysis"] = relationship("VideoAnalysis", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User")
