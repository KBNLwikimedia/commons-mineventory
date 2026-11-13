"""Robustness: recovery from damaged files, odd answers of Commons and the Meta Model API,
invalid requests and rare situations (wish Olaf: a more robust backend). Everything with
fixtures and fakes: no live calls, nothing written to Commons."""

import base64
import copy
import errno
import io
import json
import math
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from conftest import ALBUM, ALBUM_MID, FakeResponse, FakeSession, FixtureFetcher
from cutter import export, opslag
from cutter.beschrijving import MAX_HISTORY, MAX_OWN_PROMPT, usage_tokens
from cutter.cache import CachedFetcher, FetchError, FileCache, RateLimiter
from cutter.commons import CommonsClient, CommonsError, open_image, parse_input
from cutter.detectie.basis import DetectionError
from cutter.detectie.maskers import BadMask, decode_raster
from cutter.detectie.meta_sam import MetaSamDetector, SamRecord, extract_output_text
from cutter.opruimen import Cleanup, cached_bytes
from cutter.slot import LockTimeout
from cutter.verbruik import Verbruik

PAGE = f"/api/v1/bestand/{ALBUM_MID}/pagina/1"


def _rect(http, x=10, y=10, w=300, h=200):
    response = http.post(PAGE + "/detecties", json={"rechthoek": {"x": x, "y": y, "w": w, "h": h}})
    assert response.status_code == 201, response.get_json()
    return response.get_json()["object"]


def _store_path(app):
    return Path(app.config["UITVOER_DIR"]) / ALBUM_MID / "pagina_1" / "objecten.json"


def _service(app):
    return app.extensions["detectiedienst"]


# -- Writing and reading files (cutter/opslag.py) ---------------------------------------------


def test_write_atomic_replaces_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "a" / "b.json"  # the folder is made
    opslag.write_atomic(path, "één")
    opslag.write_atomic(path, b"twee")
    assert path.read_bytes() == b"twee"
    assert [p.name for p in path.parent.iterdir()] == ["b.json"]


def test_write_atomic_on_a_full_disk_keeps_the_old_file(tmp_path, monkeypatch):
    path = tmp_path / "store.json"
    path.write_text("oud", encoding="utf-8")

    def full(*_args):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(opslag.os, "replace", full)
    with pytest.raises(OSError):
        opslag.write_atomic(path, "nieuw")
    assert path.read_text(encoding="utf-8") == "oud"
    assert [p.name for p in tmp_path.iterdir()] == ["store.json"]  # the temporary file is gone


def test_write_atomic_retries_a_target_that_windows_keeps_locked(tmp_path, monkeypatch):
    path = tmp_path / "store.json"
    real, tries = opslag.os.replace, []

    def locked_twice(src, dst):
        tries.append(1)
        if len(tries) <= 2:
            raise PermissionError(13, "in use")
        real(src, dst)

    monkeypatch.setattr(opslag.os, "replace", locked_twice)
    monkeypatch.setattr(opslag.time, "sleep", lambda _s: None)
    opslag.write_atomic(path, "ok")
    assert path.read_text(encoding="utf-8") == "ok" and len(tries) == 3


def test_read_json_missing_corrupt_and_wrong_shape(tmp_path):
    path = tmp_path / "x.json"
    assert opslag.read_json(path, {"leeg": True}) == {"leeg": True}  # missing (or gone just now)
    path.write_text('{"half": ', encoding="utf-8")
    assert opslag.read_json(path, {}) == {}
    copies = list(tmp_path.glob("x.json.kapot-*"))
    assert len(copies) == 1 and copies[0].read_text(encoding="utf-8") == '{"half": '
    opslag.read_json(path, {})  # the same content is kept once, not on every read
    assert len(list(tmp_path.glob("x.json.kapot-*"))) == 1
    with pytest.raises(opslag.CorruptFile) as exc:
        opslag.read_json(path, corrupt="raise")
    assert exc.value.status == 500 and exc.value.code == "corrupt_file" and "kapot" in exc.value.message
    path.write_text("[1, 2]", encoding="utf-8")
    assert opslag.read_json(path, "standaard", valid=lambda d: isinstance(d, dict)) == "standaard"
    path.write_bytes(b"\xff\xfe\x00garbage")
    assert opslag.read_json(path, None) is None


def test_read_json_of_an_empty_file_makes_no_copy(tmp_path):
    path = tmp_path / "leeg.json"
    path.write_text("", encoding="utf-8")
    assert opslag.read_json(path, {}) == {}
    assert not list(tmp_path.glob("*.kapot-*"))


# -- The object store ------------------------------------------------------------------------


@pytest.mark.parametrize("damage", ['{"objecten": [', "", "null", '{"objecten": null}', '{"objecten": ["x"]}', '{"objecten": [{"box": {}}]}', "[]"])
def test_damaged_objecten_json_keeps_the_page_usable(app, http, damage):
    _rect(http)
    path = _store_path(app)
    path.write_text(damage, encoding="utf-8")
    page = http.get(PAGE)
    assert page.status_code == 200 and page.get_json()["objecten"] == []
    assert http.get("/api/v1/objecten").status_code == 200
    assert http.get(f"/api/v1/bestand/{ALBUM_MID}/werk").status_code == 200
    if damage.strip():  # what was there is kept aside, never silently lost
        copies = list(path.parent.glob("objecten.json.kapot-*"))
        assert len(copies) == 1 and copies[0].read_text(encoding="utf-8") == damage
    obj = _rect(http, 400, 400, 100, 100)  # and the page works again
    assert [o["id"] for o in http.get(PAGE).get_json()["objecten"]] == [obj["id"]]


def test_store_file_gone_between_check_and_read(app, http, monkeypatch):
    _rect(http)
    service = _service(app)
    real = Path.read_bytes

    def vanished(self):
        if self.name == "objecten.json":
            raise FileNotFoundError(self)
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", vanished)
    assert service.page_objects({"mid": ALBUM_MID}, 1) == []


def test_missing_mask_file_falls_back_to_the_box(app, http):
    a, b = _rect(http, 10, 10, 100, 100), _rect(http, 300, 300, 100, 100)
    group = http.post(PAGE + "/groepen", json={"objecten": [a["id"], b["id"]]}).get_json()["object"]
    mask_file = _store_path(app).parent / "sam" / f"{group['id']}.json"
    assert mask_file.exists()
    mask_file.unlink()  # gone (removed by hand, a failed copy)
    assert http.get(PAGE + f"/objecten/{group['id']}/masker.png").status_code == 200
    saved = http.post(PAGE + "/uitsneden", json={"ids": [group["id"]]})
    assert saved.status_code == 201 and saved.get_json()["opgeslagen"] == [group["id"]]


def test_damaged_mask_is_a_clear_error_not_a_crash(app, http):
    a, b = _rect(http, 10, 10, 100, 100), _rect(http, 300, 300, 100, 100)
    group = http.post(PAGE + "/groepen", json={"objecten": [a["id"], b["id"]]}).get_json()["object"]
    mask_file = _store_path(app).parent / "sam" / f"{group['id']}.json"
    mask_file.write_text(json.dumps({"encoding": "lossless", "payload": "!!", "width": 10, "height": 10}), encoding="utf-8")
    response = http.get(PAGE + f"/objecten/{group['id']}/masker.png")
    assert response.status_code == 422 and response.get_json()["code"] == "bad_mask"


def test_decode_raster_rejects_masks_of_the_wrong_size():
    png = io.BytesIO()
    Image.new("L", (4, 4), 255).save(png, "PNG")
    good = {"encoding": "png", "payload": base64.b64encode(png.getvalue()).decode(), "width": 4, "height": 4}
    assert decode_raster(good).shape == (4, 4)
    for bad in ({**good, "payload": "nonsense"}, {**good, "width": 0}, {**good, "width": 10**6, "height": 10**6}, {"encoding": "ellips"}):
        with pytest.raises(BadMask) as exc:
            decode_raster(bad)
        assert isinstance(exc.value, ValueError) and exc.value.code == "bad_mask"


def test_id_on_the_page_and_in_the_trash_purge_only_the_trash_copy(app, http):
    obj = _rect(http)
    http.post(PAGE + "/uitsneden", json={"ids": [obj["id"]]})
    path = _store_path(app)
    store = json.loads(path.read_text(encoding="utf-8"))
    store["prullenbak"].append(copy.deepcopy(store["objecten"][0]))  # the same id twice (edited by hand)
    path.write_text(json.dumps(store), encoding="utf-8")
    jpg = path.parent / "jpg" / f"{obj['id']}.jpg"
    assert jpg.exists()
    assert http.patch(PAGE + f"/objecten/{obj['id']}", json={"prullenbak": False}).get_json()["code"] in ("already_on_page", "bad_request")
    response = http.delete(f"/api/v1/prullenbak/{ALBUM_MID}/1/{obj['id']}")
    assert response.status_code == 200
    page = http.get(PAGE).get_json()["objecten"]
    assert [o["id"] for o in page] == [obj["id"]] and page[0].get("opgeslagen")
    assert jpg.exists()  # the page copy keeps its cut-out


def test_restore_when_the_same_id_is_back_on_the_page(app, http):
    obj = _rect(http)
    service = _service(app)
    path = _store_path(app)
    store = json.loads(path.read_text(encoding="utf-8"))
    store["prullenbak"].append(copy.deepcopy(store["objecten"][0]))
    store["prullenbak"][0]["box"] = {"x": 900, "y": 900, "w": 50, "h": 50}  # not the same picture
    path.write_text(json.dumps(store), encoding="utf-8")
    with pytest.raises(DetectionError) as exc:
        service.restore_object({"mid": ALBUM_MID}, 1, obj["id"])
    assert exc.value.status == 409 and exc.value.code == "already_on_page"


def test_group_member_cannot_be_purged_on_its_own_and_ungrouping_still_works(app, http):
    a, b = _rect(http, 10, 10, 100, 100), _rect(http, 300, 300, 100, 100)
    group = http.post(PAGE + "/groepen", json={"objecten": [a["id"], b["id"]]}).get_json()["object"]
    with pytest.raises(DetectionError) as exc:
        _service(app).purge_object({"mid": ALBUM_MID}, 1, a["id"])
    assert exc.value.status == 404
    response = http.delete(PAGE + f"/groepen/{group['id']}")
    assert response.status_code == 200
    assert {o["id"] for o in http.get(PAGE).get_json()["objecten"]} == {a["id"], b["id"]}


def test_group_whose_member_lost_its_mask_file(app, http):
    a, b = _rect(http, 10, 10, 100, 100), _rect(http, 300, 300, 100, 100)
    inner = http.post(PAGE + "/groepen", json={"objecten": [a["id"], b["id"]]}).get_json()["object"]
    c = _rect(http, 600, 600, 100, 100)
    (_store_path(app).parent / "sam" / f"{inner['id']}.json").unlink()
    service = _service(app)
    store = json.loads(_store_path(app).read_text(encoding="utf-8"))
    store["objecten"][0]["bron"] = "dummy"  # a group inside a group (only by hand)
    _store_path(app).write_text(json.dumps(store), encoding="utf-8")
    outer = service.group({"mid": ALBUM_MID}, 1, ids=[inner["id"], c["id"]])
    assert outer["object"]["groep"]["aantal"] == 2


def test_concurrent_edits_on_one_store_both_survive(app, http):
    ids = [_rect(http, 10 + 120 * i, 10, 100, 100)["id"] for i in range(6)]
    service, file = _service(app), {"mid": ALBUM_MID}
    errors = []

    def caption(object_id):
        try:
            service.set_caption(file, 1, object_id, {"tekst": f"tekst {object_id}"})
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=caption, args=(i,)) for i in ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert not errors
    stored = {o["id"]: o["bijschrift"]["tekst"] for o in json.loads(_store_path(app).read_text(encoding="utf-8"))["objecten"]}
    assert stored == {i: f"tekst {i}" for i in ids}
    assert not list(_store_path(app).parent.glob("*.tmp"))


def test_unknown_pages_and_objects(http):
    assert http.get(f"/api/v1/bestand/{ALBUM_MID}/pagina/99").status_code == 404
    assert http.get(f"/api/v1/bestand/{ALBUM_MID}/pagina/0").status_code == 404
    assert http.delete(f"/api/v1/prullenbak/{ALBUM_MID}/1/obj-onbekend").status_code == 404
    assert http.delete("/api/v1/prullenbak/..%2F..%2Fx/1/obj-a").status_code in (400, 404)


def test_empty_page_with_a_stale_inventory_and_duplicate_terms(app, http):
    path = _store_path(app)
    path.parent.mkdir(parents=True)
    terms = [{"en": "rose", "nl": "roos"}, {"en": "rose", "nl": "roos"}, {"en": "ROSE", "nl": None}, {"en": "", "nl": "x"}]
    path.write_text(json.dumps({"objecten": [], "prullenbak": [], "inventaris": {"zoektermen": terms}}), encoding="utf-8")
    assert http.get(PAGE).status_code == 200
    assert http.get(PAGE + "/origineel").status_code == 200
    assert http.get(PAGE + "/inventaris").status_code == 200


def test_description_history_of_a_thousand_entries_is_capped(app, http):
    obj = _rect(http)
    path = _store_path(app)
    store = json.loads(path.read_text(encoding="utf-8"))
    store["objecten"][0]["beschrijving"] = {"beschrijving": "oud", "tijdstempel": "2026-01-01T00:00:00+00:00"}
    store["objecten"][0]["beschrijving_geschiedenis"] = [{"beschrijving": f"v{i}", "tijdstempel": f"2025-{i:04d}"} for i in range(1000)]
    path.write_text(json.dumps(store), encoding="utf-8")
    assert http.get(PAGE + f"/objecten/{obj['id']}/beschrijving/geschiedenis").status_code == 200
    response = http.post(PAGE + f"/objecten/{obj['id']}/beschrijving", json={"aanwijzing": "nieuw"})
    assert response.status_code < 300
    stored = json.loads(path.read_text(encoding="utf-8"))["objecten"][0]
    assert len(stored["beschrijving_geschiedenis"]) == MAX_HISTORY


def test_own_prompt_of_exactly_the_maximum_length(app, http):
    obj = _rect(http)
    for length, kept in ((MAX_OWN_PROMPT, MAX_OWN_PROMPT), (MAX_OWN_PROMPT + 1, MAX_OWN_PROMPT)):
        text = "a" * (length - 1) + "😀"
        assert http.put(PAGE + f"/objecten/{obj['id']}/beschrijving/prompt", json={"prompt": text}).status_code < 300
        own = json.loads(_store_path(app).read_text(encoding="utf-8"))["objecten"][0]["prompt_eigen"]["tekst"]
        assert len(own) == kept


def test_corrupt_description_cache_is_asked_anew_and_kept_aside(app, http):
    obj = _rect(http)
    url = PAGE + f"/objecten/{obj['id']}/beschrijving"
    assert http.post(url, json={}).status_code < 300
    cache_dir = app.extensions["beschrijvingsdienst"].cache_dir
    cached = [p for p in Path(cache_dir).rglob("*.json")]
    assert cached
    for path in cached:
        path.write_text("{kapot", encoding="utf-8")
    response = http.post(url, json={})
    assert response.status_code < 300 and response.get_json()["uit_cache"] is False
    assert list(Path(cache_dir).rglob("*.kapot-*"))


def test_corrupt_detection_cache_and_cache_file_gone(app, http):
    first = http.post(PAGE + "/detecties", json={"prompt": "portret"})
    assert first.status_code == 201
    cache = Path(app.config["CACHE_DIR"]) / "detectie"
    files = list(cache.rglob("*.json"))
    assert files
    files[0].write_text("[{", encoding="utf-8")
    for path in files[1:]:
        path.unlink()  # removed by the cleanup between plan and search
    again = http.post(PAGE + "/detecties", json={"prompt": "portret"})
    assert again.status_code == 201
    assert {o["id"] for o in again.get_json()["objecten"]} == {o["id"] for o in first.get_json()["objecten"]}


def test_corrupt_draft_and_file_metadata(app, http):
    _rect(http)
    folder = _store_path(app).parent
    (folder / "origineel.json").write_text('{"beeldt_af": "geen lijst"}', encoding="utf-8")
    response = http.get(PAGE + "/origineel")
    assert response.status_code == 200 and response.get_json()["concept"] is None
    (folder.parent / "bestand.json").write_text("{", encoding="utf-8")
    listing = http.get("/api/v1/objecten")
    assert listing.status_code == 200 and listing.get_json()["objecten"] == []  # the file is skipped
    assert http.get(f"/api/v1/bestand/{ALBUM_MID}/export?formaat=json").status_code in (200, 404)


def test_file_renamed_on_commons_between_calls_keeps_its_objects(app, http, client):
    obj = _rect(http)
    real = client.file_query

    def renamed(ref):
        data = copy.deepcopy(real(ref))
        page = data["query"]["pages"][0]
        page["title"] = "File:Nieuwe naam.jpg"
        data["query"]["redirects"] = [{"from": "File:Nieuwe naam.jpg", "to": "File:Nieuwe naam.jpg"}]  # to itself
        return data

    client.file_query = renamed
    file = http.get(f"/api/v1/bestand/{ALBUM_MID}").get_json()
    assert file["titel"] == "File:Nieuwe naam.jpg" and file["mid"] == ALBUM_MID
    assert [o["id"] for o in http.get(PAGE).get_json()["objecten"]] == [obj["id"]]


# -- Commons ---------------------------------------------------------------------------------


class _Session:
    def __init__(self, responses):
        self.responses, self.headers, self.calls = list(responses), {}, 0

    def get(self, url, timeout):
        self.calls += 1
        return self.responses.pop(0)

    post = None


class _Response:
    def __init__(self, status, content, headers=None):
        self.status_code, self.content, self.headers = status, content, headers or {}


def test_html_instead_of_json_is_a_fetch_error_and_not_cached(tmp_path):
    session = _Session([_Response(200, b"<html>Wikimedia error</html>"), _Response(200, b'{"query": {"pages": []}}')])
    fetcher = CachedFetcher(FileCache(tmp_path), RateLimiter(0), "test", session=session, sleep=lambda _s: None)
    client = CommonsClient(fetcher)
    with pytest.raises(FetchError):
        client._json({"titles": "File:X.jpg"})
    assert client._json({"titles": "File:X.jpg"}) == {"query": {"pages": []}}  # asked again, not the cached page
    assert session.calls == 2


def test_commons_429_is_retried_like_maxlag(tmp_path):
    session = _Session([_Response(429, b"", {"Retry-After": "1"}), _Response(200, b'{"ok": 1}')])
    fetcher = CachedFetcher(FileCache(tmp_path), RateLimiter(0), "test", session=session, sleep=lambda _s: None)
    assert fetcher.get("https://commons.wikimedia.org/w/api.php?x=1") == b'{"ok": 1}'


def test_odd_file_answers_from_commons(client, monkeypatch):
    real = client.file_query
    for change in (
        lambda page: page.update(imageinfo=[]),  # no imageinfo at all
        lambda page: page["imageinfo"][0].update(filemissing=True),  # the file itself is gone
        lambda page: page.update(missing=True),  # deleted
    ):
        def odd(ref, change=change):
            data = copy.deepcopy(real(ref))
            change(data["query"]["pages"][0])
            return data

        monkeypatch.setattr(client, "file_query", odd)
        with pytest.raises(CommonsError) as exc:
            client.load_file(ALBUM)
        assert exc.value.status == 404
    monkeypatch.setattr(client, "file_query", lambda ref: {"error": "geen object"})
    monkeypatch.setattr(client.fetcher, "get", lambda url, **kw: b'{"error": "tekst"}')
    with pytest.raises(CommonsError) as exc:
        client._json({"titles": "File:X.jpg"})
    assert exc.value.code == "commons_error"


def test_html_from_commons_through_the_api(app, client):
    fetcher = FixtureFetcher()
    broken = CommonsClient(fetcher)
    url = broken.api_url({"titles": "File:Y.jpg"})
    fetcher.extra[url] = b"<!DOCTYPE html><html>502 Bad Gateway</html>"
    with pytest.raises(FetchError):
        broken._json({"titles": "File:Y.jpg"})


def test_entity_with_empty_labels_as_a_list():
    from cutter.sdc import parse_entity

    for entity in ({"id": "M1", "labels": [], "statements": []}, None, "x", {"id": "M1", "labels": {"nl": "kapot"}}):
        assert parse_entity(entity)["captions"] == {}


def test_very_long_ids_are_a_400(http):
    for mid in ("M" + "9" * 5000, "M" + "1" * 13):
        response = http.get(f"/api/v1/bestand/{mid}")
        assert response.status_code == 400 and response.get_json()["code"] == "bad_mid"
    response = http.get("/api/v1/bestand", query_string={"mid": "M" + "9" * 5000})
    assert response.status_code == 400 and response.get_json()["code"] == "bad_mid"
    with pytest.raises(CommonsError):
        parse_input("https://commons.wikimedia.org/w/index.php?curid=" + "9" * 5000)


# -- Images ----------------------------------------------------------------------------------


def _image_bytes(mode, fmt, size=(64, 48), **options):
    buffer = io.BytesIO()
    image = Image.new(mode, size)
    image.save(buffer, fmt, **options)
    return buffer.getvalue()


@pytest.mark.parametrize("mode,fmt", [("RGB", "JPEG"), ("CMYK", "JPEG"), ("L", "PNG"), ("P", "PNG"), ("I;16", "PNG"), ("LA", "PNG"), ("RGBA", "WEBP"), ("1", "TIFF"), ("RGB", "TIFF"), ("P", "GIF")])
def test_crops_from_any_image_mode(mode, fmt):
    image = open_image(_image_bytes(mode, fmt))
    box = {"x": 5, "y": 5, "w": 20, "h": 10}
    assert export.crop_jpeg(image, box, 1.0)[:2] == b"\xff\xd8"
    png, mask = export.cutout(image, box, 1.0, np.ones((3, 3), dtype=np.uint8))
    assert png.startswith(b"\x89PNG") and mask.startswith(b"\x89PNG")


def test_animated_gif_uses_its_first_frame():
    frames = [Image.new("P", (32, 32), i) for i in range(3)]
    buffer = io.BytesIO()
    frames[0].save(buffer, "GIF", save_all=True, append_images=frames[1:])
    image = open_image(buffer.getvalue())
    assert export.crop_jpeg(image, {"x": 0, "y": 0, "w": 10, "h": 10}, 1.0)


def test_zero_size_boxes_and_boxes_outside_the_image():
    image = open_image(_image_bytes("RGB", "PNG", (40, 30)))
    for box in ({"x": 5, "y": 5, "w": 0, "h": 0}, {"x": 500, "y": 500, "w": 10, "h": 10}, {"x": -20, "y": -20, "w": 10, "h": 10}):
        assert Image.open(io.BytesIO(export.crop_jpeg(image, box, 1.0))).size[0] >= 1


def test_broken_truncated_and_huge_images(monkeypatch):
    for data in (b"<html>not an image</html>", _image_bytes("RGB", "JPEG", (200, 200))[:300], b""):
        with pytest.raises(CommonsError) as exc:
            open_image(data)
        assert exc.value.code == "bad_image" and exc.value.status == 502
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)
    with pytest.raises(CommonsError) as exc:
        open_image(_image_bytes("RGB", "PNG", (100, 100)))
    assert exc.value.status == 413 and exc.value.code == "too_large"


def test_broken_page_image_through_the_api(app, http, monkeypatch):
    obj = _rect(http)
    monkeypatch.setattr(app.extensions["commons"], "page_image", lambda *a, **k: b"<html>oops</html>")
    response = http.get(PAGE + f"/objecten/{obj['id']}/uitsnede.jpg?w=120")
    assert response.status_code == 502 and response.get_json()["code"] == "bad_image"


# -- Meta Model API --------------------------------------------------------------------------


@pytest.mark.parametrize("body", [ValueError("not json"), ["a", "list"], "tekst"])
def test_meta_answer_that_is_no_json_object(body):
    detector = MetaSamDetector("sleutel", session=FakeSession(FakeResponse(200, body)))
    with pytest.raises(DetectionError) as exc:
        detector.detect(Image.new("RGB", (20, 20)), "cat")
    assert exc.value.status == 502 and exc.value.code == "unreadable_answer" and exc.value.retry


def test_meta_odd_output_shapes():
    assert extract_output_text({"output": [None, "x", {"content": [None, {"type": "output_text", "text": None}, {"type": "output_text", "text": "ok"}]}]}) == "ok"
    detector = MetaSamDetector("sleutel", session=FakeSession(FakeResponse(200, {"output_text": ""})))
    assert detector.detect(Image.new("RGB", (20, 20)), "cat") == []  # empty output: nothing found


def test_meta_nan_scores_and_inverted_or_infinite_boxes():
    detector = MetaSamDetector("sleutel", session=FakeSession(FakeResponse(200, {})))
    records = [
        SamRecord("1", left=30, top=40, right=10, bottom=20, confidence=float("nan")),
        SamRecord("2", left=float("inf"), top=0, right=5, bottom=5, confidence=0.9),
        SamRecord("3", left=0, top=0, right=5, bottom=5, confidence=0.7),
    ]
    objects = detector.to_objects(records, 2.0, "cat", "cat", (100, 100))
    assert [o.id for o in objects] == ["sam-1", "sam-3"]
    assert objects[0].score is None and objects[0].box == {"x": 20, "y": 40, "w": 40, "h": 40}
    json.dumps([o.to_dict() for o in objects], allow_nan=False)  # valid JSON for the browser


def test_odd_token_counts_are_estimated_not_a_crash():
    assert usage_tokens({"usage": {"input_tokens": "veel", "output_tokens": float("nan")}}) == (None, None, None)
    assert usage_tokens({"usage": "geen"}) == (None, None, None)
    assert usage_tokens({"usage": {"input_tokens": 10, "output_tokens": 5, "output_tokens_details": {"reasoning_tokens": -1}}}) == (10, 5, None)


# -- Usage and limits ------------------------------------------------------------------------


def test_usage_log_with_damaged_lines(tmp_path):
    usage = Verbruik(tmp_path, daily_limit=10, now=lambda: datetime(2026, 11, 13, 12))
    log = tmp_path / "logboek.jsonl"
    lines = [
        '{"tijd": "2026-11-13T10:00:00", "afbeeldingen": 1, "kosten_usd": 0.5}',
        "42", "null", '{"geen_tijd": 1}', '{"tijd": "2026-11-13T10:00:00", "kosten_usd": NaN}',
        '{"tijd": "2026-11-13T10:00:00", "afbeeldingen": "veel"}',
    ]
    log.write_bytes(("\n".join(lines) + '\n{"tijd": "2026-11-13T11:0').encode() + b"\xff")  # cut off by a crash
    assert usage.used_today() == 1 and usage.cost_today() == 0.5
    assert usage.status()["gebruikt_vandaag"] == 1
    usage.register({"bestand": "M1", "titel": "x", "pagina": 1, "term": "cat", "model": "sam"})
    assert usage.used_today() == 2  # the new call is not glued to the cut-off line


def test_usage_with_an_odd_clock(tmp_path):
    far_east = timezone(timedelta(hours=14))
    usage = Verbruik(tmp_path, daily_limit=10, now=lambda: datetime(2026, 12, 31, 23, 59, 59, tzinfo=far_east))
    usage.register({"term": "x"})
    assert usage.used_today() == 1 and usage.status()["reset"].startswith("2027-01-01T00:00")


def test_parallel_paid_calls_cannot_pass_the_daily_limit_together(app):
    service = _service(app)
    service.verbruik.daily_limit = 1
    service.detector.betaald = True  # a paid detector (the call itself is a fake)
    started, release, results = threading.Event(), threading.Event(), []
    file = {"mid": ALBUM_MID, "titel": "x"}

    def slow():
        started.set()
        release.wait(5)
        return []

    def first():
        results.append(service._detect_paid(file, 1, "a", None, slow))

    thread = threading.Thread(target=first)
    thread.start()
    started.wait(5)
    try:
        with pytest.raises(DetectionError) as exc:
            service._detect_paid(file, 1, "b", None, lambda: [])
        assert exc.value.status == 429
    finally:
        release.set()
        thread.join(5)
        service.detector.betaald = False
    assert results == [[]] and service.verbruik.used_today() == 1


# -- Caches and cleanup ----------------------------------------------------------------------


def test_file_cache_entry_gone_between_stat_and_read(tmp_path, monkeypatch):
    cache = FileCache(tmp_path)
    cache.set("k", b"data")
    real = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda self: (_ for _ in ()).throw(FileNotFoundError(self)) if self.suffix == "" and self.parent.parent == tmp_path else real(self))
    assert cache.get("k") is None


def test_cache_that_cannot_be_written_does_not_fail(tmp_path, monkeypatch):
    def full(*_a):
        raise OSError(errno.ENOSPC, "full")

    monkeypatch.setattr("cutter.cache.write_atomic", full)
    FileCache(tmp_path).set("k", b"x")  # logged, not raised
    monkeypatch.setattr("cutter.opruimen.write_atomic", full)
    assert cached_bytes(tmp_path / "p.jpg", lambda: b"made") == b"made"


def test_cached_bytes_made_again_when_removed_meanwhile(tmp_path):
    path = tmp_path / "a" / "p.jpg"
    assert cached_bytes(path, lambda: b"one") == b"one"
    path.unlink()
    assert cached_bytes(path, lambda: b"two") == b"two"


def test_cleanup_skips_a_damaged_store_and_locked_files(app, http, tmp_path, monkeypatch):
    obj = _rect(http)
    http.post(PAGE + "/uitsneden", json={"ids": [obj["id"]]})
    store = _store_path(app)
    store.write_text("{kapot", encoding="utf-8")
    jpg = store.parent / "jpg" / f"{obj['id']}.jpg"
    later = datetime.now().timestamp() + 40 * 86400  # past the cut-out period, not the page period
    cleanup = Cleanup(app.config["CACHE_DIR"], app.config["UITVOER_DIR"], now=later)
    cleanup.run(apply=True)
    assert jpg.exists() and store.read_text(encoding="utf-8") == "{kapot"  # unknown references: nothing removed

    real_unlink = Path.unlink

    def locked(self, *a, **k):
        raise PermissionError(13, "in use")

    monkeypatch.setattr(Path, "unlink", locked)
    other = tmp_path / "c"
    (other / "originelen" / "ab").mkdir(parents=True)
    (other / "originelen" / "ab" / "abc").write_bytes(b"x")
    report = Cleanup(other, tmp_path / "u", now=later).run(apply=True)  # goes on, counts nothing for it
    assert report["originelen"]["bestanden"] == 0
    monkeypatch.setattr(Path, "unlink", real_unlink)


# -- The API: errors in one shape ------------------------------------------------------------


def test_stuck_store_lock_is_a_503(app, http, monkeypatch):
    def stuck():
        raise LockTimeout("uitvoer/.slot is al 120 s bezet.")

    monkeypatch.setattr(_service(app).lock, "_lock_file", stuck)
    response = http.post(PAGE + "/detecties", json={"rechthoek": {"x": 0, "y": 0, "w": 50, "h": 50}})
    assert response.status_code == 503 and response.get_json()["code"] == "store_busy"


def test_leftover_lock_file_does_not_block(app, http):
    Path(app.config["UITVOER_DIR"]).mkdir(parents=True, exist_ok=True)
    (Path(app.config["UITVOER_DIR"]) / ".slot").write_bytes(b"left by a process that died")
    assert _rect(http)


def test_full_disk_is_a_507_and_keeps_the_store(app, http, monkeypatch):
    _rect(http)
    before = _store_path(app).read_text(encoding="utf-8")

    def full(*_a):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr("cutter.detectie.dienst.write_atomic", full)
    response = http.post(PAGE + "/detecties", json={"rechthoek": {"x": 400, "y": 400, "w": 50, "h": 50}})
    assert response.status_code == 507 and response.get_json()["code"] == "disk_full"
    assert _store_path(app).read_text(encoding="utf-8") == before


def test_unexpected_error_is_json_not_a_trace(app, http, monkeypatch):
    def boom(*_a, **_k):
        raise KeyError("onverwacht")

    monkeypatch.setattr(_service(app), "page_objects", boom)
    response = http.get(PAGE)
    assert response.status_code == 500
    assert response.get_json() == {"fout": response.get_json()["fout"], "code": "internal_error"}
    assert "Traceback" not in response.get_data(as_text=True)


def test_budget_failure_does_not_break_an_error_answer(app, http, monkeypatch):
    monkeypatch.setattr(_service(app).verbruik, "status", lambda *_a: 1 / 0)
    response = http.get(PAGE + "/objecten/bestaat-niet")
    assert response.status_code == 404 and response.get_json()["budget"] is None


@pytest.mark.parametrize("body", [
    {"prompt": 1}, {"prompt": ["kat"]}, {"prompt": {"a": 1}}, {"prompt": True},
    {"rechthoek": {"x": 1e308, "y": 1, "w": 1e308, "h": 1e308}},
    {"rechthoek": {"x": "nan", "y": 1, "w": 5, "h": 5}},
    {"punt": {"x": float("inf"), "y": 1}},
])
def test_invalid_detection_bodies_are_a_400(http, body):
    response = http.post(PAGE + "/detecties", data=json.dumps(body), content_type="application/json")
    assert response.status_code == 400 and response.get_json()["code"]


@pytest.mark.parametrize("key", ["beschrijvingsniveau", "detailniveau", "model", "redeneren"])
def test_levels_that_are_no_text_are_a_400(http, key):
    for url in (PAGE + "/inventaris", PAGE + "/inventaris/zoektermen"):
        response = http.post(url, json={key: ["normaal"]})
        assert response.status_code == 400 and response.get_json()["code"] == "invalid_body"
    response = http.patch(PAGE + "/inventaris", json={"beschrijvingsniveau": {}})
    assert response.status_code == 400


def test_odd_texts_and_ids(app, http):
    obj = _rect(http)
    caption = "‮RTL​ zero‍width 😀 مرحبا"
    response = http.patch(PAGE + f"/objecten/{obj['id']}", json={"bijschrift": {"tekst": caption}})
    assert response.status_code == 200 and "😀" in response.get_json()["bijschrift"]["tekst"]
    for odd in ("..%2F..%2Fbestand.json", "x" * 5000, "%00", "obj-​"):
        response = http.get(PAGE + f"/objecten/{odd}")
        assert response.status_code == 404 and response.get_json()["code"]
    outside = Path(app.config["UITVOER_DIR"]).parent / "buiten.txt"
    assert not outside.exists()


def test_request_body_too_large_is_a_json_413(app, http):
    app.config["MAX_CONTENT_LENGTH"] = 1000
    response = http.post(PAGE + "/detecties", data=json.dumps({"prompt": "x" * 5000}), content_type="application/json")
    assert response.status_code == 413 and response.get_json()["code"] == "too_large"


def test_nan_never_reaches_the_browser(app, http):
    obj = _rect(http)
    path = _store_path(app)
    store = json.loads(path.read_text(encoding="utf-8"))
    store["objecten"][0]["score"] = None
    path.write_text(json.dumps(store), encoding="utf-8")
    text = http.get(PAGE).get_data(as_text=True)
    assert "NaN" not in text and math.isfinite(len(text))
    assert obj["id"] in text


def test_depicts_labels_fall_back_to_a_readable_name():
    """An item without a Dutch or English label (wish Olaf 13-11-2026): the multilingual label, then
    another language with its code, and only then the Q-id; the English word for SAM is English or
    the multilingual label, else None (the app then asks for a word)."""
    from cutter import sdc
    parsed = {"beeldt_af": [
        {"waarde": "Q1", "soort": "item", "kwalificatoren": {}},
        {"waarde": "Q2", "soort": "item", "kwalificatoren": {}},
        {"waarde": "Q3", "soort": "item", "kwalificatoren": {}},
        {"waarde": "Q4", "soort": "item", "kwalificatoren": {}},
        {"waarde": "Q5", "soort": "item", "kwalificatoren": {}},
    ]}
    labels = {
        "Q1": {"nl": "vliegtuig", "en": "airplane", "mul": None, "andere": None},
        "Q2": {"nl": "matrozenkraag", "en": None, "mul": None, "andere": None},
        "Q3": {"nl": None, "en": None, "mul": "Anna Pavlova", "andere": None},
        "Q4": {"nl": None, "en": None, "mul": None, "andere": {"taal": "de", "waarde": "Flugzeug"}},
    }
    rows = {row["waarde"]: row for row in sdc.summary(parsed, labels)["beeldt_af"]}
    assert (rows["Q1"]["label"], rows["Q1"]["label_en"], rows["Q1"]["label_taal"]) == ("vliegtuig", "airplane", None)
    assert (rows["Q2"]["label"], rows["Q2"]["label_en"]) == ("matrozenkraag", None)
    assert (rows["Q3"]["label"], rows["Q3"]["label_en"], rows["Q3"]["label_taal"]) == ("Anna Pavlova", "Anna Pavlova", None)
    assert (rows["Q4"]["label"], rows["Q4"]["label_en"], rows["Q4"]["label_taal"]) == ("Flugzeug", None, "de")
    assert (rows["Q5"]["label"], rows["Q5"]["label_en"]) == ("Q5", None)



def test_page_lists_the_damaged_copies_kept_aside(app, http):
    """A damaged objecten.json (wish Olaf 13-11-2026): the page says which copies were kept, so
    the app can warn once; a page without damage has an empty list."""
    _rect(http)
    assert http.get(PAGE).get_json()["beschadigd"] == []
    path = _store_path(app)
    path.write_text('{"objecten": [', encoding="utf-8")
    copies = http.get(PAGE).get_json()["beschadigd"]
    assert len(copies) == 1 and copies[0]["bestand"].startswith("objecten.json.kapot-") and copies[0]["gewijzigd"]
    _rect(http, 400, 400, 100, 100)  # the page works again; the copy stays listed until someone removes it
    assert len(http.get(PAGE).get_json()["beschadigd"]) == 1
