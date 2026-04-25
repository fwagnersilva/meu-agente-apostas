from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.schemas.tipster import TipsterCreate, TipsterUpdate, TipsterResponse, TipsterWithStats
from app.services.tipster_service import TipsterService

router = APIRouter(prefix="/tipsters", tags=["tipsters"])


@router.get("", response_model=list[TipsterResponse])
async def list_tipsters(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await TipsterService(db).list_all(skip=skip, limit=limit)


@router.get("/{tipster_id}", response_model=TipsterWithStats)
async def get_tipster(
    tipster_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await TipsterService(db).get_with_stats(tipster_id)


@router.post("", response_model=TipsterResponse, status_code=201)
async def create_tipster(
    data: TipsterCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await TipsterService(db).create(data, actor_id=current_user.id)


@router.patch("/{tipster_id}", response_model=TipsterResponse)
async def update_tipster(
    tipster_id: int,
    data: TipsterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await TipsterService(db).update(tipster_id, data, actor_id=current_user.id)


@router.delete("/{tipster_id}", response_model=TipsterResponse)
async def deactivate_tipster(
    tipster_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await TipsterService(db).deactivate(tipster_id, actor_id=current_user.id)
