from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.tipster_repository import TipsterRepository
from app.services.audit_service import AuditService
from app.schemas.tipster import TipsterCreate, TipsterUpdate, TipsterResponse, TipsterWithStats


class TipsterService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TipsterRepository(db)
        self.audit = AuditService(db)

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[TipsterResponse]:
        tipsters = await self.repo.get_all(skip=skip, limit=limit)
        return [TipsterResponse.model_validate(t) for t in tipsters]

    async def get_with_stats(self, tipster_id: int) -> TipsterWithStats:
        tipster = await self.repo.get_by_id(tipster_id)
        if not tipster:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipster não encontrado")

        total_channels = await self.repo.count_channels(tipster_id)
        total_ideas = await self.repo.count_ideas(tipster_id)
        total_actionable = await self.repo.count_actionable_ideas(tipster_id)

        return TipsterWithStats(
            **TipsterResponse.model_validate(tipster).model_dump(),
            total_channels=total_channels,
            total_ideas=total_ideas,
            total_actionable_ideas=total_actionable,
        )

    async def create(self, data: TipsterCreate, actor_id: int | None = None) -> TipsterResponse:
        tipster = await self.repo.create(
            name=data.name,
            display_name=data.display_name,
            bio=data.bio,
            notes=data.notes,
        )
        await self.audit.log("tipster", tipster.id, "created", actor_id, {"name": data.name})
        return TipsterResponse.model_validate(tipster)

    async def update(self, tipster_id: int, data: TipsterUpdate, actor_id: int | None = None) -> TipsterResponse:
        tipster = await self.repo.get_by_id(tipster_id)
        if not tipster:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipster não encontrado")

        updates = data.model_dump(exclude_none=True)
        tipster = await self.repo.update(tipster, updates)
        await self.audit.log("tipster", tipster_id, "updated", actor_id, updates)
        return TipsterResponse.model_validate(tipster)

    async def deactivate(self, tipster_id: int, actor_id: int | None = None) -> TipsterResponse:
        return await self.update(tipster_id, TipsterUpdate(status="inactive"), actor_id)
