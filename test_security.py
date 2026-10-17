
import os

import pytest

from security import encrypt_message, decrypt_message


def test_encrypt_decrypt_round_trip():
    key = os.urandom(32)
    message = "Hello from the secure chatroom!"

    nonce, ciphertext = encrypt_message(key, message)
    recovered = decrypt_message(key, nonce, ciphertext)

    assert recovered == message


def test_tampered_ciphertext_is_rejected():
    key = os.urandom(32)
    message = "Sensitive network message"

    nonce, ciphertext = encrypt_message(key, message)

    tampered = bytearray(ciphertext)
    tampered[0] ^= 1

    with pytest.raises(Exception):
        decrypt_message(key, nonce, bytes(tampered))


def test_wrong_key_is_rejected():
    key = os.urandom(32)
    wrong_key = os.urandom(32)
    message = "Test wrong key"

    nonce, ciphertext = encrypt_message(key, message)

    with pytest.raises(Exception):
        decrypt_message(wrong_key, nonce, ciphertext)


def test_invalid_key_length_is_rejected():
    with pytest.raises(ValueError):
        encrypt_message(b"short", "This should fail")
