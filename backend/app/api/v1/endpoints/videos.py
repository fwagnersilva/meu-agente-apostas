from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_reviewer
from app.schemas.video import VideoResponse, VideoListResponse
from app.schemas.common import MessageResponse
from app.repositories.video_repository import VideoRepository

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("", response_model=list[VideoListResponse])
async def list_videos(
    channel_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = VideoRepository(db)
    videos = await repo.get_all(channel_id=channel_id, status=status, skip=skip, limit=limit)
    return [VideoListResponse.model_validate(v) for v in videos]


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from fastapi import HTTPException, status
    repo = VideoRepository(db)
    video = await repo.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vídeo não encontrado")
    return VideoResponse.model_validate(video)


@router.post("/manual-analyze", status_code=201)
async def manual_analyze(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    """Cria vídeo com transcrição colada manualmente e extrai ideias via LLM."""
    from fastapi import HTTPException, status as http_status
    from datetime import datetime, timezone
    import hashlib, uuid
    from app.repositories.channel_repository import ChannelRepository
    from app.repositories.video_repository import VideoRepository
    from app.services.extraction_orchestrator_service import ExtractionOrchestratorService
    from app.models.video import Video, VideoAnalysis
    from app.models.transcript import VideoTranscript

    tipster_id = body.get("tipster_id")
    title = body.get("title", "Análise manual")
    transcript_text = body.get("transcript_text", "").strip()
    video_date = body.get("video_date")  # YYYY-MM-DD opcional

    if not transcript_text:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Transcrição vazia")

    # Busca primeiro canal do tipster
    channel_repo = ChannelRepository(db)
    channels = await channel_repo.get_by_tipster(tipster_id)
    if not channels:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Tipster sem canais cadastrados")
    channel = channels[0]

    # Cria registro de vídeo sintético
    fake_video_id = f"manual-{uuid.uuid4().hex[:12]}"
    published_at = None
    if video_date:
        try:
            published_at = datetime.strptime(video_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    video = Video(
        channel_id=channel.id,
        youtube_video_id=fake_video_id,
        youtube_url=f"https://manual/{fake_video_id}",
        title=title,
        published_at=published_at,
        status="processing",
    )
    db.add(video)
    await db.flush()

    # Salva transcrição
    transcript = VideoTranscript(
        video_id=video.id,
        raw_transcript_text=transcript_text,
        normalized_transcript_text=transcript_text,
        transcript_source="manual",
        language_code="pt",
        has_timestamps=False,
    )
    db.add(transcript)

    # Cria análise
    slug = f"manual-{video.id}-{uuid.uuid4().hex[:8]}"
    analysis = VideoAnalysis(video_id=video.id, analysis_url_slug=slug)
    db.add(analysis)
    await db.flush()

    # Extrai ideias via LLM
    orchestrator = ExtractionOrchestratorService(db)
    await orchestrator.run(
        analysis=analysis,
        normalized_text=transcript_text,
        video_title=title,
        tipster_id=tipster_id,
    )

    video.status = "analyzed" if analysis.analysis_status != "failed" else "failed"
    await db.commit()

    return {
        "video_id": video.id,
        "analysis_id": analysis.id,
        "analysis_status": analysis.analysis_status,
        "games_detected": analysis.games_detected_count,
        "ideas_detected": analysis.ideas_detected_count,
    }


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_reviewer),
):
    """Remove vídeo e todas análises, ideias e transcrições associadas."""
    from fastapi import HTTPException, status as http_status
    from sqlalchemy import text

    result = await db.execute(text("SELECT id FROM videos WHERE id = :id"), {"id": video_id})
    if not result.fetchone():
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Vídeo não encontrado")

    # Delete in FK dependency order (children first)
    await db.execute(text("""
        DELETE FROM idea_conditions WHERE idea_id IN (
            SELECT id FROM game_ideas WHERE video_id = :id
        )
    """), {"id": video_id})
    await db.execute(text("""
        DELETE FROM idea_reasons WHERE idea_id IN (
            SELECT id FROM game_ideas WHERE video_id = :id
        )
    """), {"id": video_id})
    await db.execute(text("""
        DELETE FROM idea_labels WHERE idea_id IN (
            SELECT id FROM game_ideas WHERE video_id = :id
        )
    """), {"id": video_id})
    await db.execute(text("DELETE FROM game_ideas WHERE video_id = :id"), {"id": video_id})
    await db.execute(text("""
        DELETE FROM video_analysis_reviews WHERE video_analysis_id IN (
            SELECT id FROM video_analyses WHERE video_id = :id
        )
    """), {"id": video_id})
    await db.execute(text("DELETE FROM video_analyses WHERE video_id = :id"), {"id": video_id})
    await db.execute(text("DELETE FROM video_transcripts WHERE video_id = :id"), {"id": video_id})
    await db.execute(text("DELETE FROM videos WHERE id = :id"), {"id": video_id})
    await db.commit()


@router.post("/{video_id}/reprocess", response_model=MessageResponse)
async def reprocess_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    """Reprocessa um vídeo. Cria nova análise sem remover a anterior (RN15)."""
    from fastapi import HTTPException, status as http_status
    from app.workers.tasks import process_video_task

    repo = VideoRepository(db)
    video = await repo.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Vídeo não encontrado")

    await repo.update_status(video, "queued")
    await db.commit()
    process_video_task.delay(video_id)
    return MessageResponse(message=f"Vídeo {video_id} enfileirado para reprocessamento.")
