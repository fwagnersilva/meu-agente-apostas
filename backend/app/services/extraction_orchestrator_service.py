"""Orquestra o pipeline de extração de ideias via LLM.

Coordena:
1. Chamada ao LLM (LLMExtractionService)
2. Resolução de entidades (EntityResolverService)
3. Persistência de ideias (IdeaPersistenceService)
4. Atualização do VideoAnalysis com status, contagens e versões
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import VideoAnalysis
from app.repositories.analysis_repository import AnalysisRepository
from app.services.llm_extraction_service import LLMExtractionService, SCHEMA_VERSION, PROMPT_VERSION
from app.services.idea_persistence_service import IdeaPersistenceService

logger = logging.getLogger(__name__)

_LLM_MODEL_VERSION = "claude-sonnet-4-6"


class ExtractionOrchestratorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analysis_repo = AnalysisRepository(db)
        self.llm = LLMExtractionService()
        self.persister = IdeaPersistenceService(db)

    async def run(
        self,
        analysis: VideoAnalysis,
        normalized_text: str,
        video_title: str,
        tipster_id: int,
    ) -> None:
        """Executa extração completa e atualiza o VideoAnalysis."""
        # Mark as processing
        analysis.analysis_status = "processing"
        await self.db.flush()

        extraction = await self.llm.extract(normalized_text, video_title)

        if extraction is None:
            analysis.analysis_status = "failed"
            analysis.analyzed_at = datetime.now(timezone.utc)
            await self.db.flush()
            return

        video_info = extraction.get("video_analysis", {})
        raw_status = video_info.get("analysis_status", "analyzed_without_matches")

        ideas = await self.persister.persist(
            extraction=extraction,
            video_id=analysis.video_id,
            video_analysis_id=analysis.id,
            tipster_id=tipster_id,
        )

        # Derive final status
        if raw_status in (
            "analyzed_with_matches",
            "analyzed_without_matches",
            "analyzed_without_actionable_ideas",
            "irrelevant",
            "failed",
        ):
            final_status = raw_status
        elif ideas:
            actionable = [i for i in ideas if i.is_actionable]
            final_status = "analyzed_with_matches" if actionable else "analyzed_without_actionable_ideas"
        else:
            final_status = "analyzed_without_matches"

        analysis.analysis_status = final_status
        analysis.content_scope = video_info.get("content_scope", "unknown")
        analysis.summary_text = video_info.get("summary_text")
        analysis.games_detected_count = video_info.get("games_detected_count", len(extraction.get("games", [])))
        analysis.ideas_detected_count = video_info.get("ideas_detected_count", len(ideas))
        analysis.actionable_ideas_count = video_info.get("actionable_ideas_count", sum(1 for i in ideas if i.is_actionable))
        analysis.warnings_count = video_info.get("warnings_count", 0)
        analysis.no_value_count = video_info.get("no_value_count", 0)
        analysis.model_version = _LLM_MODEL_VERSION
        analysis.prompt_version = PROMPT_VERSION
        analysis.schema_version = SCHEMA_VERSION
        analysis.raw_output_json = extraction
        analysis.analyzed_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(
            "Extração concluída — análise=%d status=%s ideias=%d",
            analysis.id, final_status, len(ideas),
        )
