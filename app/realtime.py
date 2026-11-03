from collections import defaultdict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections = defaultdict(set)

    async def connect(self, user_id: int, socket: WebSocket):
        await socket.accept()
        self.connections[user_id].add(socket)

    def disconnect(self, user_id: int, socket: WebSocket):
        self.connections[user_id].discard(socket)
        if not self.connections[user_id]:
            self.connections.pop(user_id, None)

    async def send(self, user_id: int, payload: dict):
        for socket in tuple(self.connections.get(user_id, ())):
            try:
                await socket.send_json(payload)
            except Exception:
                self.disconnect(user_id, socket)

manager = ConnectionManager()
