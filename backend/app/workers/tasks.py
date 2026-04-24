from app.workers.celery_app import celery_app


@celery_app.task(name="monitor_channels")
def monitor_channels_task():
    """Job periódico de monitoramento de canais — implementado na Fase 2."""
    pass


@celery_app.task(name="process_video")
def process_video_task(video_id: int):
    """Pipeline de processamento de um vídeo — implementado na Fase 3."""
    pass


@celery_app.task(name="evaluate_ideas")
def evaluate_ideas_task(game_id: int):
    """Avaliação automática de ideias após resultado — implementado na Fase 6."""
    pass
