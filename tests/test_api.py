"""REST API (functional design 11) and pages, with recorded Commons responses."""

import io
import json
import re
import zipfile

import pytest
from conftest import ALBUM, ALBUM_MID, BOOK_OF_HOURS_MID

from cutter.openapi import openapi_spec

PAGE = f"/api/v1/bestand/{ALBUM_MID}/pagina/1"
BOOK = f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/pagina/1"


def test_find_file_by_url_title_and_mid(http):
    by_title = http.get("/api/v1/bestand", query_string={"titel": ALBUM}).get_json()
    by_url = http.get("/api/v1/bestand", query_string={"url": "https://commons.wikimedia.org/wiki/" + ALBUM.replace(" ", "_")}).get_json()
    by_mid = http.get(f"/api/v1/bestand/{ALBUM_MID}").get_json()
    assert by_title["mid"] == by_url["mid"] == by_mid["mid"] == ALBUM_MID
    assert by_mid["pagina_lijst"] == [{"n": 1, "afbeelding_url": f"/api/v1/bestand/{ALBUM_MID}/pagina/1/afbeelding?w=120"}]
    assert not any(key.startswith("_") for key in by_mid)


def test_errors_are_json_with_a_code(http):
    response = http.get("/api/v1/bestand")
    assert response.status_code == 400 and response.get_json()["code"] == "empty_input"
    response = http.get("/api/v1/bestand/X12")
    assert response.status_code == 400 and response.get_json()["code"] == "bad_mid"
    response = http.get("/api/v1/bestaat-niet")
    assert response.status_code == 404 and response.get_json()["code"] == "not_found"
    response = http.get("/api/v1/bestand", query_string={"url": "https://example.org/wiki/File:A.jpg"})
    assert response.status_code == 422 and response.get_json()["code"] == "not_commons"
    response = http.delete("/api/v1/status")
    assert response.status_code == 405 and response.get_json()["code"] == "method_not_allowed"


def test_commons_unreachable_gives_502(http):
    response = http.get("/api/v1/bestand", query_string={"titel": "File:Not recorded.jpg"})
    assert response.status_code == 502 and response.get_json()["code"] == "commons_unreachable"


def test_api_is_not_indexed(http):
    assert http.get("/api/v1/status").headers["X-Robots-Tag"] == "noindex, nofollow"


def test_page_and_image(http):
    page = http.get(PAGE).get_json()
    assert (page["breedte"], page["hoogte"], page["objecten"]) == (2000, 1429, [])
    image = http.get(PAGE + "/afbeelding?w=200")
    assert image.status_code == 200 and image.mimetype == "image/jpeg"
    assert http.get(PAGE + "/afbeelding?w=x").status_code == 400
    assert http.get(f"/api/v1/bestand/{ALBUM_MID}/pagina/2").status_code == 404


def test_get_never_detects(http):
    estimate = http.get(PAGE + "/detecties/raming", query_string={"prompt": "wapen"}).get_json()
    assert estimate["dry_run"] and estimate["aanroepen"]["termen"] == 1
    assert http.get(PAGE).get_json()["objecten"] == []
    assert http.get(PAGE + "/detecties").status_code == 405


def test_detect_select_save_and_export(http):
    created = http.post(PAGE + "/detecties", json={"prompt": "wapen en portret"})
    assert created.status_code == 201
    objects = created.get_json()["objecten"]
    ids = [o["id"] for o in objects]
    assert ids and all(o["masker_url"].endswith("/masker.png") for o in objects)

    chosen = http.patch(PAGE + "/objecten", json={"geselecteerd": ids[:1]}).get_json()["objecten"]
    assert [o["id"] for o in chosen if o["status"] == "geselecteerd"] == ids[:1]
    assert http.patch(PAGE + "/objecten", json={}).status_code == 400

    saved = http.post(PAGE + "/uitsneden", json={})
    assert saved.status_code == 201 and saved.get_json()["opgeslagen"] == ids[:1]
    listed = http.get(PAGE + "/uitsneden").get_json()
    assert listed["aantal"] == 1

    jpg = http.get(f"{PAGE}/object/{ids[0]}/uitsnede.jpg")
    png = http.get(f"{PAGE}/object/{ids[0]}/uitsnede.png")
    assert jpg.mimetype == "image/jpeg" and png.mimetype == "image/png"
    assert http.get(f"{PAGE}/object/{ids[0]}/uitsnede.jpg?w=100").status_code == 200
    assert http.get(f"{PAGE}/object/{ids[0]}/masker.png").mimetype == "image/png"

    archive = zipfile.ZipFile(io.BytesIO(http.get(f"/api/v1/bestand/{ALBUM_MID}/export").data))
    names = archive.namelist()
    assert "LEESMIJ.txt" in names and "bestand.json" in names
    assert f"pagina_1/jpg/{ids[0]}.jpg" in names
    wikitext = archive.read(f"wikitekst/{ids[0]}.txt").decode("utf-8")
    assert "{{Extracted from|" + ALBUM + "}}" in wikitext
    exported = http.get(f"/api/v1/bestand/{ALBUM_MID}/export?formaat=json").get_json()
    assert exported["objecten"][0]["commons"]["bestandsnaam"].endswith(".jpg")
    assert http.get(f"/api/v1/bestand/{ALBUM_MID}/export?formaat=iiif").status_code == 400


def test_export_without_saved_objects(http):
    response = http.get(f"/api/v1/bestand/{ALBUM_MID}/export")
    assert response.status_code == 404 and response.get_json()["code"] == "nothing_saved"


def test_point_rectangle_and_mask(http):
    point = http.post(PAGE + "/detecties", json={"punt": {"x": 500, "y": 500}}).get_json()
    assert point["object"]["label"] == "klik"
    rect = http.post(PAGE + "/detecties", json={"rechthoek": {"x": 10, "y": 10, "w": 300, "h": 200}}).get_json()
    assert rect["object"]["bron"] == "handmatig"
    refined = http.post(PAGE + "/detecties", json={"masker_voor": rect["object"]["id"]}).get_json()
    assert refined["object"]["masker"] is not None
    assert http.post(PAGE + "/detecties", json={"punt": {"x": "a"}}).status_code == 400


def test_regions_from_commons_and_their_concept(http):
    page = http.get(BOOK).get_json()
    assert page["regio_aantal"] == 13
    result = http.post(BOOK + "/detecties", json={"modus": "commons"}).get_json()
    regions = [o for o in result["objecten"] if o["bron"] == "commons"]
    assert len(regions) == 13
    catherine = next(o for o in regions if o["wikidata"] == "Q179718")
    concept = http.get(f"{BOOK}/object/{catherine['id']}/commons").get_json()
    assert concept["bestandsnaam"].startswith("Catherine of Alexandria – extracted from Book of Hours")
    assert concept["beeldt_af"][0]["q"] == "Q179718"

    changed = http.patch(f"{BOOK}/object/{catherine['id']}/commons", json={"formaat": "png", "caption": {"nl": "Catharina", "en": "Catherine"}}).get_json()
    assert changed["bestandsnaam"].endswith(".png") and changed["caption"]["nl"] == "Catharina"
    assert http.patch(f"{BOOK}/object/{catherine['id']}/commons", json={"formaat": "gif"}).get_json()["code"] == "invalid_concept"
    reset = http.patch(f"{BOOK}/object/{catherine['id']}/commons", json={"herstel": True}).get_json()
    assert reset["formaat"] == "jpg"


def test_upload_menu_check_and_no_upload(http):
    regions = http.post(BOOK + "/detecties", json={"modus": "commons"}).get_json()["objecten"]
    ids = [o["id"] for o in regions[:2]]
    http.post(BOOK + "/uitsneden", json={"ids": ids})
    menu = http.get(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons").get_json()
    assert menu["aantal"] == 2 and menu["upload_aan"] is False
    assert all(item["gekozen"] for item in menu["uitsneden"])
    # The check only reads from Commons; unrecorded titles count as unreachable.
    check = http.post(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons/controle", json={})
    assert check.status_code in (200, 502)
    upload = http.post(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons/uploads", json={})
    assert upload.get_json()["code"] == "not_confirmed"
    upload = http.post(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons/uploads", json={"bevestigd": True})
    assert upload.status_code == 503 and upload.get_json()["code"] == "upload_disabled"


def test_object_patch_trash_and_restore(http):
    obj = http.post(PAGE + "/detecties", json={"prompt": "wapen"}).get_json()["objecten"][0]
    url = f"{PAGE}/object/{obj['id']}"
    assert http.patch(url, json={"bijschrift": {"tekst": "  Een   wapen "}}).get_json()["bijschrift"]["tekst"] == "Een wapen"
    assert http.patch(url, json={"onbekend": 1}).status_code == 400
    assert http.delete(url).get_json()["verwijderd"] == obj["id"]
    assert http.get(url).get_json()["in_prullenbak"] is True
    assert http.get("/api/v1/prullenbak").get_json()["aantal"] == 1
    assert http.patch(url, json={"prullenbak": False}).get_json()["in_prullenbak"] is False
    http.delete(url)
    assert http.delete(f"/api/v1/prullenbak/{ALBUM_MID}/1/{obj['id']}").get_json()["over"] == 0


def test_description_with_dummy(http):
    obj = http.post(PAGE + "/detecties", json={"prompt": "wapen"}).get_json()["objecten"][0]
    url = f"{PAGE}/object/{obj['id']}/beschrijving"
    plan = http.get(url).get_json()
    assert plan["beschrijving"] is None and plan["betaald"] is False
    described = http.post(url, json={}).get_json()
    assert described["object"]["beschrijving"]["onderwerp_en"] == "Coat of arms"
    assert "beschrijving" not in http.delete(url).get_json()
    overview = http.post(PAGE + "/inventaris", json={}).get_json()
    assert overview["inventaris"]["zoektermen"]


def test_merge_duplicates_and_overviews(http):
    http.post(PAGE + "/detecties", json={"modus": "alles"})
    merged = http.patch(PAGE + "/objecten", json={"samenvoegen": True}).get_json()
    assert merged["samengevoegd"] >= 0
    all_objects = http.get("/api/v1/objecten?bron=dummy").get_json()
    assert all_objects["aantal"] == len(merged["objecten"])
    assert http.get("/api/v1/objecten?opgeslagen=1").get_json()["aantal"] == 0
    status = http.get("/api/v1/status").get_json()
    assert status["modus"] == "dummy" and status["upload"] is False and status["gebruiker"] is None
    usage = http.get("/api/v1/verbruik").get_json()
    assert usage["totaal"]["aanroepen"] == 0
    assert http.get("/api/v1/verbruik/2026-11-03").get_json()["aanroepen"] == 0
    assert http.get("/api/v1/verbruik?van=gisteren").status_code == 400


def test_paid_calls_need_a_login(app, http):
    app.extensions["detectiedienst"].detector.betaald = True
    try:
        response = http.post(PAGE + "/detecties", json={"prompt": "wapen"})
        assert response.status_code == 401 and response.get_json()["code"] == "login_required"
        with http.session_transaction() as session:
            session["gebruiker"] = "Iemand"
        response = http.post(PAGE + "/detecties", json={"prompt": "wapen"})
        assert response.status_code == 403 and response.get_json()["code"] == "not_on_access_list"
        # Free things stay free without a login.
        assert http.post(PAGE + "/detecties", json={"rechthoek": {"x": 0, "y": 0, "w": 50, "h": 50}}).status_code == 201
    finally:
        app.extensions["detectiedienst"].detector.betaald = False


# -- OpenAPI in sync with the routes (CLAUDE.md) ---------------------------------------------


def _flask_routes(app):
    routes = set()
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/v1"):
            continue
        path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rule.rule[len("/api/v1"):])
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            routes.add((method.lower(), path))
    return routes


def test_openapi_describes_every_route_and_nothing_else(app):
    described = {(method, path) for path, ops in openapi_spec()["paths"].items() for method in ops}
    assert described == _flask_routes(app)


def test_openapi_served(http):
    spec = http.get("/api/v1/openapi.json").get_json()
    assert spec["openapi"].startswith("3.1") and spec["info"]["title"] == "Commons Cutter API"


def test_docs_api_md_mentions_every_path(app):
    from cutter.config import ROOT_DIR

    text = (ROOT_DIR / "docs" / "api.md").read_text(encoding="utf-8")
    for _method, path in _flask_routes(app):
        assert path in text, path


# -- Pages -------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/objecten", "/commons?mid=M1", "/verbruik", "/docs", "/privacy", "/changelog", "/sitemap"])
def test_pages_render(http, path):
    response = http.get(path)
    assert response.status_code == 200
    assert "Commons Cutter" in response.get_data(as_text=True)


def test_page_language_follows_uselang_then_session_then_browser(http):
    english = http.get("/", headers={"Accept-Language": "en-GB"}).get_data(as_text=True)
    assert '<html lang="en">' in english and "This is an experiment" in english
    dutch = http.get("/?uselang=nl").get_data(as_text=True)
    assert '<html lang="nl">' in dutch and "Dit is een experiment" in dutch
    remembered = http.get("/", headers={"Accept-Language": "en"}).get_data(as_text=True)
    assert '<html lang="nl">' in remembered


def test_page_embeds_config_and_texts(http):
    page = http.get("/?uselang=en&mid=M5").get_data(as_text=True)
    match = re.search(r'<script id="cutter-config" type="application/json">(.*?)</script>', page, re.S)
    config = json.loads(match.group(1))
    assert config["taal"] == "en" and config["teksten"]["input.open"] == "Open"
    assert config["start"]["mid"] == "M5" and config["modus"] == "dummy"
    assert {g["sleutel"] for g in config["snel_zoeken"]} >= {"heraldiek", "portretten"}


def test_pages_use_built_assets_without_cdn(http):
    page = http.get("/").get_data(as_text=True)
    assert "unpkg" not in page and "jsdelivr" not in page and "cdn." not in page


def test_robots_and_sitemap(http):
    robots = http.get("/robots.txt").get_data(as_text=True)
    assert "Disallow: /api/" in robots and "Disallow: /commons" in robots
    sitemap = http.get("/sitemap.xml").get_data(as_text=True)
    assert "<loc>http://localhost/docs</loc>" in sitemap and "/api/" not in sitemap


def test_local_user_only_counts_in_debug_mode(app, http):
    app.config["LOKALE_GEBRUIKER"] = "OlafJanssen"
    app.extensions["detectiedienst"].detector.betaald = True
    try:
        app.debug = False
        assert http.get("/api/v1/status").get_json()["gebruiker"] is None
        assert http.post(PAGE + "/detecties", json={"prompt": "wapen"}).get_json()["code"] == "login_required"
        app.debug = True
        assert http.get("/api/v1/status").get_json()["gebruiker"] == "OlafJanssen"
        assert "OlafJanssen (" in http.get("/").get_data(as_text=True)
    finally:
        app.debug = False
        app.extensions["detectiedienst"].detector.betaald = False


def test_back_link_on_every_page_but_the_start(http):
    assert 'class="cc-terug"' not in http.get("/").get_data(as_text=True)
    objects = http.get("/objecten?uselang=nl").get_data(as_text=True)
    assert 'href="/" data-terug>' in objects and "Terug naar de Commons Cutter" in objects
    assert 'href="/?mid=M5">' in http.get("/commons?mid=M5").get_data(as_text=True)
