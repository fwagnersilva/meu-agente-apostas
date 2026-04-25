"""Integração com a YouTube Data API v3.

Busca vídeos novos em um canal usando o endpoint playlistItems.list
através da uploads playlist de cada canal.
"""
import re
from datetime import datetime, timezone
from dataclasses import dataclass
import httpx
from app.core.config import settings


@dataclass
class YoutubeVideoInfo:
    youtube_video_id: str
    youtube_url: str
    title: str
    description: str
    thumbnail_url: str | None
    published_at: datetime
    duration_seconds: int | None = None


class YouTubeService:
    BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def get_channel_external_id(self, channel_url: str) -> str | None:
        """Resolve o channel_external_id (UCxxxxxxx) a partir de uma URL do YouTube."""
        if not self._is_configured():
            return None

        handle = self._extract_handle(channel_url)
        channel_id_direct = self._extract_channel_id(channel_url)

        if channel_id_direct:
            return channel_id_direct

        async with httpx.AsyncClient(timeout=10) as client:
            if handle:
                resp = await client.get(
                    f"{self.BASE}/channels",
                    params={"part": "id", "forHandle": handle, "key": self.api_key},
                )
                data = resp.json()
                items = data.get("items", [])
                if items:
                    return items[0]["id"]
        return None

    async def fetch_new_videos(
        self,
        channel_external_id: str,
        since: datetime | None = None,
        max_results: int = 50,
    ) -> list[YoutubeVideoInfo]:
        """Retorna vídeos novos do canal desde `since`. Sem API key retorna lista vazia."""
        if not self._is_configured():
            return []

        async with httpx.AsyncClient(timeout=15) as client:
            uploads_playlist = await self._get_uploads_playlist(client, channel_external_id)
            if not uploads_playlist:
                return []

            videos = await self._list_playlist_items(client, uploads_playlist, max_results)

        if since:
            videos = [v for v in videos if v.published_at > since]

        return videos

    async def _get_uploads_playlist(self, client: httpx.AsyncClient, channel_id: str) -> str | None:
        resp = await client.get(
            f"{self.BASE}/channels",
            params={
                "part": "contentDetails",
                "id": channel_id,
                "key": self.api_key,
            },
        )
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return None
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    async def _list_playlist_items(
        self, client: httpx.AsyncClient, playlist_id: str, max_results: int
    ) -> list[YoutubeVideoInfo]:
        resp = await client.get(
            f"{self.BASE}/playlistItems",
            params={
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": min(max_results, 50),
                "key": self.api_key,
            },
        )
        data = resp.json()
        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            if not video_id:
                continue

            published_raw = snippet.get("publishedAt", "")
            try:
                published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
            except ValueError:
                published_at = datetime.now(timezone.utc)

            thumbs = snippet.get("thumbnails", {})
            thumbnail = (
                thumbs.get("high", {}).get("url")
                or thumbs.get("medium", {}).get("url")
                or thumbs.get("default", {}).get("url")
            )

            videos.append(
                YoutubeVideoInfo(
                    youtube_video_id=video_id,
                    youtube_url=f"https://www.youtube.com/watch?v={video_id}",
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    thumbnail_url=thumbnail,
                    published_at=published_at,
                )
            )
        return videos

    @staticmethod
    def _extract_handle(url: str) -> str | None:
        match = re.search(r"youtube\.com/@([^/?&]+)", url)
        return match.group(1) if match else None

    @staticmethod
    def _extract_channel_id(url: str) -> str | None:
        match = re.search(r"youtube\.com/channel/(UC[^/?&]+)", url)
        return match.group(1) if match else None
