from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video import VideoAnalysis


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, analysis_id: int) -> VideoAnalysis | None:
        result = await self.db.execute(
            select(VideoAnalysis).where(VideoAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> VideoAnalysis | None:
        result = await self.db.execute(
            select(VideoAnalysis).where(VideoAnalysis.analysis_url_slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_video_id(self, video_id: int) -> list[VideoAnalysis]:
        result = await self.db.execute(
            select(VideoAnalysis)
            .where(VideoAnalysis.video_id == video_id)
            .order_by(VideoAnalysis.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> VideoAnalysis:
        analysis = VideoAnalysis(**kwargs)
        self.db.add(analysis)
        await self.db.flush()
        return analysis

    async def update(self, analysis: VideoAnalysis, data: dict) -> VideoAnalysis:
        for field, value in data.items():
            setattr(analysis, field, value)
        await self.db.flush()
        return analysis
