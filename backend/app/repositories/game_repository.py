from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sport import Game, Team, Competition
from app.models.result import GameResult


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
                selectinload(Game.result),
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
                selectinload(Game.result),
            )
            .order_by(Game.scheduled_at)
        )
        return list(result.scalars().all())

    async def upsert_result(
        self, game_id: int, home_score: int, away_score: int, user_id: int | None = None
    ) -> GameResult:
        from sqlalchemy import select as sa_select
        res = await self.db.execute(sa_select(GameResult).where(GameResult.game_id == game_id))
        gr = res.scalar_one_or_none()
        total = home_score + away_score
        btts = home_score > 0 and away_score > 0
        if gr:
            gr.home_score = home_score
            gr.away_score = away_score
            gr.total_goals = total
            gr.both_teams_scored = btts
            gr.is_manual = True
            gr.created_by_user_id = user_id
        else:
            gr = GameResult(
                game_id=game_id,
                home_score=home_score,
                away_score=away_score,
                total_goals=total,
                both_teams_scored=btts,
                is_manual=True,
                created_by_user_id=user_id,
            )
            self.db.add(gr)
        await self.db.flush()
        return gr

    async def get_by_teams(self, home_id: int, away_id: int) -> list[Game]:
        result = await self.db.execute(
            select(Game).where(
                Game.home_team_id == home_id,
                Game.away_team_id == away_id,
            ).order_by(Game.scheduled_at.desc())
        )
        return list(result.scalars().all())
