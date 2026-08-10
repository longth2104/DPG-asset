import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.notification import Notification
from app.models.request import Request
from app.models.user import User
from app.schemas.notification import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification, Request.type, Request.status)
        .join(Request, Notification.request_id == Request.id)
        .where(Notification.recipient_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return [
        NotificationOut(
            id=n.id,
            type=n.type,
            request_id=n.request_id,
            request_type=request_type,
            request_status=request_status,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n, request_type, request_status in result.all()
    ]


@router.get("/unread-count", response_model=UnreadCountOut)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.recipient_id == user.id, Notification.is_read.is_(False))
    )
    return UnreadCountOut(count=result.scalar_one())


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    n = await db.get(Notification, notification_id)
    if not n or n.recipient_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    n.is_read = True
    await db.commit()


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()
