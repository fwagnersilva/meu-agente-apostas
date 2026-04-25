"""Serviço de auditoria — append-only. Nunca atualiza ou remove registros."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditEvent


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        entity_type: str,
        entity_id: int | None,
        event_type: str,
        actor_user_id: int | None = None,
        payload: dict | None = None,
    ) -> None:
        event = AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            event_payload_json=payload,
        )
        self.db.add(event)
        await self.db.flush()
