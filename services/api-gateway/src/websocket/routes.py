from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from src.websocket import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_endpoint(
    websocket: WebSocket,
):

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
