from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class GameIdea(Base):
    """Tabela central do sistema: uma ideia/opinião de tipster sobre um jogo."""
    __tablename__ = "game_ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int | None] = mapped_column(ForeignKey("games.id"), nullable=True, index=True)
    tipster_id: Mapped[int] = mapped_column(ForeignKey("tipsters.id", ondelete="RESTRICT"), nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="RESTRICT"), nullable=False, index=True)
    video_analysis_id: Mapped[int | None] = mapped_column(ForeignKey("video_analyses.id"), nullable=True)
    segment_id: Mapped[int | None] = mapped_column(ForeignKey("transcript_segments.id"), nullable=True)

    source_timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_timestamp_end: Mapped[float | None] = mapped_column(Float, nullable=True)

    # possible_entry | strong_entry | caution | no_value | avoid_game |
    # watch_live | trend_read | risk_alert | condition_based_entry | contextual_note
    idea_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # over_0_5 | over_1_5 | over_2_5 | under_2_5 | btts_yes | btts_no |
    # home_win | away_win | draw_no_bet | asian_handicap | corners | cards |
    # player_props | lay | back | no_specific_market
    market_type: Mapped[str] = mapped_column(String(50), default="no_specific_market", nullable=False)
    selection_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # favorable | unfavorable | neutral | conditional
    sentiment_direction: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # high | medium | low
    confidence_band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence_expression_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    belief_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fear_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    avoid_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_actionable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # pending | approved | corrected | rejected
    review_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    game: Mapped["Game | None"] = relationship("Game", back_populates="ideas")
    tipster: Mapped["Tipster"] = relationship("Tipster")
    video: Mapped["Video"] = relationship("Video", back_populates="ideas")
    video_analysis: Mapped["VideoAnalysis | None"] = relationship("VideoAnalysis", back_populates="ideas")
    segment: Mapped["TranscriptSegment | None"] = relationship("TranscriptSegment", back_populates="ideas")
    conditions: Mapped[list["IdeaCondition"]] = relationship("IdeaCondition", back_populates="idea", cascade="all, delete-orphan")
    reasons: Mapped[list["IdeaReason"]] = relationship("IdeaReason", back_populates="idea", cascade="all, delete-orphan")
    labels: Mapped[list["IdeaLabel"]] = relationship("IdeaLabel", back_populates="idea", cascade="all, delete-orphan")
    reviews: Mapped[list["IdeaReview"]] = relationship("IdeaReview", back_populates="idea")
    evaluation: Mapped["IdeaEvaluation | None"] = relationship("IdeaEvaluation", back_populates="idea", uselist=False)


class IdeaCondition(Base):
    """Condições estruturadas associadas a uma ideia."""
    __tablename__ = "idea_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False)
    # lineup | early_goal | live_entry | odds_movement | tactical_setup | unknown
    condition_type: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    condition_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_inferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    idea: Mapped[GameIdea] = relationship("GameIdea", back_populates="conditions")


class IdeaReason(Base):
    """Justificativas categorizadas de uma ideia."""
    __tablename__ = "idea_reasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False)
    # form | defense | attack | motivation | odds | lineup | context |
    # home_advantage | fatigue | market_value | unknown
    reason_category: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    idea: Mapped[GameIdea] = relationship("GameIdea", back_populates="reasons")


class IdeaLabel(Base):
    """Multi-rótulos associados a uma ideia."""
    __tablename__ = "idea_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False)
    # explicit_prediction | implicit_prediction | caution |
    # contextual_comment | risk_alert | no_value | watch_live
    label: Mapped[str] = mapped_column(String(50), nullable=False)

    idea: Mapped[GameIdea] = relationship("GameIdea", back_populates="labels")
