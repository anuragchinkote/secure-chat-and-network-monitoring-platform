
import pytest

from key_provider import DevelopmentKeyProvider


def test_default_key_is_32_bytes():
    provider = DevelopmentKeyProvider()

    assert len(provider.get_key("default")) == 32


def test_unknown_key_id_is_rejected():
    provider = DevelopmentKeyProvider()

    with pytest.raises(KeyError):
        provider.get_key("unknown-key")
