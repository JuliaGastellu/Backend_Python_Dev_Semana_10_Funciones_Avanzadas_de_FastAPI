from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUserDep, get_current_user
from app.exceptions import NotFoundError
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)])

def serialize(item):
    return {"id": item.id, "post_id": item.post_id, "message": item.message, "is_read": item.is_read, "created_at": item.created_at}

@router.get("")
async def list_notifications(user: CurrentUserDep, unread_only: bool = False, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    criteria = [Notification.user_id == user.id]
    unread = await db.scalar(select(func.count()).select_from(Notification).where(*criteria, Notification.is_read.is_(False)))
    if unread_only:
        criteria.append(Notification.is_read.is_(False))
    total = await db.scalar(select(func.count()).select_from(Notification).where(*criteria))
    items = await db.scalars(select(Notification).where(*criteria).order_by(Notification.id.desc()).offset(skip).limit(limit))
    return {"items": [serialize(item) for item in items], "total": total, "unread": unread, "skip": skip, "limit": limit}

@router.put("/{notification_id}/read")
async def mark_read(notification_id: int, user: CurrentUserDep, db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if item is None:
        raise NotFoundError("La notificación no existe")
    item.is_read = True
    await db.commit()
    return serialize(item)
