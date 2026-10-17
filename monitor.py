
import socket
import time

from fastapi import FastAPI

import server

app = FastAPI(title="Chatroom Network Monitor")


@app.get("/health")
def health():
    return {
        "status": (
            "ok"
            if server.server_started.is_set()
            and server.running.is_set()
            else "stopped"
        ),
        "service": "tcp-chat-server",
        "uptime_seconds": round(
            time.time() - server.started_at, 2
        ),
    }


@app.get("/metrics")
def get_metrics():
    with server.clients_lock:
        connected_clients = len(server.clients)

    return {
        **server.metrics,
        "connected_clients": connected_clients,
        "uptime_seconds": round(
            time.time() - server.started_at, 2
        ),
    }


@app.get("/network-check")
def network_check():
    start = time.perf_counter()

    try:
        with socket.create_connection(
            (server.host, server.port), timeout=2
        ):
            latency_ms = (
                time.perf_counter() - start
            ) * 1000

        return {
            "host": server.host,
            "port": server.port,
            "reachable": True,
            "connect_latency_ms": round(latency_ms, 2),
        }

    except OSError as exc:
        return {
            "host": server.host,
            "port": server.port,
            "reachable": False,
            "error": str(exc),
        }


@app.get("/diagnostics/ports")
def scan_local_ports():
    ports = [22, 80, 443, 8000, server.port]
    results = []

    for port in ports:
        try:
            with socket.create_connection(
                ("127.0.0.1", port), timeout=0.5
            ):
                status = "open"
        except OSError:
            status = "closed_or_unreachable"

        results.append({
            "host": "127.0.0.1",
            "port": port,
            "status": status,
        })

    return {"results": results}
