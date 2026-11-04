"""Detection service with the DummyDetector and recorded Commons files (7, 9.5)."""

import io
import json
from datetime import datetime

import pytest
from PIL import Image

from cutter.detectie.basis import DetectedObject, DetectionError, Detector
from cutter.detectie.dienst import DetectionService, iou
from cutter.detectie.dummy import DummyDetector
from cutter.verbruik import Verbruik


@pytest.fixture
def service(client, tmp_path):
    return DetectionService(DummyDetector(), client, tmp_path / "cache", tmp_path / "uitvoer", Verbruik(tmp_path / "verbruik", 500))


def test_prompt_detection_is_deterministic_and_stored(service, album, tmp_path):
    first = service.detect(album, 1, "wapen")
    again = service.detect(album, 1, "wapen")
    assert first["nieuw"] and [o["id"] for o in first["objecten"]] == [o["id"] for o in again["objecten"]]
    assert all(o["label"] == "coat of arms" and o["zoekterm"] == "wapen" for o in first["objecten"])
    assert all(o["status"] == "geselecteerd" for o in first["objecten"])
    store = json.loads((tmp_path / "uitvoer" / album["mid"] / "pagina_1" / "objecten.json").read_text(encoding="utf-8"))
    assert len(store["objecten"]) == len(first["objecten"])
    meta = json.loads((tmp_path / "uitvoer" / album["mid"] / "bestand.json").read_text(encoding="utf-8"))
    assert meta["mid"] == album["mid"] and "_wikitekst" not in meta


def test_min_excludes_overlapping(service, album):
    result = service.detect(album, 1, "wapen min wapen")
    assert all(o["status"] == "uitgesloten" for o in result["objecten"])


def test_modes(service, album):
    everything = service.detect(album, 1, modus="alles")
    assert everything["termen"]["plus"][0]["en"] == "illustration" and len(everything["termen"]["plus"]) == 8
    with pytest.raises(DetectionError):  # Snel zoeken is gone (0.21.0)
        service.detect(album, 1, modus="categorie")
    with pytest.raises(DetectionError) as exc:
        service.detect(album, 1, "")
    assert exc.value.code == "empty_prompt"


def test_estimate_changes_nothing(service, album):
    result = service.detect(album, 1, "wapen", dry_run=True)
    assert result["dry_run"] and result["aanroepen"]["termen"] == 1 and result["aanroepen"]["betaald"] == 0
    assert service.page_objects(album, 1) == []


def test_regions_from_commons_are_never_merged(service, book):
    result = service.detect(book, 1, modus="commons")
    regions = [o for o in result["objecten"] if o["bron"] == "commons"]
    assert len(regions) == 13
    assert all(o["masker"] is None for o in regions)
    catherine = next(o for o in regions if o["wikidata"] == "Q179718")
    assert catherine["label_en"] == "Catherine of Alexandria"
    # A SAM-like object exactly on a region does not swallow it.
    service._merge_into_page(book, 1, [{**catherine, "id": "obj-other", "bron": "dummy", "status": "geselecteerd"}])
    assert len(service.page_objects(book, 1)) == 14
    assert service.merge_duplicates(book, 1) == 0
    # Loading the regions again keeps what the user changed.
    service.set_statuses(book, 1, [{"id": catherine["id"], "status": "kandidaat"}])
    service.detect(book, 1, modus="commons")
    assert next(o for o in service.page_objects(book, 1) if o["id"] == catherine["id"])["status"] == "kandidaat"


def test_point_finds_known_object_or_asks_detector(service, album):
    obj = service.detect(album, 1, "portret")["objecten"][0]
    box = obj["box"]
    hit = service.point(album, 1, box["x"] + 1, box["y"] + 1)
    assert hit["object"]["id"] == obj["id"] and not hit["nieuw"]
    miss = service.point(album, 1, 1, 1) if not (box["x"] <= 1 and box["y"] <= 1) else service.point(album, 1, 1999, 1428)
    assert miss["object"]["label"] == "klik" and miss["object"]["status"] == "kandidaat"


def test_manual_rectangle_is_free_and_clamped(service, album):
    result = service.rectangle(album, 1, {"x": 1900, "y": 10, "w": 500, "h": -20 + 220})
    assert result["object"]["box"] == {"x": 1900, "y": 10, "w": 100, "h": 200}
    assert result["object"]["bron"] == "handmatig" and result["object"]["masker"] is None
    with pytest.raises(DetectionError):
        service.rectangle(album, 1, {"x": 1, "y": 1, "w": 2, "h": 2})


def test_refine_mask_of_a_region(service, book):
    region = service.detect(book, 1, modus="commons")["objecten"][0]
    result = service.refine_mask(book, 1, region["id"])
    assert result["object"]["masker"]["codering"] == "ellips"
    assert result["object"]["box_regio"] == region["box"]
    # A new "Regio's uit Commons" keeps the mask.
    service.detect(book, 1, modus="commons")
    again = next(o for o in service.page_objects(book, 1) if o["id"] == region["id"])
    assert again["masker"] and again["box_regio"] == region["box"]


def test_save_writes_full_resolution_files(service, album, tmp_path):
    objects = service.detect(album, 1, "wapen")["objecten"]
    rect = service.rectangle(album, 1, {"x": 100, "y": 100, "w": 400, "h": 300})["object"]
    result = service.save_objects(album, 1)
    assert set(result["opgeslagen"]) >= {o["id"] for o in objects} | {rect["id"]}
    folder = tmp_path / "uitvoer" / album["mid"]
    saved = {o["id"]: o for o in service.page_objects(album, 1)}
    jpg = Image.open(folder / saved[rect["id"]]["opgeslagen"]["jpg"])
    original = service.client.original_image(album, 1)
    scale = original.width / album["breedte"]
    assert jpg.size == (round(400 * scale), round(300 * scale))
    assert "png" not in saved[rect["id"]]["opgeslagen"]  # no mask: only the rectangle
    masked = saved[objects[0]["id"]]["opgeslagen"]
    assert Image.open(folder / masked["png"]).mode == "RGBA"
    assert (folder / masked["masker"]).exists()
    assert saved[rect["id"]]["opgeslagen"]["breedte"] == jpg.width  # pixels of the written file
    # The API says when the saved files go (retention, 12.1): 30 days after the last use.
    from datetime import datetime, timedelta, timezone

    expires = datetime.fromisoformat(service.public(album, 1, saved[rect["id"]])["opgeslagen"]["verloopt"])
    assert abs(expires - (datetime.now(timezone.utc) + timedelta(days=30))) < timedelta(minutes=5)


def test_save_needs_a_selection(service, album):
    with pytest.raises(DetectionError) as exc:
        service.save_objects(album, 1)
    assert exc.value.code == "nothing_selected"


def test_trash_restore_and_purge(service, album, tmp_path):
    obj = service.detect(album, 1, "wapen")["objecten"][0]
    service.save_objects(album, 1, [obj["id"]])
    service.delete_object(album, 1, obj["id"])
    assert obj["id"] not in {o["id"] for o in service.page_objects(album, 1)}
    service.detect(album, 1, "wapen")  # a cached search does not bring it back
    assert obj["id"] not in {o["id"] for o in service.page_objects(album, 1)}
    trash = service.all_objects(trash=True)
    assert [o["id"] for o in trash] == [obj["id"]] and trash[0]["mid"] == album["mid"]
    service.restore_object(album, 1, obj["id"])
    assert obj["id"] in {o["id"] for o in service.page_objects(album, 1)}
    service.delete_object(album, 1, obj["id"])
    assert service.empty_trash() == 1
    assert not list((tmp_path / "uitvoer" / album["mid"] / "pagina_1" / "jpg").glob(f"{obj['id']}*"))


def test_all_objects_filters(service, album, book):
    service.detect(album, 1, "wapen")
    service.detect(book, 1, modus="commons")
    assert {o["mid"] for o in service.all_objects()} == {album["mid"], book["mid"]}
    assert {o["bron"] for o in service.all_objects(sources=["commons"])} == {"commons"}
    assert service.all_objects(mid=album["mid"], saved=True) == []
    entry = service.all_objects(mid=book["mid"])[0]
    assert entry["app_url"].startswith(f"/?mid={book['mid']}&pagina=1&object=")


def test_cutout_preview(service, album):
    obj = service.rectangle(album, 1, {"x": 0, "y": 0, "w": 1000, "h": 500})["object"]
    preview = Image.open(io.BytesIO(service.cutout_jpeg(album, 1, obj["id"], 100)))
    assert preview.width == 100


def test_iou():
    a = {"x": 0, "y": 0, "w": 10, "h": 10}
    assert iou(a, a) == 1 and iou(a, {"x": 20, "y": 20, "w": 5, "h": 5}) == 0


class PaidDetector(Detector):
    model = "betaald"
    betaald = True

    def __init__(self):
        self.calls = 0

    def detect(self, image, prompt, native_size=None, regions=None):
        self.calls += 1
        return [DetectedObject("1", prompt, 0.9, {"x": 0, "y": 0, "w": 10, "h": 10}, herkomst={"model": self.model})]


def test_paid_calls_are_limited_cached_and_logged(client, album, tmp_path):
    detector = PaidDetector()
    usage = Verbruik(tmp_path / "verbruik", daily_limit=1)
    service = DetectionService(detector, client, tmp_path / "cache", tmp_path / "uitvoer", usage)
    service.detect(album, 1, "wapen", user="Olaf")
    service.detect(album, 1, "wapen", user="Olaf")  # from the cache: free
    assert detector.calls == 1
    entry = usage.entries()[0]
    assert entry["bestand"] == album["mid"] and entry["gebruiker"] == "Olaf" and entry["kosten_usd"] == 0.0025
    with pytest.raises(DetectionError) as exc:
        service.detect(album, 1, "portret")
    assert exc.value.status == 429 and exc.value.code == "daily_limit"


def test_usage_limits_per_user_and_budget(tmp_path):
    now = lambda: datetime(2026, 11, 3, 12, 0)  # noqa: E731
    usage = Verbruik(tmp_path, daily_limit=500, per_user_limit=2, daily_budget=0.01, now=now)
    usage.register({"term": "a"}, user="A")
    usage.register({"term": "b"}, user="A")
    with pytest.raises(DetectionError) as exc:
        usage.check(1, user="A")
    assert exc.value.code == "user_limit"
    usage.check(1, user="B")
    usage.register({"term": "c"}, cost=0.009, user="B")
    with pytest.raises(DetectionError) as exc:
        usage.check(1, user="B", cost=0.005)
    assert exc.value.code == "daily_budget"
    status = usage.status("A")
    assert status["gebruiker"]["resterend"] == 0 and status["kosten_vandaag_usd"] == pytest.approx(0.014)


def test_simultaneous_changes_do_not_overwrite_each_other(service, album):
    import threading

    ids = [service.rectangle(album, 1, {"x": 10 + 60 * i, "y": 10, "w": 50, "h": 50})["object"]["id"] for i in range(8)]
    threads = [
        threading.Thread(target=service.set_caption, args=(album, 1, oid, {"tekst": f"bijschrift {i}"}))
        for i, oid in enumerate(ids)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    stored = {o["id"]: (o.get("bijschrift") or {}).get("tekst") for o in service.page_objects(album, 1)}
    assert [stored[oid] for oid in ids] == [f"bijschrift {i}" for i in range(8)]


def test_paid_calls_under_way_count_for_the_limits(tmp_path):
    """Two requests at once cannot together pass the budget: a booking counts until it ends."""
    log = Verbruik(tmp_path / "verbruik", 2, per_user_limit=5, daily_budget=0.01)
    with log.reservation(1, user="A", cost=0.008):
        with pytest.raises(DetectionError) as exc:
            with log.reservation(1, user="B", cost=0.008):
                pass
        assert exc.value.code == "daily_budget"
    with log.reservation(1, user="B", cost=0.008):  # free again once the first ended
        pass
    assert log.cost_today() == 0.0  # bookings are not costs; register() logs the real call


def test_too_many_terms_in_one_request(service, album):
    prompt = " en ".join(f"ding{i}" for i in range(25))
    with pytest.raises(DetectionError) as exc:
        service.detect(album, 1, prompt)
    assert exc.value.code == "too_many_terms"
