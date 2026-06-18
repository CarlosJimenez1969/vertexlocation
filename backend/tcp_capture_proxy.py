"""
Proxy TCP de captura para depurar el rastreador.
Escucha en LISTEN_PORT, reenvía a Traccar (TARGET) y registra en hex los
bytes que envía el dispositivo (para identificar el protocolo y su ID).
"""
import binascii
import socket
import threading
import time

LISTEN_PORT = 6700
TARGET = ("127.0.0.1", 5015)  # huabao / JT808 en Traccar (puerto correcto)


def _ts():
    return time.strftime("%H:%M:%S")


def pipe(src, dst, log_device):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            if log_device:
                print(f"[{_ts()}] DISPOSITIVO -> {len(data)} bytes: {binascii.hexlify(data).decode()}", flush=True)
            dst.sendall(data)
    except Exception:
        pass
    finally:
        for s in (src, dst):
            try:
                s.close()
            except Exception:
                pass


def handle(client, addr):
    print(f"[{_ts()}] === CONEXION ENTRANTE desde {addr} ===", flush=True)
    try:
        up = socket.create_connection(TARGET, timeout=10)
    except Exception as e:
        print(f"[{_ts()}] No se pudo conectar a Traccar {TARGET}: {e}", flush=True)
        client.close()
        return
    threading.Thread(target=pipe, args=(client, up, True), daemon=True).start()
    threading.Thread(target=pipe, args=(up, client, False), daemon=True).start()


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", LISTEN_PORT))
    srv.listen(8)
    print(f"[{_ts()}] Proxy de captura escuchando en {LISTEN_PORT} -> Traccar {TARGET[1]} (huabao/JT808)", flush=True)
    while True:
        c, a = srv.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()


if __name__ == "__main__":
    main()
