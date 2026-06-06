import pytest
from cgimg.sizes import resolve_size


def test_known_aspects():
    assert resolve_size("16:9") == "1920x1080"
    assert resolve_size("1:1") == "1024x1024"
    assert resolve_size("3:4") == "1024x1536"
    assert resolve_size("9:16") == "1080x1920"


def test_raw_passthrough():
    assert resolve_size("1280x720") == "1280x720"


def test_unknown_raises():
    with pytest.raises(ValueError):
        resolve_size("banana")
