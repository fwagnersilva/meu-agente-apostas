from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class GameResult(Base):
    __tablename__ = "game_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="RESTRICT"), unique=True, nullable=False)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    both_teams_scored: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corners_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cards_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    game: Mapped["Game"] = relationship("Game", back_populates="result")
    created_by: Mapped["User | None"] = relationship("User")


class IdeaEvaluation(Base):
    __tablename__ = "idea_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("game_ideas.id", ondelete="CASCADE"), unique=True, nullable=False)
    # automatic_binary | automatic_conditional | manual_review | non_binary_insight
    evaluation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # pending | evaluated | requires_manual_review | skipped
    evaluation_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    is_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_partial_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    manual_required: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    idea: Mapped["GameIdea"] = relationship("GameIdea", back_populates="evaluation")
    evaluated_by: Mapped["User | None"] = relationship("User")
