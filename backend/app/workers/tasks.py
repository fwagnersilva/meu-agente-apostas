import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    """Executa uma coroutine dentro de um task Celery síncrono."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="monitor_channels", bind=True, max_retries=3)
def monitor_channels_task(self):
    """Job periódico: verifica vídeos novos em todos os canais ativos."""
    from app.core.database import AsyncSessionLocal
    from app.services.channel_monitor_service import ChannelMonitorService

    async def _inner():
        async with AsyncSessionLocal() as db:
            return await ChannelMonitorService(db).run()

    try:
        stats = _run(_inner())
        logger.info("monitor_channels concluído: %s", stats)
        return stats
    except Exception as exc:
        logger.exception("monitor_channels falhou")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="process_video", bind=True, max_retries=2)
def process_video_task(self, video_id: int):
    """Pipeline de processamento de um vídeo: transcrição, normalização e segmentação."""
    from app.core.database import AsyncSessionLocal
    from app.services.video_pipeline_service import VideoPipelineService

    async def _inner():
        async with AsyncSessionLocal() as db:
            await VideoPipelineService(db).process(video_id)

    try:
        _run(_inner())
        logger.info("process_video concluído: video_id=%s", video_id)
    except Exception as exc:
        logger.exception("process_video falhou: video_id=%s", video_id)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="evaluate_ideas", bind=True)
def evaluate_ideas_task(self, game_id: int):
    """Avaliação automática de ideias após resultado — implementado na Fase 6."""
    pass
