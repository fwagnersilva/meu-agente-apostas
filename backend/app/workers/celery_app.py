from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "tipster",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Roda a cada hora por padrão; cada canal tem seu próprio
        # monitoring_frequency_minutes que é verificado dentro do serviço.
        "monitor-channels-hourly": {
            "task": "monitor_channels",
            "schedule": crontab(minute=0),
        },
    },
)
