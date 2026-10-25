import socket

import pytest

from app.services.crawler.safety import validate_public_http_url


def test_rejects_loopback_url():
    with pytest.raises(ValueError, match="non-public"):
        validate_public_http_url("http://127.0.0.1:8000")


def test_accepts_publicly_resolved_url(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
        ],
    )

    validate_public_http_url("https://example.com")
