from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_reviewer
from app.models.result import GameResult
from app.models.sport import Game
from app.repositories.result_repository import ResultRepository
from app.services.evaluation_service import EvaluationService
from app.services.audit_service import AuditService
from app.schemas.result import GameResultCreate, GameResultResponse

router = APIRouter(prefix="/game-results", tags=["results"])


@router.post("", response_model=GameResultResponse, status_code=status.HTTP_201_CREATED)
async def create_result(
    body: GameResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    # Verify game exists
    game = await db.get(Game, body.game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jogo não encontrado")

    repo = ResultRepository(db)
    existing = await repo.get_by_game(body.game_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resultado já registrado para esse jogo. Use PATCH para atualizar.",
        )

    # Auto-derive missing fields
    data = body.model_dump()
    if data["home_score"] is not None and data["away_score"] is not None:
        if data["total_goals"] is None:
            data["total_goals"] = data["home_score"] + data["away_score"]
        if data["both_teams_scored"] is None:
            data["both_teams_scored"] = data["home_score"] > 0 and data["away_score"] > 0

    game_result = GameResult(**data, is_manual=True, created_by_user_id=current_user.id)
    game_result = await repo.create(game_result)

    # Auto-evaluate ideas
    eval_svc = EvaluationService(db)
    evaluated = await eval_svc.evaluate_game(body.game_id, game_result)

    # Update game status
    game.status = "finished"
    await db.flush()

    audit = AuditService(db)
    await audit.log(
        "result", game_result.id, "created",
        actor_user_id=current_user.id,
        payload={"game_id": body.game_id, "evaluated_ideas": evaluated},
    )
    await db.commit()
    return GameResultResponse.model_validate(game_result)


@router.patch("/{game_id}", response_model=GameResultResponse)
async def update_result(
    game_id: int,
    body: GameResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    repo = ResultRepository(db)
    existing = await repo.get_by_game(game_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resultado não encontrado")

    data = {k: v for k, v in body.model_dump().items() if v is not None and k != "game_id"}
    if "home_score" in data and "away_score" in data:
        data.setdefault("total_goals", data["home_score"] + data["away_score"])
        data.setdefault("both_teams_scored", data["home_score"] > 0 and data["away_score"] > 0)

    updated = await repo.update(existing, data)

    audit = AuditService(db)
    await audit.log(
        "result", existing.id, "updated",
        actor_user_id=current_user.id,
        payload={"game_id": game_id, "changes": data},
    )
    await db.commit()
    return GameResultResponse.model_validate(updated)


@router.get("/{game_id}", response_model=GameResultResponse)
async def get_result(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = ResultRepository(db)
    result = await repo.get_by_game(game_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resultado não encontrado")
    return GameResultResponse.model_validate(result)
