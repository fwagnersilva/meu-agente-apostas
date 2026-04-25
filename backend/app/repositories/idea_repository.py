from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.idea import GameIdea, IdeaCondition, IdeaReason, IdeaLabel


class IdeaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, idea: GameIdea) -> GameIdea:
        self.db.add(idea)
        await self.db.flush()
        return idea

    async def create_condition(self, cond: IdeaCondition) -> None:
        self.db.add(cond)
        await self.db.flush()

    async def create_reason(self, reason: IdeaReason) -> None:
        self.db.add(reason)
        await self.db.flush()

    async def create_label(self, label: IdeaLabel) -> None:
        self.db.add(label)
        await self.db.flush()

    async def get_by_game(self, game_id: int) -> list[GameIdea]:
        result = await self.db.execute(
            select(GameIdea)
            .where(GameIdea.game_id == game_id)
            .options(
                selectinload(GameIdea.conditions),
                selectinload(GameIdea.reasons),
                selectinload(GameIdea.labels),
            )
            .order_by(GameIdea.id)
        )
        return list(result.scalars().all())

    async def get_by_video(self, video_id: int) -> list[GameIdea]:
        result = await self.db.execute(
            select(GameIdea)
            .where(GameIdea.video_id == video_id)
            .options(
                selectinload(GameIdea.conditions),
                selectinload(GameIdea.reasons),
                selectinload(GameIdea.labels),
            )
        )
        return list(result.scalars().all())

    async def get_pending_review(self, skip: int = 0, limit: int = 50) -> list[GameIdea]:
        result = await self.db.execute(
            select(GameIdea)
            .where(GameIdea.review_status == "pending_review")
            .options(
                selectinload(GameIdea.conditions),
                selectinload(GameIdea.reasons),
                selectinload(GameIdea.labels),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, idea_id: int) -> GameIdea | None:
        result = await self.db.execute(
            select(GameIdea)
            .where(GameIdea.id == idea_id)
            .options(
                selectinload(GameIdea.conditions),
                selectinload(GameIdea.reasons),
                selectinload(GameIdea.labels),
            )
        )
        return result.scalar_one_or_none()

    async def update_review_status(self, idea_id: int, status: str) -> None:
        await self.db.execute(
            update(GameIdea).where(GameIdea.id == idea_id).values(review_status=status)
        )
        await self.db.flush()
