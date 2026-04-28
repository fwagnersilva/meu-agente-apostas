"""Persiste ideias extraídas pelo LLM no banco de dados.

Recebe o JSON v1 validado, resolve entidades (times, jogos, competições)
e salva game_ideas, idea_conditions, idea_reasons e idea_labels.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import GameIdea, IdeaCondition, IdeaReason, IdeaLabel
from app.repositories.idea_repository import IdeaRepository
from app.services.entity_resolver_service import EntityResolverService

logger = logging.getLogger(__name__)


class IdeaPersistenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.idea_repo = IdeaRepository(db)
        self.resolver = EntityResolverService(db)

    async def persist(
        self,
        extraction: dict[str, Any],
        video_id: int,
        video_analysis_id: int,
        tipster_id: int,
    ) -> list[GameIdea]:
        """Persiste todas as ideias do JSON v1. Retorna a lista de ideias criadas."""
        games_data = extraction.get("games", [])
        created: list[GameIdea] = []

        for game_data in games_data:
            match_ref = game_data.get("match_ref", {})
            try:
                game = await self.resolver.resolve_game(
                    home_name=match_ref.get("home", "Unknown"),
                    away_name=match_ref.get("away", "Unknown"),
                    competition_name=match_ref.get("competition"),
                    scheduled_date_str=match_ref.get("scheduled_date"),
                )
            except Exception as exc:
                logger.warning("Falha ao resolver jogo %s: %s", match_ref, exc)
                continue

            for idea_data in game_data.get("ideas", []):
                try:
                    idea = await self._persist_idea(idea_data, game.id, video_id, video_analysis_id, tipster_id)
                    created.append(idea)
                except Exception as exc:
                    logger.warning("Falha ao persistir ideia: %s — %s", idea_data.get("idea_type"), exc)

        return created

    async def _persist_idea(
        self,
        data: dict[str, Any],
        game_id: int,
        video_id: int,
        video_analysis_id: int,
        tipster_id: int,
    ) -> GameIdea:
        extraction_confidence = float(data.get("extraction_confidence", 0.9))
        needs_review = bool(data.get("needs_review", False)) or extraction_confidence < 0.80

        idea = GameIdea(
            game_id=game_id,
            video_id=video_id,
            video_analysis_id=video_analysis_id,
            tipster_id=tipster_id,
            idea_type=data.get("idea_type", "contextual_note"),
            market_type=data.get("market_type", "no_specific_market"),
            selection_label=data.get("selection_label"),
            sentiment_direction=data.get("sentiment_direction", "neutral"),
            confidence_band=data.get("confidence_band", "medium"),
            confidence_expression_text=data.get("confidence_expression_text"),
            belief_text=data.get("belief_text"),
            fear_text=data.get("fear_text"),
            entry_text=data.get("entry_text"),
            avoid_text=data.get("avoid_text"),
            rationale_text=data.get("rationale_text"),
            condition_text=data.get("condition_text"),
            timing=data.get("timing", "any"),
            live_trigger=data.get("live_trigger"),
            source_excerpt=data.get("source_excerpt"),
            source_timestamp_start=data.get("source_timestamp_start"),
            source_timestamp_end=data.get("source_timestamp_end"),
            is_actionable=bool(data.get("is_actionable", True)),
            needs_review=needs_review,
            extraction_confidence=extraction_confidence,
            review_status="pending_review" if needs_review else "not_required",
        )
        await self.idea_repo.create(idea)

        for cond in data.get("conditions", []):
            await self.idea_repo.create_condition(IdeaCondition(
                idea_id=idea.id,
                condition_type=cond.get("condition_type", "unknown"),
                text=cond.get("text", ""),
                is_inferred=bool(cond.get("is_inferred", False)),
            ))

        for reason in data.get("reasons", []):
            await self.idea_repo.create_reason(IdeaReason(
                idea_id=idea.id,
                category=reason.get("category", "unknown"),
                text=reason.get("text", ""),
            ))

        for label_name in data.get("labels", []):
            await self.idea_repo.create_label(IdeaLabel(
                idea_id=idea.id,
                label=str(label_name),
            ))

        return idea
