"""Exports of the list pages (Changelog, Usage, Objects) and GET /api/v1/changelog."""

import csv
import io
import json
import xml.etree.ElementTree as ET
import zipfile

from cutter import export

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _sheet(data):
    """The rows of an .xlsx as lists of cell values; every part must be well-formed XML."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            ET.fromstring(archive.read(name))
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    return [["".join(c.itertext()) for c in row.findall("s:c", NS)] for row in root.find("s:sheetData", NS)]


def test_csv_guards_formulas_and_keeps_accents():
    data = export.table_csv([{"a": "=HYPERLINK(1)", "b": "één", "c": True, "d": None}, {"a": -1}], ["a", "b", "c", "d"])
    assert data.startswith(b"\xef\xbb\xbf")
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert rows == [["a", "b", "c", "d"], ["'=HYPERLINK(1)", "één", "true", ""], ["-1", "", "", ""]]


def test_xlsx_text_is_text_and_xml_stays_valid():
    data = export.table_xlsx([{"a": "=1+1 <&>\x01", "b": 2.5, "c": False}], ["a", "b", "c"])
    assert _sheet(data) == [["a", "b", "c"], ["=1+1 <&>", "2.5", "0"]]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "<f>" not in sheet and 't="inlineStr"' in sheet
    assert export._column_name(0) == "A" and export._column_name(26) == "AA"


def test_changelog_as_data(http):
    data = http.get("/api/v1/changelog").get_json()
    assert data["aantal"] == len(data["versies"]) > 0
    item = next(s for v in data["versies"] for s in v["secties"])["items"][0]
    assert set(item) == {"markdown", "tekst"} and not item["markdown"].startswith("- ")


def test_changelog_export_follows_the_facets(http):
    everything = http.get("/api/v1/changelog/export").get_json()
    assert everything["aantal"] == len(everything["rijen"]) > 10
    some = http.get("/api/v1/changelog/export?soort=Opgelost&reeks=0.33").get_json()
    assert 0 < some["aantal"] < everything["aantal"]
    assert {(r["soort"], r["reeks"]) for r in some["rijen"]} == {("Opgelost", "0.33")}
    assert http.get("/api/v1/changelog/export?q=zzzznietbestaand").get_json()["aantal"] == 0


def test_export_formats_and_headers(http):
    response = http.get("/api/v1/changelog/export?formaat=xlsx")
    assert response.mimetype.endswith("spreadsheetml.sheet")
    assert ".xlsx" in response.headers["Content-Disposition"] and response.headers["Content-Disposition"].startswith("attachment")
    assert _sheet(response.data)[0] == ["versie", "datum", "reeks", "soort", "tekst"]
    assert http.get("/api/v1/changelog/export?formaat=csv").mimetype == "text/csv"
    assert http.get("/api/v1/changelog/export?formaat=pdf").status_code == 400


def test_usage_export_has_the_whole_log_and_filters(app, http):
    log = app.extensions["detectiedienst"].verbruik
    for i in range(3):
        log.register({"bestand": "M1", "titel": "File:Een.jpg", "pagina": 1, "term": f"term{i}", "model": "sam-3.1"})
    log.register({"soort": "aanvulling", "bestand": "M2", "titel": "File:Twee.jpg", "pagina": 1, "model": "muse-image-1.0"}, cost=0.01)
    rows = http.get("/api/v1/verbruik/export").get_json()["rijen"]
    assert len(rows) == 4 and rows[0]["soort"] == "aanvulling"  # newest first
    assert rows[1]["soort"] == "sam" and " " in rows[1]["tijd"]
    assert http.get("/api/v1/verbruik/export?model=muse-image-1.0").get_json()["aantal"] == 1
    assert http.get("/api/v1/verbruik/export?bestand=M1&q=term2").get_json()["aantal"] == 1


def test_usage_export_only_for_trusted_users_on_a_server(app, http):
    app.testing = False
    assert http.get("/api/v1/verbruik/export").status_code == 403


def test_objects_export_flat_rows_and_facets(app, http):
    service = app.extensions["detectiedienst"]
    plain = {"mid": "M1", "pagina": 1, "id": "a", "bron": "sam", "status": "kandidaat", "score": 0.91234, "box": {"x": 1, "y": 2, "w": 3, "h": 4}, "app_url": "/?mid=M1", "uitsnede_url": "/u.jpg"}
    saved = {**plain, "mid": "M2", "id": "b", "bron": "groep", "groep": {"naam": "Family"}, "opgeslagen": {"jpg": "x"}, "bijschrift": {"tekst": "Mijn tekst"}, "beschrijving": {"onderwerp": "Pop"}}
    service.all_objects = lambda trash=False, **kw: [plain] if trash else [plain, saved]
    rows = http.get("/api/v1/objecten/export").get_json()["rijen"]
    assert rows[0]["score"] == 0.912 and rows[0]["breedte"] == 3 and rows[0]["opgeslagen"] is False
    assert rows[0]["app_url"].startswith("http") and rows[1]["naam"] == "Family" and rows[1]["bijschrift"] == "Mijn tekst"
    assert http.get("/api/v1/objecten/export?opgeslagen=1").get_json()["aantal"] == 1
    assert http.get("/api/v1/objecten/export?bron=sam,groep&mid=M2").get_json()["aantal"] == 1
    assert http.get("/api/v1/prullenbak/export").get_json()["aantal"] == 1
    assert json.loads(http.get("/api/v1/objecten/export?q=pop").data)["rijen"][0]["id"] == "b"
    assert http.get("/api/v1/objecten/export?q=http").get_json()["aantal"] == 0  # the search does not look in links
