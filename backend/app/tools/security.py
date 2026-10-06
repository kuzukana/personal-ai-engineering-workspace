import asyncio
import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlparse

Resolver = Callable[..., list[tuple]]


def _is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return address.is_global and not address.is_multicast


async def resolve_public_http_url(
    url: str,
    resolver: Resolver = socket.getaddrinfo,
) -> list[str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http(s) URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are not allowed")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Localhost is not allowed")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        records = await asyncio.to_thread(
            resolver,
            hostname,
            port,
            0,
            socket.SOCK_STREAM,
        )
        if not records:
            raise ValueError("Hostname did not resolve") from None
        addresses = {record[4][0] for record in records}
    else:
        addresses = {str(address)}

    if any(not _is_public_address(value) for value in addresses):
        raise ValueError("URL resolves to a non-public network address")

    return sorted(addresses)


async def validate_public_http_url(url: str, resolver: Resolver = socket.getaddrinfo) -> str:
    await resolve_public_http_url(url, resolver)
    return url
