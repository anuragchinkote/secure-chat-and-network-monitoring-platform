
import socket
import threading
import base64
import json

from key_provider import DevelopmentKeyProvider
from security import encrypt_message, decrypt_message

HOST = "127.0.0.1"
PORT = 55556

KEY_PROVIDER = DevelopmentKeyProvider()
KEY_ID = "default"
KEY = KEY_PROVIDER.get_key(KEY_ID)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def encode_message(text):
    nonce, ciphertext = encrypt_message(KEY, text)
    packet = {
        "key_id": KEY_ID,
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }
    return json.dumps(packet).encode("utf-8") + b"\n"


def decode_message(data):
    packet = json.loads(data.decode("utf-8"))
    key_id = packet["key_id"]
    key = KEY_PROVIDER.get_key(key_id)

    nonce = base64.b64decode(packet["nonce"], validate=True)
    ciphertext = base64.b64decode(packet["ciphertext"], validate=True)

    return decrypt_message(key, nonce, ciphertext)


nickname = input("Choose a nickname: ")

try:
    client.connect((HOST, PORT))
except OSError as exc:
    print(f"Could not connect to server: {exc}")
    raise SystemExit(1)


def receive():
    buffer = b""

    try:
        while True:
            data = client.recv(4096)

            if not data:
                break

            buffer += data

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)

                if not line:
                    continue

                if line == b"NICK":
                    client.sendall(nickname.encode("ascii"))
                    continue

                try:
                    message = decode_message(line)
                    print(message)
                except (ValueError, KeyError, TypeError, UnicodeDecodeError):
                    # Server status messages are plaintext for now.
                    print(line.decode("utf-8", errors="replace"))

    except (OSError, ConnectionError):
        pass
    finally:
        print("Disconnected from server.")
        client.close()


def write():
    try:
        while True:
            text = input()

            if text.lower() == "/quit":
                break

            message = f"{nickname}: {text}"
            client.sendall(encode_message(message))

    except (OSError, EOFError):
        pass
    finally:
        client.close()


receive_thread = threading.Thread(target=receive, daemon=True)
receive_thread.start()

write()
