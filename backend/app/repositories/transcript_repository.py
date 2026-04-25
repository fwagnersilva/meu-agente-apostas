from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.transcript import VideoTranscript, TranscriptSegment


class TranscriptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_video_id(self, video_id: int) -> VideoTranscript | None:
        result = await self.db.execute(
            select(VideoTranscript).where(VideoTranscript.video_id == video_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> VideoTranscript:
        transcript = VideoTranscript(**kwargs)
        self.db.add(transcript)
        await self.db.flush()
        return transcript

    async def create_segment(self, **kwargs) -> TranscriptSegment:
        segment = TranscriptSegment(**kwargs)
        self.db.add(segment)
        await self.db.flush()
        return segment

    async def create_segments_bulk(
        self, video_id: int, transcript_id: int, segments: list[dict]
    ) -> list[TranscriptSegment]:
        objects = [
            TranscriptSegment(video_id=video_id, transcript_id=transcript_id, **s)
            for s in segments
        ]
        self.db.add_all(objects)
        await self.db.flush()
        return objects

    async def get_segments_by_video(self, video_id: int) -> list[TranscriptSegment]:
        result = await self.db.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.video_id == video_id)
            .order_by(TranscriptSegment.start_seconds)
        )
        return list(result.scalars().all())
