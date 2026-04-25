from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.channel_repository import ChannelRepository
from app.repositories.tipster_repository import TipsterRepository
from app.services.audit_service import AuditService
from app.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse


class ChannelService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChannelRepository(db)
        self.audit = AuditService(db)

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[ChannelResponse]:
        channels = await self.repo.get_all(skip=skip, limit=limit)
        return [ChannelResponse.model_validate(c) for c in channels]

    async def get_by_id(self, channel_id: int) -> ChannelResponse:
        channel = await self.repo.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal não encontrado")
        return ChannelResponse.model_validate(channel)

    async def create(self, data: ChannelCreate, actor_id: int | None = None) -> ChannelResponse:
        tipster_repo = TipsterRepository(self.db)
        tipster = await tipster_repo.get_by_id(data.tipster_id)
        if not tipster:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipster não encontrado")

        channel = await self.repo.create(
            tipster_id=data.tipster_id,
            channel_name=data.channel_name,
            channel_url=data.channel_url,
            channel_external_id=data.channel_external_id,
            monitoring_frequency_minutes=data.monitoring_frequency_minutes,
        )
        await self.audit.log("channel", channel.id, "created", actor_id, {"channel_name": data.channel_name})
        return ChannelResponse.model_validate(channel)

    async def update(self, channel_id: int, data: ChannelUpdate, actor_id: int | None = None) -> ChannelResponse:
        channel = await self.repo.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal não encontrado")

        updates = data.model_dump(exclude_none=True)
        channel = await self.repo.update(channel, updates)
        await self.audit.log("channel", channel_id, "updated", actor_id, updates)
        return ChannelResponse.model_validate(channel)

    async def pause(self, channel_id: int, actor_id: int | None = None) -> ChannelResponse:
        return await self.update(channel_id, ChannelUpdate(monitoring_status="paused"), actor_id)

    async def activate(self, channel_id: int, actor_id: int | None = None) -> ChannelResponse:
        return await self.update(
            channel_id,
            ChannelUpdate(monitoring_status="active", is_active=True),
            actor_id,
        )
