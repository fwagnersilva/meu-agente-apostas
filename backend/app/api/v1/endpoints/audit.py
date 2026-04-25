from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.audit import AuditEvent, ProcessingJob

router = APIRouter(tags=["audit"])


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int | None
    event_type: str
    actor_user_id: int | None
    event_payload_json: dict | None
    created_at: datetime


class ProcessingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    entity_type: str | None
    entity_id: int | None
    status: str
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


@router.get("/audit-events", response_model=list[AuditEventResponse])
async def list_audit_events(
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    event_type: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    q = select(AuditEvent).order_by(desc(AuditEvent.created_at))
    if entity_type:
        q = q.where(AuditEvent.entity_type == entity_type)
    if entity_id is not None:
        q = q.where(AuditEvent.entity_id == entity_id)
    if event_type:
        q = q.where(AuditEvent.event_type == event_type)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return [AuditEventResponse.model_validate(e) for e in result.scalars().all()]


@router.get("/processing-jobs", response_model=list[ProcessingJobResponse])
async def list_processing_jobs(
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    q = select(ProcessingJob).order_by(desc(ProcessingJob.created_at))
    if status:
        q = q.where(ProcessingJob.status == status)
    if job_type:
        q = q.where(ProcessingJob.job_type == job_type)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return [ProcessingJobResponse.model_validate(j) for j in result.scalars().all()]
