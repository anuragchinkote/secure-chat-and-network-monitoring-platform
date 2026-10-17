
import time
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import monitor
import server


client = TestClient(monitor.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "tcp-chat-server"
    assert data["status"] in ("ok", "stopped")
    assert "uptime_seconds" in data


def test_metrics_endpoint():
    response = client.get("/metrics")

    assert response.status_code == 200

    data = response.json()
    assert "connections_total" in data
    assert "messages_total" in data
    assert "disconnects_total" in data
    assert "connected_clients" in data


def test_network_check_when_server_is_reachable(monkeypatch):
    mock_connection = MagicMock()
    monkeypatch.setattr(
        monitor.socket,
        "create_connection",
        lambda *args, **kwargs: mock_connection,
    )

    response = client.get("/network-check")

    assert response.status_code == 200
    assert response.json()["reachable"] is True
    assert "connect_latency_ms" in response.json()

    mock_connection.__enter__.assert_called_once()


def test_network_check_when_server_is_unreachable(monkeypatch):
    def fail_connection(*args, **kwargs):
        raise OSError("Connection refused")

    monkeypatch.setattr(
        monitor.socket,
        "create_connection",
        fail_connection,
    )

    response = client.get("/network-check")

    assert response.status_code == 200
    assert response.json()["reachable"] is False
    assert "error" in response.json()
