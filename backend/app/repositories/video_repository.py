from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video import Video


class VideoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        channel_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Video]:
        query = select(Video).order_by(Video.published_at.desc()).offset(skip).limit(limit)
        if channel_id is not None:
            query = query.where(Video.channel_id == channel_id)
        if status is not None:
            query = query.where(Video.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, video_id: int) -> Video | None:
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()

    async def get_by_youtube_id(self, youtube_video_id: str) -> Video | None:
        result = await self.db.execute(
            select(Video).where(Video.youtube_video_id == youtube_video_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Video:
        video = Video(**kwargs)
        self.db.add(video)
        await self.db.flush()
        return video

    async def update_status(self, video: Video, status: str) -> None:
        video.status = status
        await self.db.flush()
