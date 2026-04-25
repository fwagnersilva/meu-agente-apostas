from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sport import Game, Team, Competition


class GameRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, game_id: int) -> Game | None:
        result = await self.db.execute(
            select(Game)
            .where(Game.id == game_id)
            .options(
                selectinload(Game.home_team),
                selectinload(Game.away_team),
                selectinload(Game.competition),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_date(self, target_date: date) -> list[Game]:
        start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        result = await self.db.execute(
            select(Game)
            .where(Game.scheduled_at >= start, Game.scheduled_at < end)
            .options(
                selectinload(Game.home_team),
                selectinload(Game.away_team),
                selectinload(Game.competition),
            )
            .order_by(Game.scheduled_at)
        )
        return list(result.scalars().all())

    async def get_by_teams(self, home_id: int, away_id: int) -> list[Game]:
        result = await self.db.execute(
            select(Game).where(
                Game.home_team_id == home_id,
                Game.away_team_id == away_id,
            ).order_by(Game.scheduled_at.desc())
        )
        return list(result.scalars().all())
