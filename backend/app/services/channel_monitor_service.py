"""Serviço de monitoramento de canais.

Executado pelo worker Celery periodicamente. Para cada canal ativo:
1. Busca vídeos novos via YouTube API
2. Ingere vídeos novos (deduplicação automática)
3. Enfileira processamento de cada novo vídeo
4. Atualiza timestamps do canal
5. Registra auditoria e erros
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.channel_repository import ChannelRepository
from app.services.youtube_service import YouTubeService
from app.services.video_ingest_service import VideoIngestService
from app.services.audit_service import AuditService
from app.models.audit import ProcessingJob


class ChannelMonitorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.channel_repo = ChannelRepository(db)
        self.youtube = YouTubeService()
        self.audit = AuditService(db)

    async def run(self) -> dict:
        """Roda o ciclo completo de monitoramento para todos os canais ativos."""
        channels = await self.channel_repo.get_active_for_monitoring()
        now = datetime.now(timezone.utc)

        stats = {"checked": 0, "new_videos": 0, "errors": 0}

        for channel in channels:
            try:
                new_videos = await self._check_channel(channel, now)
                stats["checked"] += 1
                stats["new_videos"] += new_videos
            except Exception as exc:
                stats["errors"] += 1
                await self.channel_repo.mark_error(channel, now)
                await self.audit.log(
                    "channel", channel.id, "failed",
                    payload={"error": str(exc)},
                )

        await self.db.commit()
        return stats

    async def _check_channel(self, channel, now: datetime) -> int:
        """Verifica novos vídeos de um único canal. Retorna quantidade de novos vídeos."""
        channel_external_id = channel.channel_external_id

        # Se não tem external_id ainda, tenta resolver via URL
        if not channel_external_id:
            channel_external_id = await self.youtube.get_channel_external_id(channel.channel_url)
            if channel_external_id:
                await self.channel_repo.update(channel, {"channel_external_id": channel_external_id})
            else:
                await self.channel_repo.update_last_checked(channel, now)
                return 0

        since = channel.last_video_published_at
        videos_info = await self.youtube.fetch_new_videos(channel_external_id, since=since)

        ingest_service = VideoIngestService(self.db)
        new_videos = await ingest_service.ingest_batch(channel.id, videos_info)

        # Atualiza timestamps do canal
        updates = {"last_checked_at": now}
        if new_videos:
            most_recent = max(v.published_at for v in videos_info if v)
            updates["last_video_published_at"] = most_recent

        await self.channel_repo.update(channel, updates)
        await self.audit.log(
            "channel", channel.id, "processed",
            payload={"new_videos": len(new_videos)},
        )

        # Enfileira processamento de cada vídeo novo
        for video in new_videos:
            await ingest_service.enqueue_processing(video)

        return len(new_videos)

    async def _create_job(self, channel_id: int) -> ProcessingJob:
        job = ProcessingJob(
            job_type="monitor_channels",
            entity_type="channel",
            entity_id=channel_id,
            status="running",
        )
        self.db.add(job)
        await self.db.flush()
        return job
