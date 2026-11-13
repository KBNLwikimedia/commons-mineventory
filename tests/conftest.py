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

    # A rendered page for action=parse (the preview of the wikitext): a little
    # of what Commons sends, including what the app has to strip.
    PARSED = (
        '<div class="mw-parser-output"><style>.x{color:red}</style>'
        '<table class="fileinfotpl"><tr><td>Description</td><td>{text}</td></tr></table>'
        '<img src="//upload.wikimedia.org/x.png"><a href="/wiki/Category:Test" onclick="evil()">Test</a>'
        '<script>alert(1)</script><span style="background:url(http://x)">bg</span></div>'
    )

    def post(self, url, data, max_age=None):
        self.calls.append(url)
        if data.get("action") == "parse":
            first = data["text"].splitlines()[0] if data["text"] else ""
            return json.dumps({"parse": {"text": self.PARSED.replace("{text}", first)}}).encode()
        raise FetchError(url, "HTTP 404", status=404)


# Fakes for the Meta Model API (requests.Session.post), shared by the detector and
# description tests: `body` or `response` may be an exception, which is then raised.
class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


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
    app = create_app(Config(), commons_client=client)
    app.testing = True  # as locally: checks meant for a server are tested on purpose (test_api)
    return app


@pytest.fixture
def http(app):
    return app.test_client()
