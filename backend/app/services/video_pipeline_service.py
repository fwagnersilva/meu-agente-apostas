"""Pipeline de processamento de vídeo.

Orquestra os passos:
1. Marcar vídeo como `processing`
2. Obter transcrição (YouTube API → Whisper)
3. Normalizar texto
4. Segmentar em blocos
5. Salvar transcript + segmentos
6. Criar VideoAnalysis
7. Extrair ideias via LLM (ExtractionOrchestratorService)
8. Atualizar status do vídeo para `analyzed` ou `failed`
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.repositories.video_repository import VideoRepository
from app.repositories.transcript_repository import TranscriptRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.channel_repository import ChannelRepository
from app.services.transcript_service import TranscriptService, TranscriptResult
from app.services.normalization_service import NormalizationService
from app.services.segmentation_service import SegmentationService, Segment
from app.services.audit_service import AuditService
from app.services.extraction_orchestrator_service import ExtractionOrchestratorService
from app.models.audit import ProcessingJob

logger = logging.getLogger(__name__)


class VideoPipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.transcript_repo = TranscriptRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.channel_repo = ChannelRepository(db)
        self.audit = AuditService(db)
        self.transcript_svc = TranscriptService()
        self.norm_svc = NormalizationService()
        self.seg_svc = SegmentationService()

    async def process(self, video_id: int) -> None:
        """Executa o pipeline completo para um vídeo."""
        video = await self.video_repo.get_by_id(video_id)
        if not video:
            logger.error("Vídeo %s não encontrado", video_id)
            return

        job = await self._create_job(video_id)
        await self.video_repo.update_status(video, "processing")
        await self.audit.log("video", video_id, "processed", payload={"step": "started"})

        try:
            await self._run_pipeline(video, job)
        except Exception as exc:
            logger.exception("Falha no pipeline do vídeo %s", video_id)
            await self._handle_failure(video, job, exc)

        await self.db.commit()

    # ── Passos internos ───────────────────────────────────────────────────

    async def _run_pipeline(self, video: Video, job: ProcessingJob) -> None:
        now = datetime.now(timezone.utc)

        # Passo 1 — Transcrição
        transcript_result = await self.transcript_svc.fetch(video.youtube_video_id)
        if not transcript_result:
            await self._finalize_no_transcript(video, job, now)
            return

        # Passo 2 — Normalização
        normalized = self.norm_svc.normalize(transcript_result.full_text)

        # Passo 3 — Persistir transcript
        transcript = await self.transcript_repo.create(
            video_id=video.id,
            transcript_source=transcript_result.source,
            language_code=transcript_result.language_code,
            raw_transcript_text=transcript_result.full_text,
            normalized_transcript_text=normalized,
            has_timestamps=transcript_result.has_timestamps,
        )

        # Passo 4 — Segmentação
        if transcript_result.has_timestamps and transcript_result.entries:
            segments = self.seg_svc.segment_by_entries(transcript_result.entries, normalized)
        else:
            segments = self.seg_svc.segment_text(normalized)

        # Passo 5 — Persistir segmentos
        segments_data = [
            {
                "raw_text": s.raw_text,
                "normalized_text": s.normalized_text,
                "segment_type": s.segment_type,
                "start_seconds": s.start_seconds,
                "end_seconds": s.end_seconds,
            }
            for s in segments
        ]
        await self.transcript_repo.create_segments_bulk(video.id, transcript.id, segments_data)

        # Passo 6 — Criar VideoAnalysis
        slug = f"analise-{video.youtube_video_id}-{uuid.uuid4().hex[:8]}"
        analysis = await self.analysis_repo.create(
            video_id=video.id,
            analysis_url_slug=slug,
            analyzed_at=now,
            analysis_status="pending",
            schema_version="v1",
        )

        # Passo 7 — Extração via LLM
        channel = await self.channel_repo.get_by_id(video.channel_id)
        tipster_id = channel.tipster_id if channel else 0
        extractor = ExtractionOrchestratorService(self.db)
        await extractor.run(
            analysis=analysis,
            normalized_text=normalized,
            video_title=video.title,
            tipster_id=tipster_id,
        )

        # Passo 8 — Atualizar canal
        if channel:
            await self.channel_repo.update(channel, {"last_video_analyzed_at": now})

        # Passo 9 — Finalizar
        await self.video_repo.update_status(video, "analyzed")
        await self._finish_job(job, "completed")
        await self.audit.log(
            "video", video.id, "processed",
            payload={
                "step": "completed",
                "transcript_source": transcript_result.source,
                "segments": len(segments),
                "analysis_id": analysis.id,
                "analysis_status": analysis.analysis_status,
            },
        )
        logger.info(
            "Vídeo %s processado: %d segmentos, analysis_id=%s",
            video.id, len(segments), analysis.id,
        )

    async def _finalize_no_transcript(self, video: Video, job: ProcessingJob, now: datetime) -> None:
        """Cria análise marcada como falha de transcrição."""
        slug = f"analise-{video.youtube_video_id}-{uuid.uuid4().hex[:8]}"
        await self.analysis_repo.create(
            video_id=video.id,
            analysis_url_slug=slug,
            analyzed_at=now,
            analysis_status="failed",
            summary_text="Transcrição não disponível.",
            schema_version="v1",
        )
        await self.video_repo.update_status(video, "failed")
        await self._finish_job(job, "failed", "Transcrição indisponível")
        await self.audit.log("video", video.id, "failed", payload={"reason": "no_transcript"})

    async def _handle_failure(self, video: Video, job: ProcessingJob, exc: Exception) -> None:
        await self.video_repo.update_status(video, "failed")
        await self._finish_job(job, "failed", str(exc))
        await self.audit.log("video", video.id, "failed", payload={"error": str(exc)})

        channel = await self.channel_repo.get_by_id(video.channel_id)
        if channel:
            await self.channel_repo.mark_error(channel, datetime.now(timezone.utc))

    async def _create_job(self, video_id: int) -> ProcessingJob:
        now = datetime.now(timezone.utc)
        job = ProcessingJob(
            job_type="process_video",
            entity_type="video",
            entity_id=video_id,
            status="running",
            started_at=now,
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def _finish_job(
        self, job: ProcessingJob, status: str, error: str | None = None
    ) -> None:
        job.status = status
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = error
        await self.db.flush()
