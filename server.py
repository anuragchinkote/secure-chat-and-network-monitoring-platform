
import base64
import json
import signal
import socket
import threading
import time

from key_provider import DevelopmentKeyProvider
from security import decrypt_message
from cryptography.exceptions import InvalidTag

HOST = "127.0.0.1"
PORT = 55556

# Compatibility aliases used by monitor.py
host = HOST
port = PORT

KEY_PROVIDER = DevelopmentKeyProvider()

# Socket creation happens only when receive() starts.
server = None

clients = {}
clients_lock = threading.Lock()

running = threading.Event()
server_started = threading.Event()

started_at = time.time()

metrics = {
    "connections_total": 0,
    "messages_total": 0,
    "disconnects_total": 0,
    "send_errors_total": 0,
}


def send_system_message(client, message):
    """Send a plaintext, newline-terminated status message."""
    client.sendall(message.encode("utf-8") + b"\n")


def broadcast(message, exclude=None):
    """Broadcast one newline-delimited message."""
    packet = message + b"\n"

    with clients_lock:
        recipients = [
            client for client in clients
            if client is not exclude
        ]

    failed_clients = []

    for client in recipients:
        try:
            client.sendall(packet)
        except OSError:
            with clients_lock:
                metrics["send_errors_total"] += 1
            failed_clients.append(client)

    for client in failed_clients:
        disconnect(client)


def broadcast_system(message):
    broadcast(message.encode("utf-8"))


def disconnect(client):
    with clients_lock:
        nickname = clients.pop(client, None)

        if nickname is None:
            return

        metrics["disconnects_total"] += 1

    try:
        client.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass

    try:
        client.close()
    except OSError:
        pass

    print(f"{nickname} disconnected")

    if running.is_set():
        broadcast_system(f"{nickname} left the chat!")


def handle(client, nickname):
    buffer = b""

    try:
        while running.is_set():
            data = client.recv(4096)

            if not data:
                break

            buffer += data

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)

                if not line:
                    continue

                try:
                    packet = json.loads(line.decode("utf-8"))

                    key_id = packet["key_id"]
                    key = KEY_PROVIDER.get_key(key_id)

                    nonce = base64.b64decode(
                        packet["nonce"],
                        validate=True,
                    )
                    ciphertext = base64.b64decode(
                        packet["ciphertext"],
                        validate=True,
                    )

                    plaintext = decrypt_message(
                        key,
                        nonce,
                        ciphertext,
                    )

                    with clients_lock:
                        metrics["messages_total"] += 1

                    print(
                        f"[SECURE MESSAGE] {nickname}: {plaintext}"
                    )

                    # Forward the encrypted packet, not plaintext.
                    broadcast(line)

                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    UnicodeDecodeError,
                    InvalidTag,
                ) as exc:
                    print(f"Rejected message from {nickname}: {exc}")
    except OSError:
        pass
    finally:
        disconnect(client)


def metrics_report():
    while running.is_set():
        time.sleep(10)

        if not running.is_set():
            break

        with clients_lock:
            connected = len(clients)
            current_metrics = metrics.copy()

        uptime = int(time.time() - started_at)

        print(
            f"[METRICS] uptime={uptime}s "
            f"connected={connected} "
            f"connections={current_metrics['connections_total']} "
            f"messages={current_metrics['messages_total']} "
            f"disconnects={current_metrics['disconnects_total']} "
            f"send_errors={current_metrics['send_errors_total']}"
        )


def stop_server(signum=None, frame=None):
    """Stop the listener and close active client sockets."""
    running.clear()
    server_started.clear()

    listener = server

    if listener is not None:
        try:
            listener.close()
        except OSError:
            pass

    with clients_lock:
        active_clients = list(clients.keys())
        clients.clear()

    for client in active_clients:
        try:
            client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            client.close()
        except OSError:
            pass

    if signum is not None:
        print("\nServer stopped.")


def receive():
    global server

    listener = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )
    server = listener

    listener.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    try:
        listener.bind((HOST, PORT))
        listener.listen()

        running.set()
        server_started.set()

        print(f"Secure chat server listening on {HOST}:{PORT}")

        threading.Thread(
            target=metrics_report,
            daemon=True,
        ).start()

        while running.is_set():
            try:
                client, address = listener.accept()
            except OSError:
                break

            print(f"Connection from {address}")

            try:
                client.sendall(b"NICK\n")
                nickname = client.recv(1024).decode("ascii").strip()

                if not nickname:
                    client.close()
                    continue

                with clients_lock:
                    clients[client] = nickname
                    metrics["connections_total"] += 1

                print(f"Nickname: {nickname}")

                send_system_message(
                    client,
                    "Connected to the server",
                )
                broadcast_system(f"{nickname} joined the chat!")

                threading.Thread(
                    target=handle,
                    args=(client, nickname),
                    daemon=True,
                ).start()

            except (OSError, UnicodeDecodeError):
                try:
                    client.close()
                except OSError:
                    pass

    except OSError as exc:
        print(f"Server error: {exc}")

    finally:
        stop_server()
        server = None


if __name__ == "__main__":
    signal.signal(signal.SIGINT, stop_server)
    receive()
