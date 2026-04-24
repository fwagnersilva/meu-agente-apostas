from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    season: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    games: Mapped[list["Game"]] = relationship("Game", back_populates="competition")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    aliases: Mapped[list["TeamAlias"]] = relationship("TeamAlias", back_populates="team")


class TeamAlias(Base):
    """Nomes alternativos de times para reconciliação de transcrições."""
    __tablename__ = "team_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped[Team] = relationship("Team", back_populates="aliases")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)
    home_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    away_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    round_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # scheduled | finished | canceled | unknown
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    competition: Mapped[Competition | None] = relationship("Competition", back_populates="games")
    home_team: Mapped[Team | None] = relationship("Team", foreign_keys=[home_team_id])
    away_team: Mapped[Team | None] = relationship("Team", foreign_keys=[away_team_id])
    aliases: Mapped[list["GameAlias"]] = relationship("GameAlias", back_populates="game")
    ideas: Mapped[list["GameIdea"]] = relationship("GameIdea", back_populates="game")
    result: Mapped["GameResult | None"] = relationship("GameResult", back_populates="game", uselist=False)


class GameAlias(Base):
    """Nomes alternativos de jogos detectados em transcrições."""
    __tablename__ = "game_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    game: Mapped[Game] = relationship("Game", back_populates="aliases")
