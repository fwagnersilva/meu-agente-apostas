import asyncio
from app.workers.celery_app import celery_app


def _run(coro):
    """Executa uma coroutine dentro de um task Celery síncrono."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="monitor_channels", bind=True, max_retries=3)
def monitor_channels_task(self):
    """Job periódico: verifica vídeos novos em todos os canais ativos."""
    from app.core.database import AsyncSessionLocal
    from app.services.channel_monitor_service import ChannelMonitorService

    async def _run_monitor():
        async with AsyncSessionLocal() as db:
            service = ChannelMonitorService(db)
            return await service.run()

    try:
        stats = _run(_run_monitor())
        return stats
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="process_video", bind=True, max_retries=2)
def process_video_task(self, video_id: int):
    """Pipeline principal de processamento de um vídeo — implementado na Fase 3."""
    pass


@celery_app.task(name="evaluate_ideas", bind=True)
def evaluate_ideas_task(self, game_id: int):
    """Avaliação automática de ideias após resultado — implementado na Fase 6."""
    pass
