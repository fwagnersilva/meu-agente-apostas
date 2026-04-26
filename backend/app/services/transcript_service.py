"""Serviço de transcrição de vídeos do YouTube.

Estratégia em cascata:
1. yt-dlp (legendas automáticas — mais resistente a bloqueios de IP)
2. youtube-transcript-api (fallback)
"""
from __future__ import annotations

import json
import logging
import subprocess
import tempfile
import os
from dataclasses import dataclass

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
    source: str          # yt_dlp | youtube_api | whisper | manual
    language_code: str
    has_timestamps: bool = True

    @property
    def full_text(self) -> str:
        return " ".join(e.text for e in self.entries)


COOKIES_PATH = "/app/youtube_cookies.txt"


class TranscriptService:
    PREFERRED_LANGS = ["pt", "pt-BR", "pt-PT", "en"]

    def _cookies_available(self) -> bool:
        return os.path.isfile(COOKIES_PATH)

    async def fetch(self, youtube_video_id: str) -> TranscriptResult | None:
        result = await self._from_ytdlp(youtube_video_id)
        if result:
            return result
        result = await self._from_youtube(youtube_video_id)
        return result

    async def _from_ytdlp(self, video_id: str) -> TranscriptResult | None:
        """Baixa legendas automáticas com yt-dlp."""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            with tempfile.TemporaryDirectory() as tmpdir:
                out_tmpl = os.path.join(tmpdir, "sub")
                for lang in ["pt", "en"]:
                    cmd = [
                        "yt-dlp",
                        "--write-auto-sub",
                        "--sub-langs", f"{lang}.*,{lang}",
                        "--skip-download",
                        "--sub-format", "json3",
                        "-o", out_tmpl,
                        "--no-warnings",
                        "--quiet",
                    ]
                    if self._cookies_available():
                        cmd += ["--cookies", COOKIES_PATH]
                    cmd.append(url)
                    subprocess.run(cmd, capture_output=True, timeout=60)

                    # Procura o arquivo gerado
                    for fname in os.listdir(tmpdir):
                        if fname.endswith(".json3"):
                            fpath = os.path.join(tmpdir, fname)
                            entries = self._parse_json3(fpath)
                            if entries:
                                return TranscriptResult(
                                    entries=entries,
                                    source="yt_dlp",
                                    language_code=lang,
                                    has_timestamps=True,
                                )
        except FileNotFoundError:
            logger.warning("yt-dlp não encontrado no PATH")
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp timeout para video_id=%s", video_id)
        except Exception as exc:
            logger.warning("yt-dlp falhou para video_id=%s: %s", video_id, exc)
        return None

    def _parse_json3(self, path: str) -> list[TranscriptEntry]:
        """Parseia arquivo .json3 de legenda do yt-dlp."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            entries = []
            for event in data.get("events", []):
                segs = event.get("segs")
                if not segs:
                    continue
                text = "".join(s.get("utf8", "") for s in segs).strip()
                if not text or text == "\n":
                    continue
                start_ms = event.get("tStartMs", 0)
                dur_ms = event.get("dDurationMs", 0)
                entries.append(TranscriptEntry(
                    text=text,
                    start=start_ms / 1000,
                    duration=dur_ms / 1000,
                ))
            return entries
        except Exception as exc:
            logger.warning("Falha ao parsear json3: %s", exc)
            return []

    async def _from_youtube(self, video_id: str) -> TranscriptResult | None:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

            kwargs = {}
            if self._cookies_available():
                kwargs["cookies"] = COOKIES_PATH

            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, **kwargs)
            except (NoTranscriptFound, TranscriptsDisabled):
                return None

            transcript = None
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
