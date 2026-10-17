
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_message(key: bytes, plaintext: str) -> tuple[bytes, bytes]:
    """Return (nonce, ciphertext) using AES-GCM."""
    if len(key) not in (16, 24, 32):
        raise ValueError("AES key must be 16, 24, or 32 bytes")

    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)

    return nonce, ciphertext


def decrypt_message(
    key: bytes,
    nonce: bytes,
    ciphertext: bytes,
) -> str:
    """Decrypt and authenticate an AES-GCM message."""
    cipher = AESGCM(key)
    plaintext = cipher.decrypt(nonce, ciphertext, None)

    return plaintext.decode("utf-8")
