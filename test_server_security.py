
import base64
import json
import socket
import threading
from unittest.mock import patch

from cryptography.exceptions import InvalidTag

import server
from security import encrypt_message


def test_tampered_packet_is_not_broadcast():
    key = server.KEY_PROVIDER.get_key("default")
    nonce, ciphertext = encrypt_message(
        key,
        "This message will be tampered with",
    )

    tampered = bytearray(ciphertext)
    tampered[0] ^= 1

    packet = {
        "key_id": "default",
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(tampered).decode("ascii"),
    }
    payload = json.dumps(packet).encode("utf-8") + b"\n"

    sender, handler_socket = socket.socketpair()

    with (
        patch.object(server, "broadcast") as mock_broadcast,
        patch.object(server, "disconnect"),
    ):
        thread = threading.Thread(
            target=server.handle,
            args=(handler_socket, "TestClient"),
        )
        thread.start()

        sender.sendall(payload)
        sender.shutdown(socket.SHUT_WR)
        thread.join(timeout=2)

        assert not thread.is_alive()
        mock_broadcast.assert_not_called()

    sender.close()
    handler_socket.close()
