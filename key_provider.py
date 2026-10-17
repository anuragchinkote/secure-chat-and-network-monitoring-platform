
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

load_dotenv()


class KeyProvider(ABC):
    """Interface for supplying symmetric encryption keys."""

    @abstractmethod
    def get_key(self, key_id: str = "default") -> bytes:
        """Return a key identified by key_id."""
        raise NotImplementedError


class DevelopmentKeyProvider(KeyProvider):
    """Load a shared development key from the environment."""

    def __init__(self):
        value = os.environ.get("CHAT_DEV_KEY")

        if not value:
            raise RuntimeError(
                "CHAT_DEV_KEY is missing from the environment"
            )

        try:
            self.key = bytes.fromhex(value)
        except ValueError as exc:
            raise RuntimeError(
                "CHAT_DEV_KEY must be hexadecimal"
            ) from exc

        if len(self.key) != 32:
            raise RuntimeError(
                "CHAT_DEV_KEY must decode to exactly 32 bytes"
            )

    def get_key(self, key_id: str = "default") -> bytes:
        if key_id != "default":
            raise KeyError(f"Unknown development key ID: {key_id}")

        return self.key


def get_development_key() -> bytes:
    """Backward-compatible helper for existing code."""
    return DevelopmentKeyProvider().get_key()
