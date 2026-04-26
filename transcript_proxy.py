"""
Proxy local de transcrição do YouTube.
Roda no Windows (IP residencial) e recebe chamadas do Docker container.

Uso: python transcript_proxy.py
Porta: 8001
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

def get_transcript(video_id: str) -> dict:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
        try:
            tl = YouTubeTranscriptApi.list_transcripts(video_id)
        except (NoTranscriptFound, TranscriptsDisabled):
            return {"error": "no_transcript"}

        transcript = None
        for lang in ["pt", "pt-BR", "pt-PT", "en"]:
            try:
                transcript = tl.find_manually_created_transcript([lang])
                break
            except Exception:
                pass

        if not transcript:
            for lang in ["pt", "pt-BR", "pt-PT", "en"]:
                try:
                    transcript = tl.find_generated_transcript([lang])
                    break
                except Exception:
                    pass

        if not transcript:
            try:
                transcript = tl.find_generated_transcript([t.language_code for t in tl])
            except Exception:
                return {"error": "no_transcript"}

        data = transcript.fetch()
        return {
            "entries": [{"text": e["text"], "start": e["start"], "duration": e["duration"]} for e in data],
            "language_code": transcript.language_code,
            "source": "youtube_api",
        }
    except Exception as e:
        return {"error": str(e)}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parts = self.path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "transcript":
            video_id = urllib.parse.unquote(parts[1])
            result = get_transcript(video_id)
            body = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[proxy] {args[0]} {args[1]}")


if __name__ == "__main__":
    import sys
    # Instala dependência se necessário
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "youtube-transcript-api"])
        from youtube_transcript_api import YouTubeTranscriptApi

    port = 8001
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Proxy de transcrição rodando na porta {port}")
    print(f"Docker acessa via: http://host.docker.internal:{port}/transcript/VIDEO_ID")
    server.serve_forever()
