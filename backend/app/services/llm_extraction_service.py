"""Servico de extracao de ideias via LLM.

Envia a transcricao normalizada para o LLM e retorna o JSON v1 validado.
Suporta Groq (gratis), Anthropic e OpenAI em cascata.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "v1"
PROMPT_VERSION = "v3.0"

SYSTEM_PROMPT = """\
Extraia ideias analiticas estruturadas de transcricoes de tipsters esportivos em JSON.

REGRAS CRITICAS:
1. MULTI-JOGO: identifique TODOS os jogos ("agora...", "proximo...", "Time A x Time B"). 3-5 ideias por jogo.
2. RACIOCINIO: capture o POR QUE, nao so o mercado. Ideias separadas para: mecanismo causal, risco, acao, gatilho.
3. DEDUPLICACAO: Over 2.5 + BTTS da mesma premissa = 1 ideia trend_read. Max 5 ideias/jogo.
4. REGRA DO SE: "se [condicao] entao [acao]" -> condition_based_entry com condition_text.
5. ACIONABILIDADE: odds esmagadas/"nao sei se tem valor" -> no_value (nao trend_read).
6. ANTI-ALUCINACAO: nao invente jogos nem mercados nao citados.

TIPOS: strong_entry | possible_entry | condition_based_entry | watch_live | no_value | avoid_game | risk_alert | trend_read | game_script | caution | contextual_note

SEMANTICA:
"nao vejo valor","odds esmagadas" -> no_value
"nao aconselho","evitaria" -> avoid_game
"levar pro live","observar antes" -> watch_live
"ambas e forte","over nao e dificil" -> trend_read
"se jogo aberto","se sair gol" -> condition_based_entry
"linha alta","toma gol com facilidade" -> risk_alert (defense)
"primeiro tempo forte","pode virar" -> game_script
"confere [jogador]","se [jogador] jogar" -> condition_based_entry (lineup)

MERCADOS VALIDOS: over_0_5|over_1_5|over_2_5|over_3_5|under_2_5|btts_yes|btts_no|home_win|away_win|draw|draw_no_bet|asian_handicap|double_chance|corners|cards|player_props|lay|back|no_specific_market

SAIDA JSON EXATA:
{"video_analysis":{"content_scope":"daily_games","analysis_status":"analyzed_with_matches","summary_text":"...","games_detected_count":0,"ideas_detected_count":0,"actionable_ideas_count":0,"warnings_count":0,"no_value_count":0},"games":[{"match_ref":{"home":"...","away":"...","competition":"...","scheduled_date":"YYYY-MM-DD"},"ideas":[{"idea_type":"trend_read","market_type":"over_2_5","selection_label":"Over 2.5","sentiment_direction":"favorable","confidence_band":"high","confidence_expression_text":null,"belief_text":"...POR QUE...","fear_text":"...","entry_text":"...","avoid_text":"...","rationale_text":"...causal...","condition_text":null,"timing":"pre_game","live_trigger":null,"source_excerpt":"...","source_timestamp_start":null,"source_timestamp_end":null,"is_actionable":true,"needs_review":false,"extraction_confidence":0.9,"labels":[],"reasons":[{"category":"attack","text":"..."}],"conditions":[]}]}]}
"""


def _split_by_chunks(text: str, chunk_size: int = 60000) -> list[str]:
    """Divide text into chunks of ~chunk_size chars, splitting at paragraph/sentence boundaries."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Try to split at paragraph boundary
        split = text.rfind("\n\n", start, end)
        if split == -1:
            split = text.rfind("\n", start, end)
        if split == -1:
            split = text.rfind(". ", start, end)
        if split == -1:
            split = end
        chunks.append(text[start:split].strip())
        start = split
    return [c for c in chunks if c]


def _build_user_content(text: str, title: str, max_chars: int = 40000) -> str:
    from datetime import date
    today = date.today().isoformat()
    return (
        f"Data de hoje: {today}\n"
        f"Titulo do video: {title}\n\n"
        f"Transcricao:\n{text[:max_chars]}"
    )


class LLMExtractionService:
    """Envia transcricao para LLM e retorna JSON v1 validado."""

    async def extract(self, normalized_text: str, video_title: str = "") -> dict[str, Any] | None:
        """Cascata: Ollama (local) → Groq → Anthropic → OpenAI."""
        if settings.OLLAMA_BASE_URL:
            result = await self._extract_ollama(normalized_text, video_title)
            if result:
                return result

        if settings.GROQ_API_KEY:
            result = await self._extract_groq(normalized_text, video_title)
            if result:
                return result

        if settings.ANTHROPIC_API_KEY:
            result = await self._extract_anthropic(normalized_text, video_title)
            if result:
                return result

        if settings.OPENAI_API_KEY:
            result = await self._extract_openai(normalized_text, video_title)
            if result:
                return result

        logger.warning("Nenhuma API de LLM configurada - extracao indisponivel")
        return None

    async def _extract_ollama(self, text: str, title: str) -> dict | None:
        """Ollama local — sem limite de payload. Para videos longos usa chunking."""
        base = settings.OLLAMA_BASE_URL.rstrip("/")
        model = settings.OLLAMA_MODEL or "llama3.2"

        # Para transcrições muito longas (>60k chars), divide em blocos por jogo
        chunks = _split_by_chunks(text, chunk_size=60000)
        merged: dict = {"video_analysis": {}, "games": []}

        for idx, chunk in enumerate(chunks):
            user_content = _build_user_content(chunk, title)
            try:
                async with httpx.AsyncClient(timeout=600) as client:
                    resp = await client.post(
                        f"{base}/v1/chat/completions",
                        json={
                            "model": model,
                            "response_format": {"type": "json_object"},
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_content},
                            ],
                        },
                    )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"]
                result = self._parse_json(raw)
                if result:
                    merged["games"].extend(result.get("games", []))
                    if not merged["video_analysis"]:
                        merged["video_analysis"] = result.get("video_analysis", {})
                    logger.info("Ollama chunk %d/%d: %d jogos extraidos", idx + 1, len(chunks), len(result.get("games", [])))
            except Exception as exc:
                logger.warning("Falha na extracao via Ollama (chunk %d): %s", idx, exc)

        if merged["games"]:
            va = merged.setdefault("video_analysis", {})
            va["games_detected_count"] = len(merged["games"])
            va["ideas_detected_count"] = sum(len(g.get("ideas", [])) for g in merged["games"])
            va["actionable_ideas_count"] = sum(
                1 for g in merged["games"] for i in g.get("ideas", []) if i.get("is_actionable")
            )
            return merged
        return None

    async def _extract_groq(self, text: str, title: str) -> dict | None:
        user_content = _build_user_content(text, title, max_chars=22000)
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "max_tokens": 4000,
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
            logger.warning("Falha na extracao via Groq: %s", exc)
            return None

    async def _extract_anthropic(self, text: str, title: str) -> dict | None:
        user_content = _build_user_content(text, title)
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-6",
                        "max_tokens": 8192,
                        "system": SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_content}],
                    },
                )
            resp.raise_for_status()
            raw = resp.json()["content"][0]["text"]
            return self._parse_json(raw)
        except Exception as exc:
            logger.warning("Falha na extracao via Anthropic: %s", exc)
            return None

    async def _extract_openai(self, text: str, title: str) -> dict | None:
        user_content = _build_user_content(text, title)
        try:
            async with httpx.AsyncClient(timeout=90) as client:
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
            logger.warning("Falha na extracao via OpenAI: %s", exc)
            return None

    def _parse_json(self, raw: str) -> dict | None:
        """Extrai o bloco JSON da resposta, mesmo que tenha texto ao redor."""
        raw = raw.strip()
        result = None
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            pass
        if result is None:
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        if result is None:
            import re
            match = re.search(r"(\{.*\})", raw, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        if result is None:
            logger.warning("Nao foi possivel parsear o JSON da resposta LLM")
            return None
        return _deduplicate_contradictions(result)


# Pares de mercados mutuamente exclusivos — manter apenas o de maior extraction_confidence
_OPPOSING_MARKETS: list[tuple[str, str]] = [
    ("over_0_5", "under_0_5"),
    ("over_1_5", "under_1_5"),
    ("over_2_5", "under_2_5"),
    ("over_3_5", "under_3_5"),
    ("btts_yes", "btts_no"),
    ("home_win", "away_win"),
]


def _deduplicate_contradictions(extraction: dict) -> dict:
    """Remove ideias com mercados opostos no mesmo jogo (ex: Over 2.5 e Under 2.5).

    Quando dois mercados são mutuamente exclusivos, mantém apenas o de maior
    extraction_confidence. Em empate, mantém o primeiro (ordem do LLM).
    """
    for game in extraction.get("games", []):
        ideas: list[dict] = game.get("ideas", [])
        to_remove: set[int] = set()

        for mkt_a, mkt_b in _OPPOSING_MARKETS:
            idxs_a = [i for i, idea in enumerate(ideas) if idea.get("market_type") == mkt_a]
            idxs_b = [i for i, idea in enumerate(ideas) if idea.get("market_type") == mkt_b]
            if not idxs_a or not idxs_b:
                continue

            conf_a = max(ideas[i].get("extraction_confidence", 0) or 0 for i in idxs_a)
            conf_b = max(ideas[i].get("extraction_confidence", 0) or 0 for i in idxs_b)

            if conf_a >= conf_b:
                to_remove.update(idxs_b)
                logger.info("Removendo mercado oposto '%s' (conf %.2f < %.2f)", mkt_b, conf_b, conf_a)
            else:
                to_remove.update(idxs_a)
                logger.info("Removendo mercado oposto '%s' (conf %.2f < %.2f)", mkt_a, conf_a, conf_b)

        if to_remove:
            game["ideas"] = [idea for i, idea in enumerate(ideas) if i not in to_remove]

    return extraction
