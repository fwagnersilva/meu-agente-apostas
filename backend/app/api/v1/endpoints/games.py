from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_reviewer
from app.repositories.game_repository import GameRepository
from app.repositories.idea_repository import IdeaRepository
from app.schemas.game import GameResponse, GameDetailResponse, IdeaResponse

router = APIRouter(tags=["games"])


def _idea_response(idea) -> IdeaResponse:
    data = IdeaResponse.model_validate(idea).model_dump()
    data["tipster_name"] = idea.tipster.display_name if idea.tipster else None
    return IdeaResponse(**data)


@router.get("/games", response_model=list[GameDetailResponse])
async def list_games(
    target_date: date = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = GameRepository(db)
    idea_repo = IdeaRepository(db)

    games = await repo.get_by_date(target_date or date.today())

    result = []
    for game in games:
        ideas = await idea_repo.get_by_game(game.id)
        game_data = GameResponse.model_validate(game).model_dump()
        detail = GameDetailResponse(**game_data, ideas=[_idea_response(i) for i in ideas])
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
    game_data = GameResponse.model_validate(game).model_dump()
    return GameDetailResponse(**game_data, ideas=[_idea_response(i) for i in ideas])


class ResultUpsert(BaseModel):
    home_score: int
    away_score: int


@router.put("/games/{game_id}/result", response_model=GameDetailResponse)
async def upsert_game_result(
    game_id: int,
    body: ResultUpsert,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    repo = GameRepository(db)
    idea_repo = IdeaRepository(db)

    game = await repo.get_by_id(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jogo não encontrado")

    await repo.upsert_result(game_id, body.home_score, body.away_score, current_user.id)
    await db.commit()

    game = await repo.get_by_id(game_id)
    ideas = await idea_repo.get_by_game(game_id)
    game_data = GameResponse.model_validate(game).model_dump()
    return GameDetailResponse(**game_data, ideas=[_idea_response(i) for i in ideas])
