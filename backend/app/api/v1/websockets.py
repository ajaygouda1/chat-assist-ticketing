from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, event_id: int, websocket: WebSocket):
        await websocket.accept()
        if event_id not in self.active_connections:
            self.active_connections[event_id] = []
        self.active_connections[event_id].append(websocket)

    def disconnect(self, event_id: int, websocket: WebSocket):
        if event_id in self.active_connections:
            if websocket in self.active_connections[event_id]:
                self.active_connections[event_id].remove(websocket)

    async def broadcast_to_event(self, event_id: int, message: dict):
        if event_id in self.active_connections:
            for connection in self.active_connections[event_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

ws_manager = ConnectionManager()

@router.websocket("/ws/live-events/{event_id}")
async def websocket_endpoint(websocket: WebSocket, event_id: int):
    await ws_manager.connect(event_id, websocket)
    try:
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
            await ws_manager.broadcast_to_event(event_id, {"event": "PING_PONG", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(event_id, websocket)
