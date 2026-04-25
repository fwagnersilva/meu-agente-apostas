from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.video import VideoAnalysis
from app.models.transcript import VideoTranscript, TranscriptSegment
from app.schemas.analysis import VideoAnalysisDetailResponse, VideoTranscriptResponse, TranscriptSegmentResponse

router = APIRouter(prefix="/video-analyses", tags=["analyses"])


@router.get("/{analysis_id}", response_model=VideoAnalysisDetailResponse)
async def get_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(VideoAnalysis).where(VideoAnalysis.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análise não encontrada")

    # Carrega transcript com segmentos
    t_result = await db.execute(
        select(VideoTranscript)
        .where(VideoTranscript.video_id == analysis.video_id)
    )
    transcript = t_result.scalar_one_or_none()

    transcript_response = None
    if transcript:
        seg_result = await db.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.transcript_id == transcript.id)
            .order_by(TranscriptSegment.start_seconds)
        )
        segments = list(seg_result.scalars().all())
        transcript_response = VideoTranscriptResponse(
            id=transcript.id,
            transcript_source=transcript.transcript_source,
            language_code=transcript.language_code,
            has_timestamps=transcript.has_timestamps,
            normalized_transcript_text=transcript.normalized_transcript_text,
            segments=[TranscriptSegmentResponse.model_validate(s) for s in segments],
        )

    return VideoAnalysisDetailResponse(
        **VideoAnalysisDetailResponse.model_validate(analysis).model_dump(exclude={"transcript"}),
        transcript=transcript_response,
    )


@router.get("/by-slug/{slug}", response_model=VideoAnalysisDetailResponse)
async def get_analysis_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(VideoAnalysis).where(VideoAnalysis.analysis_url_slug == slug)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análise não encontrada")
    return await get_analysis(analysis.id, db, _)


@router.get("/by-video/{video_id}", response_model=list[VideoAnalysisDetailResponse])
async def list_analyses_by_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(VideoAnalysis)
        .where(VideoAnalysis.video_id == video_id)
        .order_by(VideoAnalysis.created_at.desc())
    )
    analyses = list(result.scalars().all())
    return [VideoAnalysisDetailResponse.model_validate(a) for a in analyses]
