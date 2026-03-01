from fastapi import WebSocket
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(list)

    async def connect(self, lot_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[lot_id].append(websocket)

    def disconnect(self, lot_id: int, websocket: WebSocket):
        self.active_connections[lot_id].remove(websocket)

    async def broadcast(self, lot_id: int, message: dict):
        for connection in self.active_connections[lot_id]:
            await connection.send_json(message)


manager = ConnectionManager()
