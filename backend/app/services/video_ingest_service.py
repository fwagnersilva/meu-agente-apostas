"""Serviço de ingestão de vídeos.

Recebe metadados vindos do YouTube, persiste na tabela `videos`,
atualiza o canal e enfileira o processamento.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video import Video
from app.repositories.video_repository import VideoRepository
from app.repositories.channel_repository import ChannelRepository
from app.services.audit_service import AuditService
from app.services.youtube_service import YoutubeVideoInfo


class VideoIngestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.channel_repo = ChannelRepository(db)
        self.audit = AuditService(db)

    async def ingest(self, channel_id: int, info: YoutubeVideoInfo) -> Video | None:
        """Persiste um vídeo novo. Retorna None se já existir (deduplicação)."""
        existing = await self.video_repo.get_by_youtube_id(info.youtube_video_id)
        if existing:
            return None

        now = datetime.now(timezone.utc)
        video = await self.video_repo.create(
            channel_id=channel_id,
            youtube_video_id=info.youtube_video_id,
            youtube_url=info.youtube_url,
            title=info.title,
            description=info.description,
            thumbnail_url=info.thumbnail_url,
            published_at=info.published_at,
            fetched_at=now,
            duration_seconds=info.duration_seconds,
            status="queued",
        )
        await self.audit.log("video", video.id, "created", payload={"youtube_video_id": info.youtube_video_id})
        return video

    async def ingest_batch(
        self, channel_id: int, videos: list[YoutubeVideoInfo]
    ) -> list[Video]:
        """Ingere uma lista de vídeos, ignorando duplicatas."""
        ingested: list[Video] = []
        for info in videos:
            video = await self.ingest(channel_id, info)
            if video:
                ingested.append(video)
        return ingested

    async def enqueue_processing(self, video: Video) -> None:
        """Enfileira o vídeo para processamento via Celery (Fase 3)."""
        from app.workers.tasks import process_video_task
        process_video_task.delay(video.id)
        await self.video_repo.update_status(video, "queued")
