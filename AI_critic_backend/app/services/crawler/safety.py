"""URL validation for crawler requests."""
import ipaddress
import os
import socket
from urllib.parse import urlparse


IS_DEVELOPMENT = (
    os.getenv("ENVIRONMENT", "development").lower() == "development"
)


def validate_public_http_url(url: str) -> None:
    """Validate HTTP(S) URLs and block non-public destinations.

    Loopback addresses are permitted only in development.
    """
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute HTTP and HTTPS URLs are supported.")

    try:
        addresses = {
            result[4][0]
            for result in socket.getaddrinfo(
                parsed.hostname,
                parsed.port,
                type=socket.SOCK_STREAM,
            )
        }
    except (socket.gaierror, ValueError) as error:
        raise ValueError("Unable to resolve the website hostname.") from error

    if not addresses:
        raise ValueError("Unable to resolve the website hostname.")

    for address in addresses:
        ip = ipaddress.ip_address(address)

        if ip.is_global:
            continue

        if IS_DEVELOPMENT and ip.is_loopback:
            continue

        raise ValueError(
            "URLs resolving to non-public addresses are not supported."
        )