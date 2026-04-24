from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AuditEvent(Base):
    """Ledger append-only de todas as ações relevantes do sistema.

    Nunca deve ter UPDATE ou DELETE. Toda ação gera um novo registro.
    """
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # channel | video | video_analysis | transcript | idea | result | evaluation | user
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    # created | updated | deleted | processed | failed | reviewed | evaluated | reprocessed
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    actor: Mapped["User | None"] = relationship("User")


class ProcessingJob(Base):
    """Controle de jobs assíncronos de processamento."""
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # process_video | monitor_channels | evaluate_ideas | transcribe
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
