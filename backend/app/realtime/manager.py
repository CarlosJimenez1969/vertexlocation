"""
manager.py — Gestor de conexiones WebSocket por usuario.

Mantiene un conjunto de conexiones activas y permite difundir mensajes
(posiciones en vivo, alertas, cambios de ánimo) al usuario correspondiente.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # usuario_id (str) -> set de WebSocket
        self._conns: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._conns[user_id].add(ws)

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[user_id].discard(ws)
            if not self._conns[user_id]:
                self._conns.pop(user_id, None)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Envía un mensaje JSON a todas las conexiones de un usuario."""
        conns = list(self._conns.get(user_id, []))
        if not conns:
            return
        data = json.dumps(message, default=str)
        muertas = []
        for ws in conns:
            try:
                await ws.send_text(data)
            except Exception:
                muertas.append(ws)
        for ws in muertas:
            await self.disconnect(user_id, ws)

    async def broadcast(self, message: dict) -> None:
        for user_id in list(self._conns.keys()):
            await self.send_to_user(user_id, message)

    @property
    def total_conexiones(self) -> int:
        return sum(len(s) for s in self._conns.values())


manager = ConnectionManager()
