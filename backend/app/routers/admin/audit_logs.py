import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permission
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.admin import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["admin-audit"])


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    actor_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    target_id: uuid.UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user: User = Depends(require_permission("audit.view")),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog)

    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if action:
        query = query.where(AuditLog.action == action)
    if target_type:
        query = query.where(AuditLog.target_type == target_type)
    if target_id:
        query = query.where(AuditLog.target_id == target_id)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = []
    for log in logs:
        actor_name = None
        if log.actor:
            actor_name = log.actor.full_name or log.actor.email
        items.append(AuditLogResponse(
            id=log.id,
            actor_id=log.actor_id,
            actor_name=actor_name,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at,
        ))

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 1,
    )
