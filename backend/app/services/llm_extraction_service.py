"""Serviço de extração de ideias via LLM.

Envia a transcrição normalizada para o LLM (Claude ou OpenAI) e
retorna o JSON v1 validado conforme o contrato da especificação.

Suporta dois provedores:
- Anthropic (Claude) — via ANTHROPIC_API_KEY
- OpenAI (GPT) — via OPENAI_API_KEY
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "v1"
PROMPT_VERSION = "v1.0"

# ── Prompt mestre ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
Você é um sistema de análise estruturada de vídeos de tipsters esportivos.

Sua tarefa:
1. Identificar jogos mencionados na transcrição
2. Extrair ideias/opiniões do tipster por jogo
3. Classificar cada ideia conforme os tipos definidos
4. Devolver SOMENTE JSON válido no formato especificado abaixo

Regras obrigatórias:
- Não invente jogos que não foram mencionados
- Não invente mercados que não foram citados
- Não force ideias onde não existem
- Se o vídeo não tiver jogos, retorne "games": []
- Separe claramente: belief_text, fear_text, entry_text, avoid_text
- Comentários vagos sem mercado específico → idea_type: "contextual_note"
- "não vejo valor", "jogo perigoso", "cuidado" → registrar como sinais analíticos
- Marque needs_review: true quando houver ambiguidade ou baixa confiança
- is_actionable: false para ideias contextuais sem direção de mercado

Formato de saída (JSON v1):
{
  "video_analysis": {
    "content_scope": "daily_games|future_games|general_analysis|methodology|bankroll_management|trading_education|promotional|mixed|unknown",
    "analysis_status": "analyzed_with_matches|analyzed_without_matches|analyzed_without_actionable_ideas|irrelevant|failed",
    "summary_text": "resumo em 2-3 frases",
    "games_detected_count": 0,
    "ideas_detected_count": 0,
    "actionable_ideas_count": 0,
    "warnings_count": 0,
    "no_value_count": 0
  },
  "games": [
    {
      "match_ref": {
        "home": "Nome do time mandante",
        "away": "Nome do time visitante",
        "competition": "Nome da competição ou null",
        "scheduled_date": "YYYY-MM-DD ou null"
      },
      "ideas": [
        {
          "idea_type": "possible_entry|strong_entry|caution|no_value|avoid_game|watch_live|trend_read|risk_alert|condition_based_entry|contextual_note",
          "market_type": "over_0_5|over_1_5|over_2_5|under_2_5|btts_yes|btts_no|home_win|away_win|draw_no_bet|asian_handicap|corners|cards|player_props|lay|back|no_specific_market",
          "selection_label": "descrição curta da seleção ou null",
          "sentiment_direction": "favorable|unfavorable|neutral|conditional",
          "confidence_band": "high|medium|low",
          "confidence_expression_text": "expressão exata de confiança dita pelo tipster",
          "belief_text": "o que o tipster acredita",
          "fear_text": "o que o tipster teme",
          "entry_text": "quando/como entrar",
          "avoid_text": "quando/como evitar",
          "rationale_text": "justificativa geral",
          "condition_text": "condições para a ideia",
          "source_excerpt": "trecho exato da transcrição",
          "source_timestamp_start": 0.0,
          "source_timestamp_end": 0.0,
          "is_actionable": true,
          "needs_review": false,
          "extraction_confidence": 0.9,
          "labels": ["explicit_prediction"],
          "reasons": [
            {"category": "form|defense|attack|motivation|odds|lineup|context|home_advantage|fatigue|market_value|unknown", "text": "..."}
          ],
          "conditions": [
            {"condition_type": "lineup|early_goal|live_entry|odds_movement|tactical_setup|unknown", "text": "...", "is_inferred": false}
          ]
        }
      ]
    }
  ]
}
"""


class LLMExtractionService:
    """Envia transcrição para LLM e retorna JSON v1 validado."""

    async def extract(self, normalized_text: str, video_title: str = "") -> dict[str, Any] | None:
        """Tenta extração via Anthropic primeiro, depois OpenAI. Retorna None se falhar."""
        if settings.ANTHROPIC_API_KEY:
            result = await self._extract_anthropic(normalized_text, video_title)
            if result:
                return result

        if settings.OPENAI_API_KEY:
            result = await self._extract_openai(normalized_text, video_title)
            if result:
                return result

        logger.warning("Nenhuma API de LLM configurada — extração indisponível")
        return None

    async def _extract_anthropic(self, text: str, title: str) -> dict | None:
        user_content = f"Título do vídeo: {title}\n\nTranscrição:\n{text[:12000]}"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-6",
                        "max_tokens": 4096,
                        "system": SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_content}],
                    },
                )
            resp.raise_for_status()
            raw = resp.json()["content"][0]["text"]
            return self._parse_json(raw)
        except Exception as exc:
            logger.warning("Falha na extração via Anthropic: %s", exc)
            return None

    async def _extract_openai(self, text: str, title: str) -> dict | None:
        user_content = f"Título do vídeo: {title}\n\nTranscrição:\n{text[:12000]}"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-4o",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_content},
                        ],
                    },
                )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            return self._parse_json(raw)
        except Exception as exc:
            logger.warning("Falha na extração via OpenAI: %s", exc)
            return None

    def _parse_json(self, raw: str) -> dict | None:
        """Extrai o bloco JSON da resposta, mesmo que tenha texto ao redor."""
        raw = raw.strip()
        # Tenta direto
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Procura bloco ```json ... ```
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # Procura primeiro { ... }
        match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        logger.warning("Não foi possível parsear o JSON da resposta LLM")
        return None
