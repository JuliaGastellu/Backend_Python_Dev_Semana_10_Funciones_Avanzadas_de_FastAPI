from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pathlib import Path
from app.database import async_session_factory
from app.models import User
from app.security import decode_token
from app.realtime import manager

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.get("/client", response_class=FileResponse)
async def client():
    return FileResponse(Path(__file__).resolve().parents[1] / "static/ws_client.html")

@router.websocket("/notifications")
async def notifications(socket: WebSocket, token: str = ""):
    try:
        payload = decode_token(token, "access")
        async with async_session_factory() as db:
            user = await db.get(User, int(payload["sub"]))
            if user is None or not user.is_active:
                raise ValueError("Usuario inválido")
            user_id = user.id
    except Exception:
        await socket.close(code=1008)
        return
    await manager.connect(user_id, socket)
    try:
        while True:
            message = await socket.receive_text()
            if message == "ping":
                await socket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, socket)
