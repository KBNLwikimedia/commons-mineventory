import json
import re
from pathlib import Path
from urllib.parse import unquote

import pytest

from cutter import create_app
from cutter.cache import FetchError
from cutter.commons import CommonsClient
from cutter.config import Config

FIXTURES = Path(__file__).parent / "fixtures"
COMMONS = FIXTURES / "commons"

ALBUM = "File:Album amicorum van Jacob van Bronckhorst van Batenburg (8077131573).jpg"
ALBUM_MID = "M28830642"
BOOK_OF_HOURS_MID = "M83565772"
PDF_MID = "M115782147"

# Recorded on 3-11-2026 with tests/record_commons.py (read-only requests).
INDEX = json.loads((COMMONS / "index.json").read_text(encoding="utf-8"))


def _without_width(url):
    return re.sub(r"&iiurlparam=[^&]*", "", re.sub(r"iiurlwidth=\d+", "iiurlwidth=", url))


def _image_name(url):
    """The file name in an upload/thumb URL (for matching originals and other sizes)."""
    path = unquote(url.split("?")[0])
    match = re.search(r"/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/]+)", path)
    return match.group(1) if match else None


class FixtureFetcher:
    """Serves recorded responses; unknown URLs behave like a 404.

    Thumbnail requests for another width are answered with the recorded one,
    and the original of a file with its recorded (small) thumbnail: the app
    scales boxes by image width, so cut-outs still line up."""

    def __init__(self, extra=None):
        self.calls = []
        self.extra = extra or {}

    def get(self, url, max_age=None, store=True):
        self.calls.append(url)
        if url in self.extra:
            value = self.extra[url]
            return value if isinstance(value, bytes) else json.dumps(value).encode()
        name = INDEX.get(url)
        if name is None and "api.php" in url and "iiurlwidth=" in url:
            wanted = _without_width(url)
            name = next((v for k, v in INDEX.items() if _without_width(k) == wanted), None)
        if name is None and ("upload.wikimedia.org" in url or "thumb.wikimedia.org" in url):
            image = _image_name(url)
            name = next((v for k, v in INDEX.items() if "api.php" not in k and _image_name(k) == image), None)
        if name is None:
            raise FetchError(url, "HTTP 404", status=404)
        return (COMMONS / name).read_bytes()


@pytest.fixture
def fetcher():
    return FixtureFetcher()


@pytest.fixture
def client(fetcher, tmp_path):
    return CommonsClient(fetcher, cache_dir=tmp_path / "cache")


@pytest.fixture
def album(client):
    return client.load_file(ALBUM)


@pytest.fixture
def book(client):
    return client.load_file(BOOK_OF_HOURS_MID)


@pytest.fixture
def app(client, tmp_path, monkeypatch):
    monkeypatch.setenv("UITVOER_DIR", str(tmp_path / "uitvoer"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("VITE_DEV", "uit")
    return create_app(Config(), commons_client=client)


@pytest.fixture
def http(app):
    return app.test_client()
