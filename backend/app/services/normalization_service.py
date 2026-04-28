"""Serviço de normalização de transcrições.

Remove ruído (saudações, CTAs, propaganda) e normaliza o texto
para facilitar a segmentação e extração de ideias.
"""
from __future__ import annotations

import re

# Padrões de ruído que não contêm conteúdo analítico
_NOISE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\[música\]", re.IGNORECASE),
    re.compile(r"\[aplausos\]", re.IGNORECASE),
    re.compile(r"\[risadas?\]", re.IGNORECASE),
    re.compile(r"\buh+\b", re.IGNORECASE),
    re.compile(r"\bah+\b", re.IGNORECASE),
    re.compile(r"\bhmm+\b", re.IGNORECASE),
    re.compile(r"\bé+\s+é+\b", re.IGNORECASE),
    # Cabeçalhos de capítulo do YouTube
    re.compile(r"Cap[íi]tulo\s+\d+\s*:[^\n]*", re.IGNORECASE),
    # "[limpando a garganta]", "[ruído]", etc.
    re.compile(r"\[[^\]]{1,40}\]"),
    # Timestamps YouTube colados: "8:228 minutos e 22 segundos" — remove "MM:SSN"
    re.compile(r"\d{1,2}:\d{2}(?::\d{2})?\d*"),
    # Rótulos de tempo: "minutos e 22 segundos" (residuo apos remover timestamp colado)
    re.compile(r"\bminutos?\s+e\s+\d+\s+segundos?", re.IGNORECASE),
    # Rótulos de tempo isolados: "22 segundos", "8 minutos" — sem \b no final pois ficam colados
    re.compile(r"\b\d+\s+(?:minutos?|segundos?|horas?)", re.IGNORECASE),
]

# Frases de CTA / autopropaganda que não devem virar ideias
_CTA_PATTERNS: list[re.Pattern] = [
    re.compile(r"se inscreva.{0,40}canal", re.IGNORECASE),
    re.compile(r"curta.{0,20}vídeo", re.IGNORECASE),
    re.compile(r"ativa.{0,30}sininho", re.IGNORECASE),
    re.compile(r"deixa.{0,30}comentário", re.IGNORECASE),
    re.compile(r"link.{0,40}descrição", re.IGNORECASE),
    re.compile(r"telegram.{0,60}", re.IGNORECASE),
    re.compile(r"whatsapp.{0,60}grupo", re.IGNORECASE),
    re.compile(r"cadastr.{0,60}bônus", re.IGNORECASE),
]


class NormalizationService:
    def normalize(self, raw_text: str) -> str:
        """Retorna versão normalizada do texto de transcrição."""
        text = self._fix_encoding(raw_text)
        text = self._remove_noise(text)
        text = self._remove_cta_sentences(text)
        text = self._clean_whitespace(text)
        return text

    def _fix_encoding(self, text: str) -> str:
        # Corrige caracteres comuns mal-codificados
        replacements = {
            "â": "'",
            "Ã£": "ã",
            "Ã©": "é",
            "Ã§Ã£o": "ção",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    def _remove_noise(self, text: str) -> str:
        for pattern in _NOISE_PATTERNS:
            text = pattern.sub(" ", text)
        return text

    def _remove_cta_sentences(self, text: str) -> str:
        """Remove sentenças que são majoritariamente CTA/propaganda."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        cleaned = []
        for sentence in sentences:
            if not any(p.search(sentence) for p in _CTA_PATTERNS):
                cleaned.append(sentence)
        return " ".join(cleaned)

    def _clean_whitespace(self, text: str) -> str:
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()
