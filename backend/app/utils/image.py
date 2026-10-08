"""Image validation and normalization.

Trusts magic bytes and decoding, never file extensions.

Security semantics:
- MAX_IMAGE_BYTES caps the compressed upload.
- max_pixels is a DECODED PIXEL BUDGET (width * height) checked from the image
  header before any full decode, so decompression bombs are rejected cheaply.
- EXIF orientation is applied before dimensions are reported, so aspect ratios
  reflect what the viewer sees (critical for phone photos).
- Transparent images (RGBA/LA/palette transparency) are composited over a white
  background before RGB conversion, so arbitrary hidden pixel data under the
  alpha channel never leaks into analysis.
"""
import base64
import io
import re
from math import gcd

from PIL import Image, ImageOps

from app.utils.errors import (
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedFormatError,
)

ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}

# Tolerance for snapping measured ratios onto well-known labels.
COMMON_RATIOS: list[tuple[int, int]] = [
    (1, 1), (2, 1), (1, 2), (3, 2), (2, 3), (4, 3), (3, 4), (5, 4), (4, 5),
    (16, 9), (9, 16), (16, 10), (10, 16), (21, 9), (9, 21),
]


def decode_data_url(data_url: str) -> tuple[bytes, str]:
    """Split a base64 data URL (or bare base64) into raw bytes and declared mime type."""
    if not data_url or not data_url.strip():
        raise InvalidImageError("No image data was provided.")
    payload = data_url.strip()
    mime = ""
    if payload.startswith("data:"):
        header, sep, b64 = payload.partition(",")
        if not sep:
            raise InvalidImageError("Malformed image data URL.")
        mime = header[5:].split(";")[0].strip().lower()
        payload = b64
    try:
        compact = re.sub(r"\s+", "", payload)
        raw = base64.b64decode(compact, validate=True)
    except Exception:
        raise InvalidImageError("Image data is not valid base64.")
    if not raw:
        raise InvalidImageError("Image data is empty after decoding.")
    return raw, mime


def sniff_format(raw: bytes) -> str:
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if raw[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == "WEBP".encode():
        return "WEBP"
    raise UnsupportedFormatError("Unrecognized image format. Use PNG, JPG/JPEG or WEBP.")


def _flatten_to_rgb(img: Image.Image) -> Image.Image:
    """Convert to RGB, compositing transparency over white instead of exposing raw channels."""
    has_alpha = img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    )
    if has_alpha:
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")
    return img.convert("RGB")


def validate_and_normalize(
    raw: bytes, max_bytes: int, max_pixels: int, max_side: int = 2048
) -> tuple[bytes, str, int, int]:
    """Validate an uploaded image and re-encode it as a size-capped JPEG for the vision API.

    Order matters (spec v0.3):
    1. byte-size and magic-byte checks (cheap)
    2. header dimensions vs the decoded pixel budget (no full decode yet)
    3. EXIF transpose
    4. final dimensions + alpha flattening over white
    5. downscale to max_side (API cost control) and JPEG re-encode

    Returns (jpeg_bytes, mime, reported_width, reported_height) where the
    reported dimensions reflect the visually oriented image.
    """
    if not raw:
        raise InvalidImageError("Image data is empty.")
    if len(raw) > max_bytes:
        raise ImageTooLargeError(
            f"Image is {len(raw) / 1_048_576:.1f} MB; the limit is {max_bytes / 1_048_576:.0f} MB."
        )
    sniff_format(raw)
    try:
        with Image.open(io.BytesIO(raw)) as img:
            if img.format not in ALLOWED_FORMATS:
                raise UnsupportedFormatError(
                    f"Unsupported image format ({img.format}). Use PNG, JPG/JPEG or WEBP."
                )
            # Header read only: Pillow has not decoded pixel data yet.
            width, height = img.size
            if width * height > max_pixels:
                raise ImageTooLargeError(
                    f"Image decodes to {width} × {height} ({width * height:,} pixels); "
                    f"the limit is {max_pixels:,} pixels."
                )
            img = ImageOps.exif_transpose(img)
            width, height = img.size
            rgb = _flatten_to_rgb(img)
    except (UnsupportedFormatError, InvalidImageError, ImageTooLargeError):
        raise
    except Exception:
        raise InvalidImageError("The image is corrupted or cannot be decoded.")

    try:
        rgb.thumbnail((max_side, max_side), Image.LANCZOS)
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=90)
        return buf.getvalue(), "image/jpeg", width, height
    except Exception:
        raise InvalidImageError("Failed to re-encode the image for analysis.")


def aspect_ratio_label(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        return ""
    g = gcd(width, height)
    rw, rh = width // g, height // g
    ratio = rw / rh
    for cw, ch in COMMON_RATIOS:
        if abs(ratio - cw / ch) <= 0.015:
            return f"{cw}:{ch}"
    return f"{rw}:{rh}"


def orientation_label(width: int, height: int) -> str:
    if width > height:
        return "landscape"
    if height > width:
        return "portrait"
    return "square"
