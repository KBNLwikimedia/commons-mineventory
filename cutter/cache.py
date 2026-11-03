"""Local file cache and a rate-limited HTTP fetcher for Wikimedia requests.

Commons is used politely (functional design 5.2): an own User-Agent, about one
request per second on cache misses, and responses cached on disk. Unlike
Delpher, Commons pages change (descriptions, structured data), so cached API
answers can expire (`max_age`); files on upload.wikimedia.org never change
under the same URL and are kept until cleaned up.
"""

import hashlib
import threading
import time
from pathlib import Path

import requests


class FetchError(Exception):
    """Raised when a remote resource cannot be fetched."""

    def __init__(self, url, message, status=None):
        super().__init__(f"{message} ({url})")
        self.url = url
        self.status = status


class FileCache:
    """Stores raw response bytes on disk, keyed by a hash of the URL."""

    def __init__(self, directory, clock=time.time):
        self.directory = Path(directory)
        self._clock = clock

    def _path(self, key):
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self.directory / digest[:2] / digest

    def get(self, key, max_age=None):
        """The cached bytes, or None when absent or older than `max_age` seconds."""
        path = self._path(key)
        if not path.exists():
            return None
        if max_age is not None and self._clock() - path.stat().st_mtime > max_age:
            return None
        return path.read_bytes()

    def set(self, key, data):
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)


class RateLimiter:
    """Ensures at least `min_interval` seconds between consecutive calls (thread-safe)."""

    def __init__(self, min_interval, clock=time.monotonic, sleep=time.sleep):
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last = None

    def wait(self):
        with self._lock:
            now = self._clock()
            if self._last is not None:
                remaining = self.min_interval - (now - self._last)
                if remaining > 0:
                    self._sleep(remaining)
                    now = self._clock()
            self._last = now


class CachedFetcher:
    """HTTP GET with a file cache and a rate limit on cache misses.

    Only successful responses are cached. `max_age` (seconds) per call lets API
    answers expire; None keeps them until the cache is cleaned up. A `maxlag`
    answer from MediaWiki (HTTP 200 with error code "maxlag", or 503 with
    Retry-After) is retried a few times after the advised wait.
    """

    MAXLAG_RETRIES = 3

    def __init__(self, cache, rate_limiter, user_agent, timeout=30.0, session=None, sleep=time.sleep):
        self.cache = cache
        self.rate_limiter = rate_limiter
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self._sleep = sleep

    def get(self, url, max_age=None, store=True):
        """The response body. `store=False` skips the cache (large originals
        are kept elsewhere)."""
        cached = self.cache.get(url, max_age) if store else None
        if cached is not None:
            return cached
        for attempt in range(self.MAXLAG_RETRIES + 1):
            self.rate_limiter.wait()
            try:
                response = self.session.get(url, timeout=self.timeout)
            except requests.RequestException as exc:
                raise FetchError(url, f"Wikimedia niet bereikbaar: {exc.__class__.__name__}") from exc
            lagged = response.status_code == 503 or (
                response.status_code == 200 and b'"maxlag"' in response.content[:300]
            )
            if lagged and attempt < self.MAXLAG_RETRIES:
                self._sleep(_retry_after(response))
                continue
            if response.status_code != 200 or lagged:
                raise FetchError(url, f"HTTP {response.status_code}", status=response.status_code)
            if store:
                self.cache.set(url, response.content)
            return response.content
        raise FetchError(url, "maxlag")  # pragma: no cover (loop always returns or raises)


def _retry_after(response):
    try:
        return max(1, min(30, int(response.headers.get("Retry-After", 5))))
    except ValueError:
        return 5
