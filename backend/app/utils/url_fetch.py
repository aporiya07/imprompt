"""Server-side image URL fetching with SSRF protections.

Protections:
- only public http(s) URLs; every redirect hop is re-validated
- ``ip.is_global`` invariant (covers loopback, private, link-local, reserved,
  multicast, unspecified and CGNAT 100.64.0.0/10 in one check)
- streaming download: Content-Length is checked up front and the body is read
  in chunks, aborting the moment the byte budget is exceeded
- ``trust_env=False`` so proxy environment variables cannot silently redirect
  requests and break SSRF assumptions
- hostname resolution and Pillow decoding run in worker threads so the event
  loop is never blocked

Residual risk (documented, deliberately not "fixed" with a broken pinning
implementation): the connection is made by hostname after resolving once, so a
DNS-rebinding TOCTOU window remains. Full pinning requires a custom transport
that connects to a validated IP while preserving Host/SNI. Fine for a localhost
tool; revisit before exposing this API beyond the machine.
"""
import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from app.utils.errors import BadRequestError, ImageTooLargeError
from app.utils.image import validate_and_normalize

MAX_REDIRECTS = 3
USER_AGENT = "ImPrompt/0.3 (reference-image fetcher)"
CHUNK_SIZE = 64 * 1024


def _assert_public_ip(ip_str: str) -> None:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        raise BadRequestError("That URL resolves to an invalid address.")
    if not ip.is_global:
        raise BadRequestError("That URL points to a non-public address.")


async def assert_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise BadRequestError("Only http and https URLs are supported.")
    if parsed.username or parsed.password:
        raise BadRequestError("URLs with embedded credentials are not allowed.")
    host = parsed.hostname
    if not host:
        raise BadRequestError("The URL has no host.")
    try:
        infos = await asyncio.to_thread(socket.getaddrinfo, host, None)
    except socket.gaierror:
        raise BadRequestError("Could not resolve that host.")
    if not infos:
        raise BadRequestError("Could not resolve that host.")
    for info in infos:
        _assert_public_ip(info[4][0])


async def _read_stream(response: httpx.Response, max_bytes: int) -> bytes:
    declared = response.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > max_bytes:
        raise ImageTooLargeError(
            f"The image at that URL is {int(declared) / 1_048_576:.1f} MB; "
            f"the limit is {max_bytes / 1_048_576:.0f} MB."
        )
    buffer = bytearray()
    async for chunk in response.aiter_bytes(CHUNK_SIZE):
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise ImageTooLargeError(
                f"The image at that URL exceeds the {max_bytes / 1_048_576:.0f} MB limit."
            )
    return bytes(buffer)


async def download_image(
    url: str, *, max_bytes: int, max_pixels: int, max_side: int = 2048, timeout: float = 20.0
) -> tuple[bytes, str, int, int]:
    """Fetch an image from a public URL and normalize it for the pipeline.

    Returns (jpeg_bytes, mime, reported_width, reported_height).
    """
    await assert_public_http_url(url)
    raw: bytes | None = None
    async with httpx.AsyncClient(follow_redirects=False, trust_env=False, timeout=timeout) as client:
        current = url
        for _hop in range(MAX_REDIRECTS + 1):
            await assert_public_http_url(current)
            async with client.stream("GET", current, headers={"User-Agent": USER_AGENT}) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        raise BadRequestError("The image host redirected without a target.")
                    current = str(httpx.URL(response.url).join(location))
                    continue
                if response.status_code != 200:
                    raise BadRequestError(f"The image host returned HTTP {response.status_code}.")
                content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                if content_type and not content_type.startswith("image/"):
                    raise BadRequestError("That URL does not point to an image.")
                raw = await _read_stream(response, max_bytes)
                break
    if raw is None:
        raise BadRequestError("Too many redirects while fetching that image.")
    jpeg, mime, width, height = await asyncio.to_thread(
        validate_and_normalize, raw, max_bytes, max_pixels, max_side
    )
    return jpeg, mime, width, height
