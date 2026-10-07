import base64
import io

import pytest
from PIL import Image

from app.main import app


def jpeg_bytes(w=32, h=24):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 100, 50)).save(buf, "JPEG")
    return buf.getvalue()


class TestFetchImageRejections:
    """SSRF / validation paths — these never touch the network."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost/x.png",
            "http://127.0.0.1/x.png",
            "http://192.168.0.10/x.png",
            "http://10.0.0.5/x.png",
            "http://169.254.1.2/x.png",
            "http://[::1]/x.png",
            "http://0.0.0.0/x.png",
        ],
    )
    def test_private_and_local_addresses_blocked(self, client, url):
        r = client.post("/api/fetch-image", json={"url": url})
        assert r.status_code == 400
        assert "non-public" in r.json()["error"]["message"]

    def test_non_http_scheme_blocked(self, client):
        r = client.post("/api/fetch-image", json={"url": "ftp://example.com/x.png"})
        assert r.status_code == 400

    def test_file_scheme_blocked(self, client):
        r = client.post("/api/fetch-image", json={"url": "file:///etc/passwd"})
        assert r.status_code == 400

    def test_embedded_credentials_blocked(self, client):
        r = client.post("/api/fetch-image", json={"url": "https://user:pass@example.com/x.png"})
        assert r.status_code == 400

    def test_unresolvable_host_blocked(self, client):
        r = client.post("/api/fetch-image", json={"url": "https://definitely-not-a-real-host-xyz987.invalid/x.png"})
        assert r.status_code == 400

    def test_empty_url_rejected(self, client):
        r = client.post("/api/fetch-image", json={"url": ""})
        assert r.status_code in (400, 422)


class TestFetchImageSuccess:
    def test_returns_data_url(self, client, monkeypatch):
        from app.api import routes_analysis

        async def fake_download(url, *, max_bytes, max_pixels, timeout=20.0):
            return jpeg_bytes(), "image/jpeg", 32, 24

        monkeypatch.setattr(routes_analysis, "download_image", fake_download)
        r = client.post("/api/fetch-image", json={"url": "https://images.example.com/photo.jpg"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert data["image"].startswith("data:image/jpeg;base64,")
        assert data["width"] == 32 and data["height"] == 24
        base64.b64decode(data["image"].split(",", 1)[1])


class TestModelsCharLimits:
    def test_midjourney_has_soft_limit(self, client):
        models = {m["id"]: m for m in client.get("/api/models").json()["data"]["models"]}
        assert models["midjourney"]["soft_char_limit"] == 1500
        assert models["generic"]["soft_char_limit"] is None
        assert app.state.runtime is not None  # app booted
