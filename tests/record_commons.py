"""Record Commons responses as test fixtures (read-only requests only).

    python tests/record_commons.py

Uses the app's own fetcher (User-Agent, about one request per second, maxlag)
and stores every response under tests/fixtures/commons/, with index.json
mapping URL to file. The tests replay them with FixtureFetcher (conftest.py).
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cutter.cache import CachedFetcher, FileCache, RateLimiter  # noqa: E402
from cutter.commons import CommonsClient  # noqa: E402
from cutter.config import Config  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "commons"

ALBUM = "File:Album amicorum van Jacob van Bronckhorst van Batenburg (8077131573).jpg"
BOOK_OF_HOURS = "M83565772"
PDF = "File:Heritage Album Paperwork - Polk Co SO - COMPLETE.pdf"
# A page of a picture book with {{Book}} and |Wikidata=, without a date of its own.
PICTURE_BOOK = "M90890204"


class RecordingFetcher:
    def __init__(self, inner):
        self.inner = inner
        self.index_path = FIXTURES / "index.json"
        self.index = json.loads(self.index_path.read_text(encoding="utf-8")) if self.index_path.exists() else {}

    def get(self, url, max_age=None, store=True):
        data = self.inner.get(url)
        suffix = ".json" if "api.php" in url else Path(url.split("?")[0]).suffix.lower() or ".bin"
        name = hashlib.sha1(url.encode()).hexdigest()[:16] + suffix
        (FIXTURES / name).write_bytes(data)
        self.index[url] = name
        self.index_path.write_text(json.dumps(self.index, indent=2, ensure_ascii=False), encoding="utf-8")
        return data


def main():
    import truststore

    truststore.inject_into_ssl()
    FIXTURES.mkdir(parents=True, exist_ok=True)
    config = Config()
    fetcher = RecordingFetcher(
        CachedFetcher(FileCache(ROOT / "cache" / "record"), RateLimiter(1.0), user_agent=config.COMMONS_USER_AGENT)
    )
    client = CommonsClient(fetcher, api=config.COMMONS_API, wikidata_api=config.WIKIDATA_API)
    for ref in (ALBUM, BOOK_OF_HOURS, PDF, PICTURE_BOOK):
        file = client.load_file(ref)
        # The API looks files up by M-id, the start page by title or URL: record both.
        client.load_file({"pageid": file["pageid"]})
        client.load_file({"titel": file["titel"]})
        print(file["mid"], file["titel"], file["breedte"], file["hoogte"], file["mime"], file["paginas"], file["rechten"]["labels"])
        client.page_image(file, 1, 250)
        if file["paginas"] > 1:
            print("  page 2:", client.load_page(file, 2))
    book = client.load_file(BOOK_OF_HOURS)
    print("regions:", book["regio_aantal"], "extracted:", book["bestaande_uitsneden"])
    client.depicted_by_extracted(book)
    # Which width does Commons hand out for a non-standard request (5.2)?
    info = client._thumb_info(client.load_file(ALBUM), 1, 1000)
    print("thumb for 1000:", info.get("thumbwidth"), info.get("thumburl"))
    album = client.load_file(ALBUM)
    print("sha1 duplicates:", client.files_with_sha1(album["sha1"]))
    print(client.titles_exist(["Category:Alba amicorum", "Category:Does not exist 123456", "File:" + album["naam"]]))


if __name__ == "__main__":
    main()
