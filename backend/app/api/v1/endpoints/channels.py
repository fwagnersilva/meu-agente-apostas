from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin, require_reviewer
from app.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse
from app.schemas.common import MessageResponse
from app.services.channel_service import ChannelService

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=list[ChannelResponse])
async def list_channels(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ChannelService(db).list_all(skip=skip, limit=limit)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ChannelService(db).get_by_id(channel_id)


@router.post("", response_model=ChannelResponse, status_code=201)
async def create_channel(
    data: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await ChannelService(db).create(data, actor_id=current_user.id)


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    data: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await ChannelService(db).update(channel_id, data, actor_id=current_user.id)


@router.post("/{channel_id}/pause", response_model=ChannelResponse)
async def pause_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    return await ChannelService(db).pause(channel_id, actor_id=current_user.id)


@router.post("/{channel_id}/activate", response_model=ChannelResponse)
async def activate_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    return await ChannelService(db).activate(channel_id, actor_id=current_user.id)


@router.post("/{channel_id}/trigger-monitor", response_model=MessageResponse)
async def trigger_monitor(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_reviewer),
):
    """Dispara manualmente o monitoramento de um canal específico."""
    from app.workers.tasks import monitor_channels_task
    monitor_channels_task.delay()
    return MessageResponse(message=f"Monitoramento do canal {channel_id} enfileirado.")
