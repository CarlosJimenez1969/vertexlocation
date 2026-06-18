import { useEffect, useRef, useState } from 'react';

/**
 * Conecta al WebSocket del backend (ws://host/ws?token=...) y entrega
 * el último mensaje recibido. Reconecta automáticamente.
 */
export function useRealtime() {
  const [lastMessage, setLastMessage] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('vx_token');
    if (!token) return;

    let reconnectTimer;
    let alive = true;

    const connect = () => {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
      // En dev, el backend corre en :8001
      const host = import.meta.env.DEV ? 'localhost:8001' : window.location.host;
      const ws = new WebSocket(`${proto}://${host}/ws?token=${token}`);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onmessage = (e) => {
        try {
          setLastMessage(JSON.parse(e.data));
        } catch {
          /* ping/pong */
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (alive) reconnectTimer = setTimeout(connect, 4000);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      alive = false;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  return { lastMessage, connected };
}
