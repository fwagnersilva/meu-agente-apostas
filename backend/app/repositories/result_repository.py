from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.result import GameResult, IdeaEvaluation


class ResultRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_game(self, game_id: int) -> GameResult | None:
        result = await self.db.execute(
            select(GameResult).where(GameResult.game_id == game_id)
        )
        return result.scalar_one_or_none()

    async def create(self, game_result: GameResult) -> GameResult:
        self.db.add(game_result)
        await self.db.flush()
        return game_result

    async def update(self, game_result: GameResult, data: dict) -> GameResult:
        for k, v in data.items():
            setattr(game_result, k, v)
        await self.db.flush()
        return game_result


class EvaluationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_idea(self, idea_id: int) -> IdeaEvaluation | None:
        result = await self.db.execute(
            select(IdeaEvaluation).where(IdeaEvaluation.idea_id == idea_id)
        )
        return result.scalar_one_or_none()

    async def create(self, evaluation: IdeaEvaluation) -> IdeaEvaluation:
        self.db.add(evaluation)
        await self.db.flush()
        return evaluation

    async def update(self, evaluation: IdeaEvaluation, data: dict) -> IdeaEvaluation:
        for k, v in data.items():
            setattr(evaluation, k, v)
        await self.db.flush()
        return evaluation
