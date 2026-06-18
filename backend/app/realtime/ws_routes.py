"""
ws_routes.py — Endpoint WebSocket para clientes (dashboard / app móvil).

El cliente se conecta a:  ws://host/ws?token=<JWT>
y recibe en tiempo real: posiciones, alertas y cambios de estado de ánimo.
"""
from __future__ import annotations

import uuid

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.security import decode_access_token
from app.realtime.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Autenticación por JWT en el query string
    try:
        payload = decode_access_token(token)
        user_id = payload["sub"]
        uuid.UUID(user_id)  # valida formato
    except (jwt.PyJWTError, KeyError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user_id, websocket)
    await websocket.send_json({"type": "connected", "user_id": user_id})
    try:
        while True:
            # Mantiene viva la conexión; el cliente puede enviar pings/subscripciones
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
    except Exception:
        await manager.disconnect(user_id, websocket)
