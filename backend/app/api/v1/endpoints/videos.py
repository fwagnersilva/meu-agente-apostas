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
