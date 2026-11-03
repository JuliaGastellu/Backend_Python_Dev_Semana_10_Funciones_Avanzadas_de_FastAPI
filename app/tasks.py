import json
import logging
from pathlib import Path
import aiofiles
from app.database import async_session_factory
from app.models.notification import Notification
from app.realtime import manager

logger = logging.getLogger("pulse.tasks")

async def append_event(filename: str, payload: dict):
    async with aiofiles.open(Path("var") / filename, "a", encoding="utf-8") as stream:
        await stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

async def analytics(user_id: int):
    await append_event("analytics.log", {"event": "registered", "user_id": user_id})

async def notify_comment(post_id: int, author_id: int, commenter_id: int):
    if author_id == commenter_id:
        return
    try:
        async with async_session_factory() as db:
            item = Notification(user_id=author_id, post_id=post_id, message=f"Recibí un comentario nuevo en el post {post_id}")
            db.add(item)
            await db.commit()
            await db.refresh(item)
            payload = {"id": item.id, "post_id": post_id, "message": item.message}
        await manager.send(author_id, payload)
        await append_event("outbox.log", {"recipient_user_id": author_id, **payload})
    except Exception:
        logger.exception("No pude procesar la notificación del post %s", post_id)
