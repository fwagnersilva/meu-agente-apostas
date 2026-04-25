"""Avaliação automática de ideias após registro de resultado.

Suporta mercados binários simples: over_X_5, under_X_5, btts_yes/no,
home_win, away_win. Ideias de outros tipos vão para manual_review.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import GameIdea
from app.models.result import GameResult, IdeaEvaluation
from app.repositories.idea_repository import IdeaRepository
from app.repositories.result_repository import EvaluationRepository

logger = logging.getLogger(__name__)

_AUTO_MARKETS = {
    "over_0_5", "over_1_5", "over_2_5", "over_3_5",
    "under_2_5", "under_3_5",
    "btts_yes", "btts_no",
    "home_win", "away_win",
}


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.idea_repo = IdeaRepository(db)
        self.eval_repo = EvaluationRepository(db)

    async def evaluate_game(self, game_id: int, result: GameResult) -> int:
        """Avalia todas as ideias de um jogo. Retorna contagem de avaliações criadas."""
        ideas = await self.idea_repo.get_by_game(game_id)
        count = 0
        for idea in ideas:
            if not idea.is_actionable:
                continue
            existing = await self.eval_repo.get_by_idea(idea.id)
            if existing:
                continue
            is_hit = self._evaluate(idea, result)
            eval_type = "automatic_binary" if is_hit is not None else "manual_review"
            evaluation = IdeaEvaluation(
                idea_id=idea.id,
                evaluation_type=eval_type,
                evaluation_status="evaluated" if is_hit is not None else "requires_manual_review",
                is_hit=is_hit,
                manual_required=(is_hit is None),
                evaluated_at=datetime.now(timezone.utc),
            )
            await self.eval_repo.create(evaluation)
            count += 1
        return count

    def _evaluate(self, idea: GameIdea, result: GameResult) -> bool | None:
        market = idea.market_type
        total = result.total_goals

        if market == "over_0_5" and total is not None:
            return total > 0
        if market == "over_1_5" and total is not None:
            return total > 1
        if market == "over_2_5" and total is not None:
            return total > 2
        if market == "over_3_5" and total is not None:
            return total > 3
        if market == "under_2_5" and total is not None:
            return total < 3
        if market == "under_3_5" and total is not None:
            return total < 4
        if market == "btts_yes" and result.both_teams_scored is not None:
            return result.both_teams_scored
        if market == "btts_no" and result.both_teams_scored is not None:
            return not result.both_teams_scored
        if market == "home_win" and result.home_score is not None and result.away_score is not None:
            return result.home_score > result.away_score
        if market == "away_win" and result.home_score is not None and result.away_score is not None:
            return result.away_score > result.home_score
        return None
