"""Server-side image URL fetching with SSRF protections.

Only public http(s) URLs are allowed; every redirect hop is re-validated.
Known residual risk: a DNS-rebinding TOCTOU window (resolve-check vs. connect)
— acceptable for a localhost MVP, revisit if this API is ever exposed.
"""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from app.utils.errors import BadRequestError
from app.utils.image import validate_and_normalize

MAX_REDIRECTS = 3
USER_AGENT = "ImagePromptAI/0.1 (reference-image fetcher)"


def assert_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise BadRequestError("Only http and https URLs are supported.")
    if parsed.username or parsed.password:
        raise BadRequestError("URLs with embedded credentials are not allowed.")
    host = parsed.hostname
    if not host:
        raise BadRequestError("The URL has no host.")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise BadRequestError("Could not resolve that host.")
    if not infos:
        raise BadRequestError("Could not resolve that host.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise BadRequestError("That URL points to a non-public address.")


async def download_image(
    url: str, *, max_bytes: int, max_pixels: int, timeout: float = 20.0
) -> tuple[bytes, str, int, int]:
    """Fetch an image from a public URL and normalize it for the pipeline.

    Returns (jpeg_bytes, mime, original_width, original_height) — same shape as
    validate_and_normalize, since the downloaded bytes go through it.
    """
    assert_public_http_url(url)
    async with httpx.AsyncClient(follow_redirects=False, timeout=timeout) as client:
        current = url
        resp = None
        for _hop in range(MAX_REDIRECTS + 1):
            assert_public_http_url(current)
            resp = await client.get(current, headers={"User-Agent": USER_AGENT})
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("location")
                if not location:
                    raise BadRequestError("The image host redirected without a target.")
                current = str(httpx.URL(resp.url).join(location))
                continue
            break
    assert resp is not None
    if resp.status_code != 200:
        raise BadRequestError(f"The image host returned HTTP {resp.status_code}.")
    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type and not content_type.startswith("image/"):
        raise BadRequestError("That URL does not point to an image.")
    if len(resp.content) > max_bytes:
        raise BadRequestError(
            f"The image at that URL is {len(resp.content) / 1_048_576:.1f} MB; "
            f"the limit is {max_bytes / 1_048_576:.0f} MB."
        )
    return validate_and_normalize(resp.content, max_bytes, max_pixels)
