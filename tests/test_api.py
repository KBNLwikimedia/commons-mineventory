"""REST API (functional design 11) and pages, with recorded Commons responses."""

import io
import json
import re
from urllib.parse import quote
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

    jpg = http.get(f"{PAGE}/objecten/{ids[0]}/uitsnede.jpg")
    png = http.get(f"{PAGE}/objecten/{ids[0]}/uitsnede.png")
    assert jpg.mimetype == "image/jpeg" and png.mimetype == "image/png"
    assert http.get(f"{PAGE}/objecten/{ids[0]}/uitsnede.jpg?w=100").status_code == 200
    assert http.get(f"{PAGE}/objecten/{ids[0]}/masker.png").mimetype == "image/png"

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
    concept = http.get(f"{BOOK}/objecten/{catherine['id']}/commons").get_json()
    assert concept["bestandsnaam"].startswith("Catherine of Alexandria – extracted from Book of Hours")
    assert concept["beeldt_af"][0]["q"] == "Q179718"

    changed = http.patch(f"{BOOK}/objecten/{catherine['id']}/commons", json={"formaat": "png", "caption": {"nl": "Catharina", "en": "Catherine"}}).get_json()
    assert changed["bestandsnaam"].endswith(".png") and changed["caption"]["nl"] == "Catharina"
    assert http.patch(f"{BOOK}/objecten/{catherine['id']}/commons", json={"formaat": "gif"}).get_json()["code"] == "invalid_concept"
    reset = http.patch(f"{BOOK}/objecten/{catherine['id']}/commons", json={"herstel": True}).get_json()
    assert reset["formaat"] == "jpg"


def test_upload_menu_check_and_no_upload(http):
    regions = http.post(BOOK + "/detecties", json={"modus": "commons"}).get_json()["objecten"]
    ids = [o["id"] for o in regions[:2]]
    http.post(BOOK + "/uitsneden", json={"ids": ids})
    menu = http.get(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons").get_json()
    assert menu["aantal"] == 2 and menu["upload_aan"] is False
    assert all(item["gekozen"] for item in menu["uitsneden"])
    # The check only reads from Commons; unrecorded titles count as unreachable.
    check = http.get(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons/controle")
    assert check.status_code in (200, 502)
    assert http.get(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons/controle?objecten=geen-pagina").get_json()["code"] == "invalid_parameter"
    upload = http.post(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons/uploads", json={})
    assert upload.get_json()["code"] == "not_confirmed"
    upload = http.post(f"/api/v1/bestand/{BOOK_OF_HOURS_MID}/commons/uploads", json={"bevestigd": True})
    assert upload.status_code == 503 and upload.get_json()["code"] == "upload_disabled"


def test_object_patch_trash_and_restore(http):
    obj = http.post(PAGE + "/detecties", json={"prompt": "wapen"}).get_json()["objecten"][0]
    url = f"{PAGE}/objecten/{obj['id']}"
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
    url = f"{PAGE}/objecten/{obj['id']}/beschrijving"
    plan = http.get(url).get_json()
    assert plan["beschrijving"] is None and plan["betaald"] is False
    described = http.post(url, json={}).get_json()
    assert described["object"]["beschrijving"]["onderwerp_en"] == "Coat of arms"
    first = described["object"]["beschrijving"]
    other = http.post(url, json={"opnieuw": True, "aanwijzing": "alleen de rand"}).get_json()["object"]["beschrijving"]
    history = http.get(url + "/geschiedenis").get_json()["geschiedenis"]
    assert history[0]["tijdstempel"] == first["tijdstempel"] and other["aanwijzing"] == "alleen de rand"
    back = http.put(url, json={"versie": history[0]["versie"]}).get_json()["beschrijving"]
    assert back["tijdstempel"] == first["tijdstempel"] and back.get("aanwijzing") is None
    history = http.get(url + "/geschiedenis").get_json()["geschiedenis"]
    assert any(h.get("aanwijzing") == "alleen de rand" for h in history)
    assert http.put(url, json={"versie": "nooit"}).status_code == 404
    assert http.put(url, json={}).status_code == 400
    # One version of the history has a path of its own.
    gone = http.delete(f"{url}/geschiedenis/{quote(history[0]['versie'], safe='')}").get_json()["geschiedenis"]
    assert len(gone) == len(history) - 1
    preview = http.get(url + "/invoer.jpg?marge=0.5")
    assert preview.status_code == 200 and preview.mimetype == "image/jpeg"
    # A larger version for the lightbox (never larger than the original piece; at most 4000 px).
    from PIL import Image as PILImage

    small = PILImage.open(io.BytesIO(preview.data)).size
    large = PILImage.open(io.BytesIO(http.get(url + "/invoer.jpg?marge=0.5&max=3000").data)).size
    assert max(large) >= max(small) and max(large) <= 3000
    assert http.get(url + "/invoer.jpg?max=veel").status_code == 400
    wide = http.post(url, json={"opnieuw": True, "marge": 0.5}).get_json()
    assert wide["object"]["beschrijving"]["marge"] == 0.5
    hinted = http.post(url, json={"opnieuw": True, "aanwijzing": "alleen het wapen"}).get_json()
    assert hinted["object"]["beschrijving"]["aanwijzing"] == "alleen het wapen"
    assert http.post(url, json={"aanwijzing": 5}).status_code == 400
    described = http.post(url, json={"opnieuw": True}).get_json()
    assert described["object"]["beschrijving"]["aanwijzing"] is None
    ai_text = described["object"]["beschrijving"]["beschrijving_en"]
    edited = http.patch(url, json={"beschrijving_en": " A coat of arms. ", "onderwerp": "Wapen"}).get_json()["beschrijving"]
    assert edited["beschrijving_en"] == "A coat of arms." and edited["bewerkt"] is True
    assert edited["ai_origineel"]["beschrijving_en"] == ai_text
    # Back to the AI text: nothing is edited any more.
    back = http.patch(url, json={"beschrijving_en": ai_text, "onderwerp": edited["ai_origineel"]["onderwerp"]}).get_json()["beschrijving"]
    assert back["bewerkt"] is False and "ai_origineel" not in back
    assert http.patch(url, json={"soort": "x"}).status_code == 400
    typed = http.patch(url, json={"tekst_rond_beeld": "Wapen van X"}).get_json()["beschrijving"]
    assert typed["tekst_rond_beeld"] == "Wapen van X" and typed["bewerkt"] is True
    cleared = http.patch(url, json={"tekst_rond_beeld": ""}).get_json()["beschrijving"]
    assert not cleared["tekst_rond_beeld"]
    assert "beschrijving" not in http.delete(url).get_json()
    assert http.patch(url, json={"beschrijving": "x"}).status_code == 409
    overview = http.post(PAGE + "/inventaris", json={}).get_json()
    assert overview["inventaris"]["zoektermen"]
    # One part of the overview: its own path.
    assert http.delete(PAGE + "/inventaris/zoektermen").get_json()["inventaris"]["zoektermen"] == []
    assert http.post(PAGE + "/inventaris/zoektermen", json={}).get_json()["inventaris"]["zoektermen"]
    assert http.delete(PAGE + "/inventaris/alles").status_code == 404
    # The detail level (the slider): fewer or more search terms, remembered with the overview.
    one = http.post(PAGE + "/inventaris/zoektermen", json={"detailniveau": "hoofdonderwerp"}).get_json()["inventaris"]
    assert len(one["zoektermen"]) == 1 and one["detailniveau"] == "hoofdonderwerp"
    many = http.post(PAGE + "/inventaris/zoektermen", json={"detailniveau": "details"}).get_json()["inventaris"]
    assert len(many["zoektermen"]) > 3 and many["detailniveau"] == "details"
    assert http.post(PAGE + "/inventaris/zoektermen", json={"detailniveau": "alles"}).status_code == 400
    http.post(PAGE + "/inventaris/zoektermen", json={"detailniveau": "normaal"})
    # The description of the image by hand, with its earlier versions.
    first = http.get(PAGE + "/inventaris").get_json()["inventaris"]
    edited = http.patch(PAGE + "/inventaris", json={"samenvatting": "Met de hand."}).get_json()["inventaris"]
    assert edited["samenvatting"] == "Met de hand." and edited["bewerkt"] and edited["ai_origineel"]["samenvatting"] == first["samenvatting"]
    assert edited["zoektermen"] == first["zoektermen"] or edited["zoektermen"]
    history = http.get(PAGE + "/inventaris/geschiedenis").get_json()["geschiedenis"]
    assert history[0]["samenvatting"] == first["samenvatting"]
    assert http.patch(PAGE + "/inventaris", json={"onbekend": "x"}).status_code == 400
    back = http.put(PAGE + "/inventaris/beschrijving", json={"versie": history[0]["versie"]}).get_json()
    assert back["inventaris"]["samenvatting"] == first["samenvatting"] and not back["inventaris"].get("bewerkt")
    assert any(h["samenvatting"] == "Met de hand." for h in back["geschiedenis"])
    assert http.put(PAGE + "/inventaris/zoektermen", json={"versie": "x"}).status_code == 404
    gone = http.delete(f"{PAGE}/inventaris/geschiedenis/{quote(back['geschiedenis'][0]['versie'], safe='')}").get_json()["geschiedenis"]
    assert len(gone) == len(back["geschiedenis"]) - 1


def test_merge_duplicates_and_overviews(http):
    http.post(PAGE + "/detecties", json={"modus": "alles"})
    merged = http.post(PAGE + "/samenvoegingen", json={}).get_json()
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
        # A session cookie is not a login (until OAuth sets one): even a forged one counts for nothing.
        with http.session_transaction() as session:
            session["gebruiker"] = "OlafJanssen"
        assert http.post(PAGE + "/detecties", json={"prompt": "wapen"}).status_code == 401
        # Locally, in debug mode, LOKALE_GEBRUIKER stands in for a login; not on the list: 403.
        app.debug = True
        app.config["LOKALE_GEBRUIKER"] = "Iemand"
        response = http.post(PAGE + "/detecties", json={"prompt": "wapen"})
        assert response.status_code == 403 and response.get_json()["code"] == "not_on_access_list"
        app.debug = False
        app.config["LOKALE_GEBRUIKER"] = ""
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
    assert spec["openapi"].startswith("3.1") and spec["info"]["title"] == "Commons Mineventory API"


def test_docs_api_md_mentions_every_path(app):
    from cutter.config import ROOT_DIR

    text = (ROOT_DIR / "docs" / "api.md").read_text(encoding="utf-8")
    for _method, path in _flask_routes(app):
        assert path in text, path


# -- Pages -------------------------------------------------------------------------------------


def test_privacy_statement_in_both_languages(http):
    assert "Wat de app van jou verwerkt" in http.get("/privacy?uselang=nl").get_data(as_text=True)
    assert "What the app processes about you" in http.get("/privacy?uselang=en").get_data(as_text=True)


@pytest.mark.parametrize("path", ["/", "/objecten", "/commons?mid=M1", "/verbruik", "/docs", "/privacy", "/changelog", "/sitemap"])
def test_pages_render(http, path):
    response = http.get(path)
    assert response.status_code == 200
    assert "Commons Mineventory" in response.get_data(as_text=True)


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
    assert "snel_zoeken" not in config  # removed in 0.21.0


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
    assert 'href="/" data-terug>' in objects and "Terug naar de Commons Mineventory" in objects
    assert 'href="/?mid=M5">' in http.get("/commons?mid=M5").get_data(as_text=True)


def test_concept_carries_the_ai_texts(http):
    obj = http.post(PAGE + "/detecties", json={"prompt": "wapen"}).get_json()["objecten"][0]
    url = f"{PAGE}/objecten/{obj['id']}"
    assert http.get(url + "/commons").get_json()["ai"] is None
    http.post(url + "/beschrijving", json={})
    ai = http.get(url + "/commons").get_json()["ai"]
    assert ai["caption"]["en"] == "Coat of arms" and ai["beschrijving"]["nl"].startswith("Voorbeeldbeschrijving")


def test_cutout_view_or_download_with_the_concept_name(http):
    obj = http.post(PAGE + "/detecties", json={"rechthoek": {"x": 0, "y": 0, "w": 200, "h": 100}}).get_json()["object"]
    url = f"{PAGE}/objecten/{obj['id']}/uitsnede.jpg"
    shown = http.get(url).headers["Content-Disposition"]
    saved = http.get(url + "?download=1").headers["Content-Disposition"]
    assert shown.startswith("inline;") and saved.startswith("attachment;")
    # "Detail – extracted from …": an ASCII fallback and the full UTF-8 name.
    assert 'filename="Detail _ extracted from Album amicorum' in saved
    assert "filename*=UTF-8''Detail%20%E2%80%93%20extracted%20from%20Album" in saved and saved.endswith(".jpg")
    png = http.get(f"{PAGE}/objecten/{obj['id']}/uitsnede.png?download=1").headers["Content-Disposition"]
    assert png.endswith(".png")


def test_changes_only_from_the_app_itself(http):
    """CSRF: another website cannot make the browser change something or spend money."""
    url = PAGE + "/detecties"
    body = {"rechthoek": {"x": 0, "y": 0, "w": 50, "h": 50}}
    assert http.post(url, json=body, headers={"Origin": "https://evil.example"}).status_code == 403
    assert http.post(url, json=body, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert http.post(url, data="{}", headers={"Content-Type": "text/plain"}).status_code == 415
    assert http.post(url, json=body, headers={"Origin": "http://localhost", "Sec-Fetch-Site": "same-origin"}).status_code == 201
    assert http.get(PAGE, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 200  # reading stays open


def test_config_in_the_page_cannot_break_out_of_its_script(http):
    page = http.get("/?url=%3C!--%3Cscript%3E%3C/script%3E").get_data(as_text=True)
    config = page.split('<script id="cutter-config" type="application/json">', 1)[1].split("</script>", 1)[0]
    assert "<" not in config and "\\u003c!--" in config


@pytest.mark.parametrize("body", [
    {"punt": {"x": "NaN", "y": 1}},
    {"punt": {"x": 1}},
    {"punt": "midden"},
    {"rechthoek": {"x": "inf", "y": 0, "w": 10, "h": 10}},
    {"prompt": "wapen", "minscore": 2},
])
def test_wrong_detection_input_is_a_400(http, body):
    assert http.post(PAGE + "/detecties", json=body).status_code == 400


def test_wrong_ids_are_a_400(http):
    assert http.patch(PAGE + "/objecten", json={"geselecteerd": [["x"]]}).status_code == 400
    assert http.delete("/api/v1/prullenbak", json={"objecten": [{"mid": "M1"}]}).status_code == 400


def test_usage_and_emptying_the_trash_need_the_access_list_on_a_server(app, http):
    """On a server (no debug) the usage log (user names) and emptying everybody's trash
    are only for users on the access list; locally (debug) nothing changes."""
    testing = app.testing
    app.debug, app.testing = False, False  # as on a server
    try:
        assert http.get("/api/v1/verbruik").status_code == 403
        assert http.delete("/api/v1/prullenbak").status_code == 403
        app.debug = True  # locally
        assert http.get("/api/v1/verbruik").status_code == 200
    finally:
        app.debug, app.testing = False, testing


def test_old_paths_still_work_and_say_they_are_deprecated(http):
    """Until 0.30.0 the paths from before 0.29.0 work, with Deprecation and a Link to the new path."""
    obj = http.post(PAGE + "/detecties", json={"prompt": "wapen"}).get_json()["objecten"][0]
    old = http.get(f"{PAGE}/object/{obj['id']}")
    assert old.status_code == 200 and old.headers["Deprecation"] == "true"
    assert f"{PAGE}/objecten/{obj['id']}" in old.headers["Link"] and 'rel="successor-version"' in old.headers["Link"]
    new = http.get(f"{PAGE}/objecten/{obj['id']}")
    assert new.status_code == 200 and "Deprecation" not in new.headers
    url = f"{PAGE}/object/{obj['id']}/beschrijving"
    first = http.post(url, json={}).get_json()["object"]["beschrijving"]
    http.post(url, json={"opnieuw": True, "aanwijzing": "x"})
    back = http.post(url + "/terugzetten", json={"tijdstempel": first["tijdstempel"]})
    assert back.status_code == 200 and back.headers["Deprecation"] == "true"
    merged = http.patch(PAGE + "/objecten", json={"samenvoegen": True})
    assert merged.status_code == 200 and "/samenvoegingen" in merged.headers["Link"]


def test_group_and_ungroup(http):
    found = http.post(PAGE + "/detecties", json={"modus": "prompt", "prompt": "flower"}).get_json()
    flowers = [o for o in found["objecten"] if o["zoekterm"] == "flower"]
    assert len(flowers) >= 1
    http.post(PAGE + "/detecties", json={"modus": "prompt", "prompt": "bird"})
    page = http.get(PAGE).get_json()["objecten"]
    assert http.post(PAGE + "/groepen", json={"objecten": [page[0]["id"]]}).status_code == 400
    ids = [o["id"] for o in page[:2]]
    made = http.post(PAGE + "/groepen", json={"objecten": ids})
    assert made.status_code == 201
    group = made.get_json()["object"]
    assert group["bron"] == "groep" and group["groep"]["aantal"] == 2 and group["masker"]["codering"] == "png"
    after = made.get_json()["objecten"]
    assert group["id"] in [o["id"] for o in after] and not set(ids) & {o["id"] for o in after}
    # The group's box holds both members; its mask PNG can be made.
    for member in group["groep"]["leden"]:
        b, g = member["box"], group["box"]
        assert g["x"] <= b["x"] and g["y"] <= b["y"] and b["x"] + b["w"] <= g["x"] + g["w"] and b["y"] + b["h"] <= g["y"] + g["h"]
    assert http.get(f"{PAGE}/objecten/{group['id']}/masker.png").status_code == 200
    # The members' cut-outs can still be shown (the ungroup confirmation lists them).
    assert http.get(f"{PAGE}/objecten/{ids[0]}/uitsnede.jpg?w=96").status_code == 200
    assert group["groep"]["leden"][0]["label_nl"]
    # A new search does not put the members back on their own.
    http.post(PAGE + "/detecties", json={"modus": "prompt", "prompt": "flower, bird"})
    assert not set(ids) & {o["id"] for o in http.get(PAGE).get_json()["objecten"]}
    back = http.delete(f"{PAGE}/groepen/{group['id']}").get_json()["objecten"]
    assert set(ids) <= {o["id"] for o in back} and group["id"] not in [o["id"] for o in back]
    assert http.delete(f"{PAGE}/groepen/{ids[0]}").status_code == 400
    # Group all objects of one search term.
    named = http.post(PAGE + "/groepen", json={"objecten": ids, "naam": "  Vogels  en bloemen "}).get_json()["object"]
    assert named["label_nl"] == named["label_en"] == "Vogels en bloemen"
    http.delete(f"{PAGE}/groepen/{named['id']}")
    by_term = http.post(PAGE + "/groepen", json={"zoekterm": "bird"})
    birds = [o for o in back if o["zoekterm"] == "bird"]
    assert by_term.status_code == (201 if len(birds) >= 2 else 400)


def test_ai_completed_version(http):
    found = http.post(PAGE + "/detecties", json={"modus": "prompt", "prompt": "cat"}).get_json()
    obj = found["objecten"][0]
    url = f"{PAGE}/objecten/{obj['id']}"
    plan = http.get(url + "/aanvulling").get_json()
    assert plan["aangevuld"] is None and plan["model"] == "muse-image-1.0" and plan["betaald"] is False
    assert http.get(url + "/aangevuld.png").status_code == 404
    made = http.post(url + "/aanvulling", json={})
    assert made.status_code == 201
    note = made.get_json()["object"]["aangevuld"]
    assert note["model"] == "muse-image-1.0" and note["uit_cache"] is False and note["afmetingen"][0] > 0
    image = http.get(url + "/aangevuld.png")
    assert image.status_code == 200 and image.data[:4] == b"\x89PNG"
    assert "AI-aangevuld" in image.headers.get("Content-Disposition", "")
    assert http.post(url + "/aanvulling", json={}).get_json()["uit_cache"] is True  # the same cut-out: from the cache
    assert http.delete(url + "/aanvulling").get_json()["object"]["aangevuld"] is None


def test_completion_request_has_no_search():
    from cutter.aanvulling import build_request, prepare

    body = build_request("muse-image-1.0", "x", "data:image/png;base64,", "10x10")
    assert body["tool_enablement"] == {"enable_image_search": False, "enable_web_search": False, "enable_shell": False}
    import io
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGBA", (3000, 1000), (0, 0, 0, 0)).save(buffer, format="PNG")
    sent, size = prepare(buffer.getvalue())
    assert size == "1536x512" and Image.open(io.BytesIO(sent)).getpixel((5, 5)) == (255, 255, 255)
