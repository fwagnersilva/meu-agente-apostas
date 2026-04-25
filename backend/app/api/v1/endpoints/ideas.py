from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_reviewer
from app.models.review import IdeaReview
from app.repositories.idea_repository import IdeaRepository
from app.services.audit_service import AuditService
from app.schemas.game import IdeaResponse
from app.schemas.review import ReviewActionRequest, IdeaReviewResponse

router = APIRouter(tags=["ideas"])


@router.get("/ideas", response_model=list[IdeaResponse])
async def list_ideas(
    game_id: int | None = Query(default=None),
    video_id: int | None = Query(default=None),
    pending_review: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = IdeaRepository(db)
    if pending_review:
        ideas = await repo.get_pending_review(skip=skip, limit=limit)
    elif game_id is not None:
        ideas = await repo.get_by_game(game_id)
    elif video_id is not None:
        ideas = await repo.get_by_video(video_id)
    else:
        ideas = await repo.get_pending_review(skip=skip, limit=limit)
    return [IdeaResponse.model_validate(i) for i in ideas]


@router.get("/ideas/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = IdeaRepository(db)
    idea = await repo.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    return IdeaResponse.model_validate(idea)


@router.post("/review/ideas/{idea_id}", response_model=IdeaReviewResponse, status_code=status.HTTP_201_CREATED)
async def review_idea(
    idea_id: int,
    body: ReviewActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    repo = IdeaRepository(db)
    audit = AuditService(db)

    idea = await repo.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")

    valid_actions = {"approve", "edit", "reject", "split", "merge", "reassign_game"}
    if body.action_type not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"action_type deve ser um de: {', '.join(valid_actions)}",
        )

    previous_data = {
        "review_status": idea.review_status,
        "idea_type": idea.idea_type,
        "market_type": idea.market_type,
        "is_actionable": idea.is_actionable,
    }

    # Apply edits
    if body.action_type == "edit" and body.edited_data:
        allowed_fields = {
            "idea_type", "market_type", "selection_label", "sentiment_direction",
            "confidence_band", "belief_text", "fear_text", "entry_text",
            "avoid_text", "rationale_text", "is_actionable",
        }
        for field, value in body.edited_data.items():
            if field in allowed_fields:
                setattr(idea, field, value)

    new_status = "reviewed" if body.action_type in ("approve", "edit") else "rejected"
    await repo.update_review_status(idea_id, new_status)

    review = IdeaReview(
        idea_id=idea_id,
        reviewer_user_id=current_user.id,
        action_type=body.action_type,
        previous_data_json=previous_data,
        new_data_json=body.edited_data,
        review_notes=body.notes,
    )
    db.add(review)
    await db.flush()

    await audit.log(
        "game_idea", idea_id, f"review_{body.action_type}",
        actor_user_id=current_user.id,
        payload={"action": body.action_type, "notes": body.notes},
    )
    await db.commit()

    return IdeaReviewResponse.model_validate(review)
