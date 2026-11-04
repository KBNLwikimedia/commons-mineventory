"""The Commons concept (9.1-9.5): file name, wikitext, SDC, check. No upload."""

import pytest
from conftest import ALBUM

from cutter import concept


def test_filename_subject_first_in_english():
    name = concept.filename("coat of arms", ALBUM, "jpg")
    assert name == "Coat of arms – extracted from Album amicorum van Jacob van Bronckhorst van Batenburg (8077131573).jpg"


def test_filename_numbering_and_forbidden_characters():
    name = concept.filename("Saint [John] / Baptist: #1", "File:A.b.jpg", "png", number=2)
    assert name == "Saint -John- - Baptist- -1 (2) – extracted from A.b.png"
    assert not concept.FORBIDDEN.search(name)


def test_filename_is_at_most_240_bytes_and_keeps_the_subject():
    long_original = "File:" + "Ééné heel lange titel " * 30 + ".tif"
    name = concept.filename("Catherine of Alexandria", long_original, "jpg")
    assert len(name.encode("utf-8")) <= concept.MAX_NAME_BYTES
    assert name.startswith("Catherine of Alexandria – extracted from Ééné") and name.endswith("….jpg")


def test_subject_choice():
    assert concept.subject_of({"bron": "commons", "label_en": "Catherine of Alexandria", "label": "Catharina"}) == "Catherine of Alexandria"
    assert concept.subject_of({"label": "coat of arms", "beschrijving": {"onderwerp_en": "Arms of Batenburg"}}) == "Arms of Batenburg"
    assert concept.subject_of({"label": "portrait"}) == "portrait"
    assert concept.subject_of({"label": "klik"}) == "Detail"


def test_concept_of_a_region(book):
    from cutter import regios

    page = {"breedte": book["breedte"], "hoogte": book["hoogte"]}
    region = next(o for o in regios.depicts_regions(book, page, book["_labels"]) if o["wikidata"] == "Q179718")
    region["label_nl"] = region["label"]
    c = concept.concept(book, region)
    assert c["bestandsnaam"] == (
        "Catherine of Alexandria – extracted from Book of Hours of Philip of Burgundy - KW76F - folio 283r - "
        "Heaven - All Saints - Jean Le Tavernier.jpg"
    )
    assert c["beeldt_af"] == [{"q": "Q179718", "label": region["label"]}]
    assert c["gekozen"] and c["upload_toegestaan"]
    text = c["wikitekst"]
    assert "{{Extracted from|File:Book of Hours of Philip of Burgundy" in text
    assert "[[Category:Uploaded with Commons Cutter]]" in text
    assert "=={{int:license-header}}==" in text
    p180 = [claim for claim in c["sdc"]["claims"] if claim["mainsnak"]["property"] == "P180"]
    assert p180 == [{"mainsnak": concept._item_snak("P180", "Q179718"), "type": "statement", "rank": "normal"}]
    assert "qualifiers" not in p180[0]  # no P2677 on the cut-out
    assert "[[File:" in c["samenvatting"] or "[[" in c["samenvatting"]


def test_concept_of_the_album_copies_licence_and_maker(album):
    obj = {"id": "obj-1", "label": "coat of arms", "bron": "dummy", "box": {"x": 0, "y": 0, "w": 10, "h": 10}}
    c = concept.concept(album, obj)
    assert "{{PD-art|PD-old-70-1923}}" in c["wikitekst"]
    assert "Koninklijke Bibliotheek" in c["maker"]
    assert "|date=2010-11-26 14:49" in c["wikitekst"]
    assert "flickrreview" not in c["wikitekst"].lower().split("<!--")[0]
    assert "licentiecontrole" in c["wikitekst"]  # a reference to the original instead
    assert "[[Category:Album Amicorum]]" in c["wikitekst"]
    assert not any(cat["naam"] == "PD-old-70-expired" for cat in c["categorieen"])  # hidden ones never


def test_artwork_template_is_taken_over():
    file = {
        "titel": "File:Painting.jpg",
        "categorieen": [],
        "rechten": {"labels": ["in_orde"], "upload_toegestaan": True},
        "_wikitekst": "{{Artwork\n|artist={{Creator:X}}\n|title=Old title\n|date=1650\n|institution={{Institution:Y}}\n"
        "|accession number=SK-A-1\n|source=museum\n}}\n== {{int:license-header}} ==\n{{PD-art|PD-old-100}}",
    }
    c = concept.concept(file, {"id": "o", "label": "portrait"})
    assert c["wikitekst"].startswith("=={{int:filedesc}}==\n{{Artwork")
    assert "|artist={{Creator:X}}" in c["wikitekst"] and "|accession number=SK-A-1" in c["wikitekst"]
    assert "Old title" not in c["wikitekst"] and "|source={{Extracted from|File:Painting.jpg}}" in c["wikitekst"]


def test_user_changes_and_format(album):
    obj = {
        "id": "o", "label": "coat of arms", "box": {"x": 0, "y": 0, "w": 1, "h": 1},
        "commons": {"formaat": "png", "categorieen": [{"naam": "Coats of arms", "gekozen": True}], "image_extracted": False},
    }
    c = concept.concept(album, obj)
    assert c["bestandsnaam"].endswith(".png") and c["formaat"] == "png"
    assert "[[Category:Coats of arms]]" in c["wikitekst"] and "Album Amicorum" not in c["wikitekst"]
    assert c["image_extracted"] is False


def test_trademark_needs_a_confirmation(album):
    obj = {"id": "o", "label": "logo", "beschrijving": {"soort": "logo"}, "box": {"x": 0, "y": 0, "w": 1, "h": 1}}
    c = concept.concept(album, obj)
    assert c["rechten"]["label"] == "merk" and not c["gekozen"] and not c["upload_toegestaan"]
    obj["commons"] = {"merk_bevestigd": "Historisch logo, geen bescherming meer"}
    assert concept.concept(album, obj)["upload_toegestaan"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"onbekend": 1},
        {"formaat": "gif"},
        {"bestandsnaam": "a|b.jpg"},
        {"bestandsnaam": "x" * 300},
        {"caption": {"nl": "x" * 251}},
        {"beeldt_af": [{"q": "X1"}]},
        {"categorieen": ["los"]},
        {"merk_bevestigd": ""},
    ],
)
def test_validate_patch_refuses(body):
    with pytest.raises(ValueError):
        concept.validate_patch(body)


class CheckClient:
    def titles_exist(self, titles):
        return {t: t in ("File:Taken.jpg", "Category:Real") for t in titles}

    def files_with_sha1(self, sha1):
        return ["File:Same.jpg"] if sha1 == "dup" else []


def test_check_before_upload():
    base = {"categorieen": [{"naam": "Real", "gekozen": True}, {"naam": "Fake", "gekozen": True}], "upload_toegestaan": True}
    concepts = {"a": {**base, "bestandsnaam": "Taken.jpg"}, "b": {**base, "bestandsnaam": "Free.jpg", "categorieen": [{"naam": "Real", "gekozen": True}]}}
    result = concept.check(CheckClient(), concepts, {"a": "dup", "b": "unique"})
    codes = {w["code"] for w in result["a"]["waarschuwingen"]}
    assert codes == {"exists", "duplicate", "missing_category"}
    assert result["a"]["ontbrekende_categorieen"] == ["Fake"]
    assert result["b"]["in_orde"]


# -- Date and maker from the work's Wikidata item ------------------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        ({"time": "+1920-05-17T00:00:00Z", "precision": 11}, "1920-05-17"),
        ({"time": "+1920-05-00T00:00:00Z", "precision": 10}, "1920-05"),
        ({"time": "+1920-00-00T00:00:00Z", "precision": 9}, "1920"),
        ({"time": "+1920-00-00T00:00:00Z", "precision": 8}, "{{other date|decade|1920}}"),
        ({"time": "+1650-00-00T00:00:00Z", "precision": 7}, "{{other date|century|17}}"),
        ({"time": "-0300-00-00T00:00:00Z", "precision": 9}, None),
        (None, None),
    ],
)
def test_wikitext_date(value, expected):
    from cutter import sdc

    assert sdc.wikitext_date(value) == expected


def test_picture_book_gets_date_and_maker_from_wikidata(client):
    page = client.load_file("M90890204")  # {{Book}} with |Date= empty and |Wikidata=Q72752528
    assert page["werk"]["wikidata"] == "Q72752528"
    assert page["werk"]["datum"] == "{{other date|decade|1920}}" and page["werk"]["datum_eigenschap"] == "P577"
    c = concept.concept(page, {"id": "o", "label": "doll", "box": {"x": 0, "y": 0, "w": 1, "h": 1}})
    assert c["datum"] == "{{other date|decade|1920}}"
    assert c["herkomst"]["datum"] == {"bron": "wikidata", "item": "Q72752528", "eigenschap": "P577"}
    assert c["maker"] == "{{Unknown|author}}"  # P50 no value, P110 unknown value
    text = c["wikitekst"]
    # {{Book}} keeps its own capitalised parameter names, the book's data and its Wikidata link.
    assert text.startswith("=={{int:filedesc}}==\n{{Book\n")
    assert "|Date={{other date|decade|1920}}" in text and "|date=" not in text
    assert "|Author={{Unknown|author}}" in text
    assert "|City=Haarlem" in text and "|Language=Dutch" in text and "|Wikidata=Q72752528" in text
    assert "|Source={{Extracted from|File:003-KW XKZ 0214-Buiten waar de vogels fluiten-page3.jpg}}" in text
    assert "|Other_versions=" in text


def test_date_from_the_wikitext_wins(album):
    c = concept.concept(album, {"id": "o", "label": "x", "box": {"x": 0, "y": 0, "w": 1, "h": 1}})
    assert c["herkomst"]["datum"] == {"bron": "wikitekst"}
    assert c["herkomst"]["maker"] == {"bron": "wikitekst"}


def test_original_regions_for_the_cutout():
    from cutter.concept import original_regions

    file = {"paginas": 1, "_sdc": {"beeldt_af": [{"soort": "item", "waarde": "Q1420", "kwalificatoren": {"P2677": ["pct:10,20,25,50"]}}]}}
    page = {"breedte": 2000, "hoogte": 1000}
    obj = {"box": {"x": 200, "y": 200, "w": 500, "h": 500}}
    result = original_regions(file, page, obj, {"beeldt_af": [{"q": "Q43115"}, {"q": "Q1420"}]})
    assert result["regios"] == [
        {"q": "Q43115", "positie": "pct:10,20,25,50", "aanwezig": False},
        {"q": "Q1420", "positie": "pct:10,20,25,50", "aanwezig": True},
    ]
    [claim] = result["sdc"]["claims"]
    assert claim["mainsnak"]["datavalue"]["value"]["id"] == "Q43115"
    assert claim["qualifiers"]["P2677"][0]["datavalue"]["value"] == "pct:10,20,25,50"
    assert original_regions({**file, "paginas": 3}, page, obj, {"beeldt_af": []}) is None


def test_sdc_has_file_facts_and_depicts_without_position():
    from cutter.concept import structured_data

    file = {"_sdc": {}}
    c = {"caption": {"en": "Man"}, "beeldt_af": [{"q": "Q43115"}], "formaat": "png"}
    facts = {"sha1": "abc", "bytes": 1234, "breedte": 200, "hoogte": 400}
    claims = structured_data(file, c, facts)["claims"]
    by_prop = {}
    for claim in claims:
        by_prop.setdefault(claim["mainsnak"]["property"], []).append(claim)
    depicts = by_prop["P180"]
    assert [d["mainsnak"]["datavalue"]["value"]["id"] for d in depicts] == ["Q43115"]
    assert "qualifiers" not in depicts[0]
    assert by_prop["P31"][0]["mainsnak"]["datavalue"]["value"]["id"] == "Q1250322"
    assert by_prop["P1163"][0]["mainsnak"]["datavalue"]["value"] == "image/png"
    assert by_prop["P4092"][0]["qualifiers"]["P459"][0]["datavalue"]["value"]["id"] == "Q13414952"
    assert by_prop["P3575"][0]["mainsnak"]["datavalue"]["value"]["amount"] == "+1234"
    assert by_prop["P2049"][0]["mainsnak"]["datavalue"]["value"]["amount"] == "+200"
    assert by_prop["P2048"][0]["mainsnak"]["datavalue"]["value"]["amount"] == "+400"


def test_sdc_drops_subject_has_role_from_the_collection():
    from cutter.concept import structured_data

    collection = {"property": "P195", "snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q1526131"}}}
    role = [{"property": "P2868", "snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q29188408"}}}]
    file = {"_sdc": {"collectie": [{"_mainsnak": collection, "_qualifiers": {"P2868": role}}]}}
    c = {"caption": {}, "beeldt_af": [], "formaat": "jpg"}
    [claim] = [x for x in structured_data(file, c)["claims"] if x["mainsnak"]["property"] == "P195"]
    assert "qualifiers" not in claim
