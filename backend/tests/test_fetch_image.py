import base64
import io

import pytest
from PIL import Image

from app.main import app
from app.utils.errors import ImageTooLargeError


def jpeg_bytes(w=32, h=24):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 100, 50)).save(buf, "JPEG")
    return buf.getvalue()


class TestFetchImageRejections:
    """SSRF / validation paths: these never touch the network."""

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

        async def fake_download(url, *, max_bytes, max_pixels, max_side=2048, timeout=20.0):
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


class TestUrlSecurity:
    def test_cgnat_range_blocked(self, client):
        r = client.post("/api/fetch-image", json={"url": "http://100.64.0.10/x.png"})
        assert r.status_code == 400
        assert "non-public" in r.json()["error"]["message"]

    def test_cgnat_hostname_resolving_to_cgnat_blocked(self, client, monkeypatch):
        import app.utils.url_fetch as uf

        def fake_getaddrinfo(host, port):
            return [(None, None, None, "", ("100.64.1.5", 0))]

        monkeypatch.setattr(uf.socket, "getaddrinfo", fake_getaddrinfo)
        import asyncio

        with pytest.raises(Exception) as exc:
            asyncio.run(uf.assert_public_http_url("https://rebind.example/x.png"))
        assert "non-public" in str(exc.value)

    def test_trust_env_disabled(self):
        import inspect

        from app.utils import url_fetch

        source = inspect.getsource(url_fetch.download_image)
        assert "trust_env=False" in source

    def test_redirect_to_private_ip_blocked(self, monkeypatch):
        """Every redirect hop must be re-validated (SSRF)."""
        import asyncio

        import httpx

        import app.utils.url_fetch as uf

        public_host_calls = {"n": 0}

        async def fake_assert(url: str) -> None:
            # First hop (public) allowed; Location pointing at private must fail.
            if "evil.example" in url or "127.0.0.1" in url or "192.168." in url:
                raise uf.BadRequestError("That URL points to a non-public address.")
            public_host_calls["n"] += 1

        class FakeStream:
            def __init__(self, status_code, headers):
                self.status_code = status_code
                self.headers = headers
                self.url = httpx.URL("https://cdn.example.com/photo.jpg")

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def aiter_bytes(self, chunk_size=65536):
                if False:
                    yield b""

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            def stream(self, method, url, headers=None):
                if "cdn.example.com" in url:
                    return FakeStream(302, {"location": "http://127.0.0.1/secret.png"})
                return FakeStream(200, {"content-type": "image/jpeg"})

        monkeypatch.setattr(uf, "assert_public_http_url", fake_assert)
        monkeypatch.setattr(uf.httpx, "AsyncClient", FakeClient)

        with pytest.raises(Exception) as exc:
            asyncio.run(
                uf.download_image(
                    "https://cdn.example.com/photo.jpg",
                    max_bytes=1_000_000,
                    max_pixels=10_000_000,
                )
            )
        assert "non-public" in str(exc.value).lower() or "non-public" in repr(exc.value).lower()
        assert public_host_calls["n"] >= 1

    def test_oversized_content_length_rejected_before_read(self):
        import asyncio

        import httpx

        from app.utils.url_fetch import _read_stream

        async def run():
            request = httpx.Request("GET", "https://images.example.com/huge.png")
            response = httpx.Response(
                200, headers={"Content-Length": str(500_000_000), "Content-Type": "image/png"}, request=request
            )
            await _read_stream(response, 10_000_000)

        try:
            asyncio.run(run())
            raised = None
        except ImageTooLargeError as e:
            raised = e
        assert raised is not None and "the limit is 10 MB" in str(raised)

    def test_oversized_streaming_body_aborts(self):
        import asyncio

        import httpx

        from app.utils.url_fetch import _read_stream

        async def run():
            request = httpx.Request("GET", "https://images.example.com/huge.png")
            response = httpx.Response(200, content=b"x" * (12_000_000), request=request)
            await _read_stream(response, 10_000_000)

        try:
            asyncio.run(run())
            raised = None
        except ImageTooLargeError as e:
            raised = e
        assert raised is not None


class TestModelsCharLimits:
    def test_midjourney_has_soft_limit(self, client):
        models = {m["id"]: m for m in client.get("/api/models").json()["data"]["models"]}
        assert models["midjourney"]["soft_char_limit"] == 1500
        assert models["generic"]["soft_char_limit"] is None
        assert app.state.runtime is not None  # app booted
