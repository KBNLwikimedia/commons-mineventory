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


# A KB print in {{Artwork}} as GWToolset uploads it: aliases, KB-only fields, other_fields.
KB_ARTWORK = """=={{int:filedesc}}==
{{Artwork
 |artist             =
 |author             = {{Creator:Jan Kops}}
 |title              = Band van beschilderd blank perkament
 |object type        = Book binding
 |year               = 1751-1760
 |technique          = {{nl|Blank perkament}}
 |size               = {{Size|mm|110|57|31}}
 |gallery            = {{Institution:Koninklijke Bibliotheek}}
 |location           = Bijzondere collecties
 |id                 = Shelfmark 1748 G 10
 |place of creation  = Duitsland(?)
 |publisher          = Luchtmans
 |place of publication = Leiden
 |exhibition history = {{Temporary Exhibition|name=Boekbanden}}
 |depicted people    = Willem I
 |inscriptions       = Ex libris
 |notes              = This object is part of the collection of bookbindings
 |wikidata           = Q123
 |other_fields       = {{Information field|name=Binder/bindery|value=Unknown}}{{Information field|name=Depicted locations|value=Leiden}}
 |source             = Geheugen van Nederland {{Koninklijke Bibliotheek}}
}}
=={{int:license-header}}==
{{PD-art|PD-old-70-1923}}
"""


def kb_file(text=KB_ARTWORK, hidden=("Media contributed by Koninklijke Bibliotheek",)):
    return {
        "titel": "File:Band.jpeg",
        "categorieen": ["Bookbindings"],
        "verborgen_categorieen": list(hidden),
        "rechten": {"labels": ["in_orde"], "upload_toegestaan": True},
        "_wikitekst": text,
    }


def test_kb_artwork_keeps_object_fields_and_drops_picture_fields():
    obj = {"id": "o", "label": "wapen", "beschrijving": {"onderwerp": "wapen", "onderwerp_en": "coat of arms", "tekst_in_beeld": "SPES MEA DEUS"}}
    text = concept.concept(kb_file(), obj)["wikitekst"]
    # Object: kept in the original's own spelling (aliases included).
    for line in ("|object type=Book binding", "|technique={{nl|Blank perkament}}", "|gallery={{Institution:Koninklijke Bibliotheek}}",
                 "|location=Bijzondere collecties", "|id=Shelfmark 1748 G 10", "|place of creation=Duitsland(?)",
                 "|publisher=Luchtmans", "|place of publication=Leiden", "|notes=This object is part of the collection of bookbindings",
                 "|wikidata=Q123", "|year=1751-1760", "|author={{Creator:Jan Kops}}"):
        assert line in text, line
    # Picture and size: not taken over; exhibition history left out (Olaf, 4-11-2026).
    for gone in ("{{Size|mm|110|57|31}}", "Willem I", "Ex libris", "Temporary Exhibition", "Depicted locations", "Band van beschilderd"):
        assert gone not in text, gone
    # New for the detail: own title, depicted part (both languages) and the text in the cut-out.
    assert "|title={{nl|1=wapen}}{{en|1=coat of arms}}" in text
    assert "|depicted part={{nl|1=wapen}}{{en|1=coat of arms}}" in text
    assert "|inscriptions={{Inscription|1=SPES MEA DEUS|type=text|linebreaks=1}}" in text
    assert "{{Information field|name=Binder/bindery|value=Unknown}}" in text
    assert "|source={{Extracted from|File:Band.jpeg}}" in text and "{{Koninklijke Bibliotheek}}" not in text


def test_partner_categories_become_cutout_categories():
    names = [c["naam"] for c in concept.concept(kb_file(), {"id": "o", "label": "x"})["categorieen"]]
    assert names == ["Bookbindings", "Cut-outs from media contributed by Koninklijke Bibliotheek"]
    delpher = kb_file(hidden=("Media from Delpher",))
    assert "Cut-outs from media from Delpher" in [c["naam"] for c in concept.concept(delpher, {"id": "o", "label": "x"})["categorieen"]]
    other = kb_file(hidden=())
    assert [c["naam"] for c in concept.concept(other, {"id": "o", "label": "x"})["categorieen"]] == ["Bookbindings"]


def test_map_keeps_map_data_but_not_its_centre():
    text = ("{{Map\n|title=Kaart van Zeeland\n|map date=1750\n|print date=1752\n|location=Zeeland\n|latitude=51.5\n|longitude=3.8\n"
            "|scale=1:100000\n|legend=Wegen\n|author={{Creator:Hattinga}}\n|source=KB\n}}\n== {{int:license-header}} ==\n{{PD-old}}")
    out = concept.concept(kb_file(text), {"id": "o", "label": "kerk", "beschrijving": {"onderwerp": "kerk", "onderwerp_en": "church"}})["wikitekst"]
    assert out.startswith("=={{int:filedesc}}==\n{{Map\n")
    assert "|map date=1750" in out and "|print date=1752" in out and "|location=Zeeland" in out and "|scale=1:100000" in out
    assert "latitude" not in out and "longitude" not in out and "Wegen" not in out and "Kaart van Zeeland" not in out
    assert "|title={{nl|1=kerk}}{{en|1=church}}" in out and "|author={{Creator:Hattinga}}" in out


def test_partner_template_with_cutout_category_in_source():
    c = concept.concept(kb_file(), {"id": "o", "label": "x"})
    text = c["wikitekst"]
    assert ("|source={{Extracted from|File:Band.jpeg}} {{Koninklijke Bibliotheek|category="
            "[[Category:Cut-outs from media contributed by Koninklijke Bibliotheek]]}}") in text
    # Not twice: the template puts the page in the category, no separate line.
    assert text.count("Cut-outs from media contributed by Koninklijke Bibliotheek") == 1
    assert "[[Category:Bookbindings]]" in text and "[[Category:Uploaded with Commons Cutter]]" in text
    # Unticked by the user: no partner template either (it would add the KB's own category).
    c["categorieen"] = [{**cat, "gekozen": cat["naam"] == "Bookbindings"} for cat in c["categorieen"]]
    assert "Koninklijke Bibliotheek" not in concept.wikitext(kb_file(), c).split("[[Category:Bookbindings]]")[0].split("|gallery=")[0]
    delpher = kb_file(hidden=("Media from Delpher",))
    assert "{{Delpher|category=[[Category:Cut-outs from media from Delpher]]}}" in concept.concept(delpher, {"id": "o", "label": "x"})["wikitekst"]



def test_text_in_and_around_the_cutout_become_inscriptions():
    obj = {"id": "o", "label": "x", "beschrijving": {"onderwerp": "akte", "tekst_in_beeld": "Deze Hoffstede\nis | groot", "tekst_rond_beeld": "Den Inhoud van de Plaats"}}
    text = concept.concept(kb_file(), obj)["wikitekst"]
    assert ("|inscriptions={{Inscription|1=Deze Hoffstede\nis &#124; groot|type=text|linebreaks=1}}"
            "{{Inscription|1=Den Inhoud van de Plaats|type=caption|linebreaks=1|comment=outside the cut-out, on the original}}") in text
    # {{Information}} and {{Book}} have no inscriptions field: an extra row in other fields.
    plain = kb_file("== {{int:license-header}} ==\n{{PD-old}}")
    info = concept.concept(plain, obj)["wikitekst"]
    assert "|other fields={{Information field|name={{int:wm-license-artwork-inscriptions}}|value={{Inscription|1=Deze" in info
    book = kb_file("{{Book\n|Author=X\n|Title=Boek\n|Source=KB\n}}\n== {{int:license-header}} ==\n{{PD-old}}")
    out = concept.concept(book, obj)["wikitekst"]
    assert "={{Information field|name={{int:wm-license-artwork-inscriptions}}" in out and "Other" in out
    # Nothing read: no inscriptions at all.
    assert "Inscription" not in concept.concept(kb_file(), {"id": "o", "label": "x"})["wikitekst"]


def test_statement_values_can_be_changed_but_keep_their_qualifiers():
    c = concept.default_concept({"titel": "File:X.jpg", "categorieen": [], "_wikitekst": ""}, {"id": "o", "label": "x"})
    file = {
        "titel": "File:X.jpg",
        "_sdc": {"collectie": [{"_mainsnak": concept._item_snak("P195", "Q1"), "_qualifiers": {"P217": [{"snaktype": "value", "property": "P217"}]}}]},
    }
    from cutter.sdc import PROPERTIES

    file["_sdc"] = {PROPERTIES["P195"]: file["_sdc"]["collectie"]}
    c["sdc_waarden"] = {"P195": [{"item": "Q2", "bron": 0}, {"item": "Q3"}], "P571": [{"tijd": "1708-02"}], "P170": [{"onbekend": True}]}
    claims = concept.structured_data(file, c)["claims"]
    collection = [cl for cl in claims if cl["mainsnak"]["property"] == "P195"]
    assert [cl["mainsnak"]["datavalue"]["value"]["id"] for cl in collection] == ["Q2", "Q3"]
    assert "P217" in collection[0]["qualifiers"] and "qualifiers" not in collection[1]
    date = next(cl for cl in claims if cl["mainsnak"]["property"] == "P571")["mainsnak"]["datavalue"]["value"]
    assert date["time"] == "+1708-02-00T00:00:00Z" and date["precision"] == 10
    assert next(cl for cl in claims if cl["mainsnak"]["property"] == "P170")["mainsnak"]["snaktype"] == "somevalue"
    # An empty list removes the statement.
    c["sdc_waarden"] = {"P195": []}
    assert not [cl for cl in concept.structured_data(file, c)["claims"] if cl["mainsnak"]["property"] == "P195"]


@pytest.mark.parametrize("body", [
    {"sdc_waarden": {"P31": [{"item": "Q1"}]}},
    {"sdc_waarden": {"P195": [{"item": "X1"}]}},
    {"sdc_waarden": {"P571": [{"tijd": "ergens"}]}},
    {"sdc_waarden": {"P195": [{"item": "Q1", "tijd": "1708"}]}},
])
def test_statement_values_are_checked(body):
    with pytest.raises(ValueError):
        concept.validate_patch(body)


def test_free_text_cannot_inject_wikitext():
    """AI output or typed text with template, link, category, signature or magic-word syntax
    ends up as literal text: no extra parameters, categories or templates."""
    evil = "Mooi}}\n|author=Evil ~~~~ [[Category:Spam]] {{subst:X}} __NOINDEX__ <script>"
    obj = {"id": "o", "label": "x", "beschrijving": {"onderwerp": evil, "onderwerp_en": "x", "beschrijving": evil, "tekst_in_beeld": evil, "tekst_rond_beeld": evil}}
    text = concept.concept(kb_file(), obj)["wikitekst"]
    for bad in ("[[Category:Spam]]", "{{subst:", "~~~~", "__NOINDEX__", "<script>", "|author=Evil", "Mooi}}"):
        assert bad not in text, bad
    assert "Mooi&#125;&#125;" in text and "&#91;&#91;Category:Spam&#93;&#93;" in text
    # Only our own: Bookbindings, the tracking category and the KB cut-out category (via its template).
    assert text.count("[[Category:") == 3


@pytest.mark.parametrize("body", [
    {"datum": None},
    {"maker": ["x"]},
    {"gekozen": "ja"},
    {"caption": {"xx": "a"}},
    {"categorieen": [{"naam": "A]] [[Category:B", "gekozen": True}]},
    {"sdc_waarden": {"P195": [{"item": "Q1", "bron": True}]}},
])
def test_concept_patch_refuses_wrong_types(body):
    with pytest.raises(ValueError):
        concept.validate_patch(body)


def test_art_photo_is_taken_over_as_art_photo():
    text = ("{{Art Photo\n|artist={{Creator:Rembrandt}}\n|title=Nachtwacht\n|location=Zaal 1\n|photo description=De hele zaal\n"
            "|photographer=Jan\n|photo date=2001\n|artwork license={{PD-old}}\n|photo license={{CC-BY-4.0}}\n|source=Rijks\n}}\n"
            "== {{int:license-header}} ==\n{{PD-old}}")
    out = concept.concept(kb_file(text), {"id": "o", "label": "x", "beschrijving": {"onderwerp": "hond", "onderwerp_en": "dog"}})["wikitekst"]
    assert out.startswith("=={{int:filedesc}}==\n{{Art Photo\n")
    for kept in ("|artist={{Creator:Rembrandt}}", "|location=Zaal 1", "|photographer=Jan", "|photo date=2001", "|artwork license={{PD-old}}", "|photo license={{CC-BY-4.0}}"):
        assert kept in out, kept
    assert "De hele zaal" not in out and "Nachtwacht" not in out
    assert "|title={{nl|1=hond}}{{en|1=dog}}" in out
