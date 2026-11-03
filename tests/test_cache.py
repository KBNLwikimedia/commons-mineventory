import pytest

from cutter.cache import CachedFetcher, FetchError, FileCache, RateLimiter


class FakeResponse:
    def __init__(self, status_code, content=b"", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)
        return self.responses.pop(0)


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.slept = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def test_rate_limiter_spaces_calls():
    clock = FakeClock()
    limiter = RateLimiter(1.0, clock=clock.clock, sleep=clock.sleep)
    limiter.wait()
    clock.now += 0.25
    limiter.wait()
    assert clock.slept == [pytest.approx(0.75)]


def test_cache_hit_skips_network(tmp_path):
    session = FakeSession([FakeResponse(200, b"data")])
    fetcher = CachedFetcher(FileCache(tmp_path), RateLimiter(0), "test", session=session)
    assert fetcher.get("https://example.org/a") == b"data"
    assert fetcher.get("https://example.org/a") == b"data"
    assert session.urls == ["https://example.org/a"]


def test_errors_are_not_cached(tmp_path):
    session = FakeSession([FakeResponse(404), FakeResponse(200, b"ok")])
    fetcher = CachedFetcher(FileCache(tmp_path), RateLimiter(0), "test", session=session)
    with pytest.raises(FetchError) as exc:
        fetcher.get("https://example.org/b")
    assert exc.value.status == 404
    assert fetcher.get("https://example.org/b") == b"ok"


def test_maxlag_is_retried_after_the_advised_wait(tmp_path):
    lagged = FakeResponse(200, b'{"error": {"code": "maxlag", "lag": 7}}', {"Retry-After": "7"})
    session = FakeSession([lagged, FakeResponse(503, b"", {"Retry-After": "2"}), FakeResponse(200, b'{"ok": 1}')])
    slept = []
    fetcher = CachedFetcher(FileCache(tmp_path), RateLimiter(0), "test", session=session, sleep=slept.append)
    assert fetcher.get("https://example.org/api") == b'{"ok": 1}'
    assert slept == [7, 2]


def test_maxlag_gives_up_after_a_few_tries(tmp_path):
    session = FakeSession([FakeResponse(503) for _ in range(4)])
    fetcher = CachedFetcher(FileCache(tmp_path), RateLimiter(0), "test", session=session, sleep=lambda s: None)
    with pytest.raises(FetchError):
        fetcher.get("https://example.org/api")
    assert len(session.urls) == 4


def test_cached_answers_expire_with_max_age(tmp_path):
    now = [1000.0]
    cache = FileCache(tmp_path, clock=lambda: now[0])
    cache.set("k", b"old")
    import os

    os.utime(cache._path("k"), (1000.0, 1000.0))
    assert cache.get("k", max_age=60) == b"old"
    now[0] = 2000.0
    assert cache.get("k", max_age=60) is None
    assert cache.get("k") == b"old"  # without max_age it never expires


def test_store_false_skips_the_cache(tmp_path):
    session = FakeSession([FakeResponse(200, b"big"), FakeResponse(200, b"big")])
    fetcher = CachedFetcher(FileCache(tmp_path), RateLimiter(0), "test", session=session)
    fetcher.get("https://example.org/original.tif", store=False)
    fetcher.get("https://example.org/original.tif", store=False)
    assert len(session.urls) == 2


def test_user_agent_is_set(tmp_path):
    session = FakeSession([])
    CachedFetcher(FileCache(tmp_path), RateLimiter(0), "CommonsCutter/0.1 (test)", session=session)
    assert session.headers["User-Agent"] == "CommonsCutter/0.1 (test)"
