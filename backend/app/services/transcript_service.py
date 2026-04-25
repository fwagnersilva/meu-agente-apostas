"""Serviço de transcrição de vídeos do YouTube.

Estratégia em cascata:
1. YouTube Transcript API (legendas automáticas/manuais — gratuito, sem quota)
2. Whisper local (fallback quando não há legenda disponível)

A fonte usada é registrada em `transcript_source` para rastreabilidade.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TranscriptEntry:
    text: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass
class TranscriptResult:
    entries: list[TranscriptEntry]
    source: str          # youtube_api | whisper | manual
    language_code: str
    has_timestamps: bool = True

    @property
    def full_text(self) -> str:
        return " ".join(e.text for e in self.entries)


class TranscriptService:
    PREFERRED_LANGS = ["pt", "pt-BR", "pt-PT", "en"]

    async def fetch(self, youtube_video_id: str) -> TranscriptResult | None:
        """Tenta obter transcrição. Retorna None se nenhuma fonte funcionar."""
        result = await self._from_youtube(youtube_video_id)
        if result:
            return result

        result = await self._from_whisper(youtube_video_id)
        return result

    async def _from_youtube(self, video_id: str) -> TranscriptResult | None:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            except (NoTranscriptFound, TranscriptsDisabled):
                return None

            transcript = None
            # Prioriza idiomas preferidos (manual > gerado automaticamente)
            for lang in self.PREFERRED_LANGS:
                try:
                    transcript = transcript_list.find_manually_created_transcript([lang])
                    break
                except Exception:
                    pass

            if not transcript:
                for lang in self.PREFERRED_LANGS:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        break
                    except Exception:
                        pass

            if not transcript:
                # Último recurso: qualquer disponível
                try:
                    transcript = transcript_list.find_generated_transcript(
                        [t.language_code for t in transcript_list]
                    )
                except Exception:
                    return None

            data = transcript.fetch()
            entries = [
                TranscriptEntry(text=e["text"], start=e["start"], duration=e["duration"])
                for e in data
            ]
            return TranscriptResult(
                entries=entries,
                source="youtube_api",
                language_code=transcript.language_code,
                has_timestamps=True,
            )

        except ImportError:
            logger.warning("youtube-transcript-api não instalado")
            return None
        except Exception as exc:
            logger.warning("Falha ao buscar transcript via YouTube API: %s", exc)
            return None

    async def _from_whisper(self, video_id: str) -> TranscriptResult | None:
        """Transcreve via Whisper local. Requer download do áudio."""
        try:
            import whisper
            import tempfile
            import subprocess

            youtube_url = f"https://www.youtube.com/watch?v={video_id}"

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            # Baixa áudio com yt-dlp (deve estar instalado no container)
            result = subprocess.run(
                ["yt-dlp", "-x", "--audio-format", "mp3", "-o", tmp_path, youtube_url],
                capture_output=True,
                timeout=120,
            )
            if result.returncode != 0:
                return None

            model = whisper.load_model("base")
            output = model.transcribe(tmp_path, language="pt")

            entries = [
                TranscriptEntry(
                    text=seg["text"].strip(),
                    start=seg["start"],
                    duration=seg["end"] - seg["start"],
                )
                for seg in output.get("segments", [])
            ]
            detected_lang = output.get("language", "pt")
            return TranscriptResult(
                entries=entries,
                source="whisper",
                language_code=detected_lang,
                has_timestamps=True,
            )

        except ImportError:
            logger.warning("whisper não instalado — fallback indisponível")
            return None
        except Exception as exc:
            logger.warning("Falha ao transcrever via Whisper: %s", exc)
            return None
