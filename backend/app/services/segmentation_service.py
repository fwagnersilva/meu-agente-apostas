"""Serviço de segmentação de transcrições.

Divide o texto normalizado em blocos por tipo de conteúdo:
- intro / closing: saudações e encerramentos
- match_analysis: blocos que analisam um jogo específico
- methodology: discussão de método, apostas, trading
- promotional: propaganda e CTAs que escaparam da normalização
- unknown: blocos não classificados

A segmentação é feita com heurísticas de palavras-chave.
Cada segmento é salvo em `transcript_segments`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.transcript_service import TranscriptEntry


@dataclass
class Segment:
    raw_text: str
    normalized_text: str
    segment_type: str
    start_seconds: float | None = None
    end_seconds: float | None = None


# Palavras-chave por tipo (ordem de prioridade)
_KEYWORDS: dict[str, list[str]] = {
    "intro": [
        r"\bsejam?\s+bem[-\s]?vindo", r"\bbom\s+dia\b", r"\bboa\s+tarde\b",
        r"\bboa\s+noite\b", r"\bvamos\s+começar\b", r"\babrindo\s+o\s+vídeo\b",
    ],
    "closing": [
        r"\baté\s+(a\s+)?próxima\b", r"\bum\s+abraço\b", r"\bvaleu\s+galera\b",
        r"\bobrigad[oa]s?\b.{0,20}assistir", r"\bencerr(ar|ando)\b",
    ],
    "promotional": [
        r"\bse\s+inscrev", r"\blink\s+na\s+descrição\b", r"\btelegram\b",
        r"\bwhatsapp\b.{0,30}grupo", r"\bbônus\b.{0,30}cadastr",
        r"\bcasa\s+de\s+aposta", r"\bpatrocinador\b",
    ],
    "methodology": [
        r"\bgestão\s+de\s+banca\b", r"\bdisciplina\b.{0,30}aposta",
        r"\bstrategy\b", r"\bmétodo\b", r"\btrading\s+esportivo\b",
        r"\bpsicologia\b.{0,30}aposta", r"\brisco.{0,20}retorno\b",
    ],
    "match_analysis": [
        r"\b(mandante|visitante|casa|fora)\b",
        r"\bover\b", r"\bunder\b", r"\bbtts\b", r"\bambas\s+marcam\b",
        r"\bhandicap\b", r"\blive\b", r"\bpré[-\s]?jogo\b",
        r"\bplacar\b", r"\bgol\b", r"\bescalação\b", r"\breserva\b",
        r"\bforma\s+recente\b", r"\bconfrontodireto\b",
        r"\bpossível\s+entrada\b", r"\bentry\b", r"\bodds\b",
    ],
}

_COMPILED: dict[str, list[re.Pattern]] = {
    seg_type: [re.compile(p, re.IGNORECASE) for p in patterns]
    for seg_type, patterns in _KEYWORDS.items()
}

# Quanto texto mínimo (chars) para considerar um segmento de análise
_MIN_ANALYSIS_CHARS = 80


class SegmentationService:
    def segment_by_entries(self, entries: list[TranscriptEntry], normalized_text: str) -> list[Segment]:
        """Segmenta usando os timestamps das entradas da transcrição."""
        if not entries:
            return self._segment_text_only(normalized_text)

        # Agrupa entradas em janelas de ~60 segundos ou por virada de tipo
        windows = self._build_windows(entries)
        segments: list[Segment] = []
        for window in windows:
            raw = " ".join(e.text for e in window)
            normalized = normalized_text  # reutiliza o texto já normalizado globalmente
            seg_type = self._classify(raw)
            if len(raw.strip()) < 20:
                continue
            segments.append(
                Segment(
                    raw_text=raw,
                    normalized_text=raw,  # segmento já é sub-texto do normalizado
                    segment_type=seg_type,
                    start_seconds=window[0].start,
                    end_seconds=window[-1].end,
                )
            )
        return segments or self._segment_text_only(normalized_text)

    def segment_text(self, normalized_text: str) -> list[Segment]:
        """Segmenta sem timestamps — divide por sentenças e classifica."""
        return self._segment_text_only(normalized_text)

    def _segment_text_only(self, text: str) -> list[Segment]:
        """Divide o texto em blocos de ~400 palavras e classifica cada um."""
        words = text.split()
        block_size = 400
        segments: list[Segment] = []
        for i in range(0, len(words), block_size):
            chunk = " ".join(words[i : i + block_size])
            if len(chunk.strip()) < 20:
                continue
            segments.append(
                Segment(
                    raw_text=chunk,
                    normalized_text=chunk,
                    segment_type=self._classify(chunk),
                )
            )
        return segments

    def _build_windows(self, entries: list[TranscriptEntry], window_seconds: float = 60.0) -> list[list[TranscriptEntry]]:
        """Agrupa entradas em janelas de tempo de ~window_seconds."""
        if not entries:
            return []
        windows: list[list[TranscriptEntry]] = []
        current: list[TranscriptEntry] = [entries[0]]
        window_start = entries[0].start
        for entry in entries[1:]:
            if entry.start - window_start <= window_seconds:
                current.append(entry)
            else:
                windows.append(current)
                current = [entry]
                window_start = entry.start
        windows.append(current)
        return windows

    def _classify(self, text: str) -> str:
        scores: dict[str, int] = {seg_type: 0 for seg_type in _COMPILED}
        for seg_type, patterns in _COMPILED.items():
            for p in patterns:
                if p.search(text):
                    scores[seg_type] += 1

        # Prioridade explícita para intro/closing/promotional
        for priority in ("intro", "closing", "promotional"):
            if scores[priority] >= 1:
                return priority

        best = max(scores, key=lambda k: scores[k])
        if scores[best] == 0:
            # Heurística: texto longo sem classificação provavelmente é análise
            return "match_analysis" if len(text) >= _MIN_ANALYSIS_CHARS else "unknown"
        return best
