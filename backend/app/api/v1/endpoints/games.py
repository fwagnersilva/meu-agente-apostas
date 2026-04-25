from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.sport import Game
from app.models.idea import GameIdea
from app.repositories.game_repository import GameRepository
from app.repositories.idea_repository import IdeaRepository
from app.schemas.game import GameResponse, GameDetailResponse, IdeaResponse

router = APIRouter(tags=["games"])


@router.get("/games", response_model=list[GameDetailResponse])
async def list_games(
    target_date: date = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = GameRepository(db)
    idea_repo = IdeaRepository(db)

    if target_date:
        games = await repo.get_by_date(target_date)
    else:
        games = await repo.get_by_date(date.today())

    result = []
    for game in games:
        ideas = await idea_repo.get_by_game(game.id)
        detail = GameDetailResponse.model_validate(game)
        detail.ideas = [IdeaResponse.model_validate(i) for i in ideas]
        result.append(detail)
    return result


@router.get("/games/{game_id}", response_model=GameDetailResponse)
async def get_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = GameRepository(db)
    idea_repo = IdeaRepository(db)

    game = await repo.get_by_id(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jogo não encontrado")

    ideas = await idea_repo.get_by_game(game_id)
    detail = GameDetailResponse.model_validate(game)
    detail.ideas = [IdeaResponse.model_validate(i) for i in ideas]
    return detail
