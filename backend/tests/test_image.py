import base64

import pytest
from PIL import Image
import io

from app.utils.errors import (
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedFormatError,
)
from app.utils.image import (
    aspect_ratio_label,
    decode_data_url,
    orientation_label,
    sniff_format,
    validate_and_normalize,
)


def png_bytes(w=64, h=40, color=(10, 200, 30)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()


class TestDecodeDataUrl:
    def test_bare_base64(self):
        raw = b"hello"
        out, mime = decode_data_url(base64.b64encode(raw).decode())
        assert out == raw
        assert mime == ""

    def test_data_url(self):
        raw = png_bytes(4, 4)
        out, mime = decode_data_url("data:image/png;base64," + base64.b64encode(raw).decode())
        assert out == raw
        assert mime == "image/png"

    def test_empty_rejected(self):
        with pytest.raises(InvalidImageError):
            decode_data_url("")

    def test_bad_base64_rejected(self):
        with pytest.raises(InvalidImageError):
            decode_data_url("data:image/png;base64,QU@D=")


class TestSniffFormat:
    def test_png(self):
        assert sniff_format(png_bytes()) == "PNG"

    def test_jpeg(self):
        buf = io.BytesIO()
        Image.new("RGB", (8, 8)).save(buf, "JPEG")
        assert sniff_format(buf.getvalue()) == "JPEG"

    def test_gif_rejected(self):
        with pytest.raises(UnsupportedFormatError):
            sniff_format(b"GIF89a" + b"\x00" * 20)

    def test_text_rejected(self):
        with pytest.raises(UnsupportedFormatError):
            sniff_format(b"hello world, definitely not an image")


class TestValidateAndNormalize:
    def test_png_becomes_jpeg(self):
        out, mime, w, h = validate_and_normalize(png_bytes(), 10_000_000, 2048)
        assert mime == "image/jpeg"
        assert sniff_format(out) == "JPEG"
        assert (w, h) == (64, 40)

    def test_downscales_to_max_pixels(self):
        out, mime, w, h = validate_and_normalize(png_bytes(3000, 1000), 10_000_000, 2048)
        img = Image.open(io.BytesIO(out))
        assert max(img.size) <= 2048
        assert (w, h) == (3000, 1000)

    def test_corrupt_file_rejected(self):
        raw = png_bytes()
        with pytest.raises(InvalidImageError):
            validate_and_normalize(raw[:20], 10_000_000, 2048)

    def test_gif_rejected(self):
        buf = io.BytesIO()
        Image.new("P", (8, 8)).save(buf, "GIF")
        with pytest.raises(UnsupportedFormatError):
            validate_and_normalize(buf.getvalue(), 10_000_000, 2048)

    def test_oversize_rejected(self):
        with pytest.raises(ImageTooLargeError):
            validate_and_normalize(png_bytes(), 10, 2048)


class TestLabels:
    @pytest.mark.parametrize(
        "w,h,expected",
        [
            (1920, 1080, "16:9"),
            (1080, 1920, "9:16"),
            (600, 400, "3:2"),
            (1000, 1000, "1:1"),
            (64, 40, "16:10"),
            (700, 500, "7:5"),
        ],
    )
    def test_aspect_ratio(self, w, h, expected):
        assert aspect_ratio_label(w, h) == expected

    def test_orientation(self):
        assert orientation_label(100, 50) == "landscape"
        assert orientation_label(50, 100) == "portrait"
        assert orientation_label(50, 50) == "square"
