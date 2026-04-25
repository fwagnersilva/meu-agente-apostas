from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.channel import YoutubeChannel


class ChannelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[YoutubeChannel]:
        result = await self.db.execute(
            select(YoutubeChannel).order_by(YoutubeChannel.channel_name).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, channel_id: int) -> YoutubeChannel | None:
        result = await self.db.execute(
            select(YoutubeChannel).where(YoutubeChannel.id == channel_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tipster(self, tipster_id: int) -> list[YoutubeChannel]:
        result = await self.db.execute(
            select(YoutubeChannel).where(YoutubeChannel.tipster_id == tipster_id)
        )
        return list(result.scalars().all())

    async def get_active_for_monitoring(self) -> list[YoutubeChannel]:
        result = await self.db.execute(
            select(YoutubeChannel).where(
                YoutubeChannel.monitoring_status == "active",
                YoutubeChannel.is_active == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_by_external_id(self, external_id: str) -> YoutubeChannel | None:
        result = await self.db.execute(
            select(YoutubeChannel).where(YoutubeChannel.channel_external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> YoutubeChannel:
        channel = YoutubeChannel(**kwargs)
        self.db.add(channel)
        await self.db.flush()
        return channel

    async def update(self, channel: YoutubeChannel, data: dict) -> YoutubeChannel:
        for field, value in data.items():
            setattr(channel, field, value)
        await self.db.flush()
        return channel

    async def update_last_checked(self, channel: YoutubeChannel, now: datetime) -> None:
        channel.last_checked_at = now
        await self.db.flush()

    async def mark_error(self, channel: YoutubeChannel, now: datetime) -> None:
        channel.monitoring_status = "error"
        channel.last_failed_analysis_at = now
        await self.db.flush()
