
from unittest.mock import MagicMock

import watcher


def test_check_server_when_reachable(monkeypatch):
    connection = MagicMock()
    connection.__enter__.return_value = connection

    monkeypatch.setattr(
        watcher.socket,
        "create_connection",
        lambda *args, **kwargs: connection,
    )

    status, latency_ms, error = watcher.check_server()

    assert status == "UP"
    assert latency_ms >= 0
    assert error is None


def test_check_server_when_unreachable(monkeypatch):
    def fail_connection(*args, **kwargs):
        raise OSError("Connection refused")

    monkeypatch.setattr(
        watcher.socket,
        "create_connection",
        fail_connection,
    )

    status, latency_ms, error = watcher.check_server()

    assert status == "DOWN"
    assert latency_ms is None
    assert "Connection refused" in error


def test_down_transition_sends_alert(monkeypatch):
    alerts = []

    monkeypatch.setattr(
        watcher,
        "send_alert",
        lambda subject, body: alerts.append((subject, body)) or True,
    )

    watcher.handle_status_change(
        "DOWN",
        "UP",
        "Connection refused",
    )

    assert len(alerts) == 1
    assert alerts[0][0] == "Chat server DOWN"
    assert "Connection refused" in alerts[0][1]


def test_recovery_transition_sends_alert(monkeypatch):
    alerts = []

    monkeypatch.setattr(
        watcher,
        "send_alert",
        lambda subject, body: alerts.append((subject, body)) or True,
    )

    watcher.handle_status_change("UP", "DOWN")

    assert len(alerts) == 1
    assert alerts[0][0] == "Chat server RECOVERED"


def test_unchanged_status_does_not_send_alert(monkeypatch):
    alerts = []

    monkeypatch.setattr(
        watcher,
        "send_alert",
        lambda subject, body: alerts.append((subject, body)) or True,
    )

    watcher.handle_status_change("DOWN", "DOWN")
    watcher.handle_status_change("UP", "UP")

    assert alerts == []
