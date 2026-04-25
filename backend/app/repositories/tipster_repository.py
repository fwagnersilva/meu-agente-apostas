from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tipster import Tipster
from app.models.channel import YoutubeChannel
from app.models.idea import GameIdea


class TipsterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Tipster]:
        result = await self.db.execute(
            select(Tipster).order_by(Tipster.name).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, tipster_id: int) -> Tipster | None:
        result = await self.db.execute(select(Tipster).where(Tipster.id == tipster_id))
        return result.scalar_one_or_none()

    async def create(self, name: str, display_name: str, bio: str | None, notes: str | None) -> Tipster:
        tipster = Tipster(name=name, display_name=display_name, bio=bio, notes=notes)
        self.db.add(tipster)
        await self.db.flush()
        return tipster

    async def update(self, tipster: Tipster, data: dict) -> Tipster:
        for field, value in data.items():
            if value is not None:
                setattr(tipster, field, value)
        await self.db.flush()
        return tipster

    async def count_channels(self, tipster_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).where(YoutubeChannel.tipster_id == tipster_id)
        )
        return result.scalar_one()

    async def count_ideas(self, tipster_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).where(GameIdea.tipster_id == tipster_id)
        )
        return result.scalar_one()

    async def count_actionable_ideas(self, tipster_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                GameIdea.tipster_id == tipster_id,
                GameIdea.is_actionable == True,  # noqa: E712
            )
        )
        return result.scalar_one()
