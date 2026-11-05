"""Wikitext parsing (licence, notes, extracted files) and rights labels (5.3)."""

import pytest

from cutter import rechten, regios, sdc, wikitekst

PAGE = """=={{int:filedesc}}==
{{Artwork
 |artist={{Creator:Jean Le Tavernier}}
 |title={{en|1=All Saints}}
 |date=circa 1450-1460
 |institution={{Institution:Koninklijke Bibliotheek}}
 |accession number=KW 76 F 2
 |source=[https://example.org KB]
 |permission=
}}
{{ImageNote|id=1|x=10|y=20|w=30|h=40|dimx=100|dimy=200|style=2}}
Een '''engel''' met [[harp|een harp]]
{{ImageNoteEnd|id=1}}

== {{int:license-header}} ==
{{PD-art|PD-old-100-expired}}
{{Flickrreview}}

{{Image extracted|Saint A.jpg|2=File:Saint_B.jpg}}
[[Category:Book of Hours of Philip of Burgundy]]
"""


def test_templates_and_parameters():
    calls = wikitekst.templates(PAGE)
    artwork = calls[0]
    assert artwork.name == "artwork"
    assert artwork.params["accession number"] == "KW 76 F 2"
    assert artwork.params["artist"] == "{{Creator:Jean Le Tavernier}}"  # nested template kept whole
    assert {"imagenote", "imagenoteend", "pd-art", "flickrreview", "image extracted"} <= {c.name for c in calls}
    assert "creator:jean le tavernier" in wikitekst.names(PAGE)


def test_license_templates_are_verbatim_without_reviews():
    assert wikitekst.license_templates(PAGE) == ["{{PD-art|PD-old-100-expired}}"]


def test_license_templates_without_a_licence_heading():
    text = "{{Information|description=x}}\n{{self|cc-by-sa-4.0}}\n{{Uncategorized}}"
    assert wikitekst.license_templates(text) == ["{{self|cc-by-sa-4.0}}"]


def test_image_notes():
    notes = wikitekst.image_notes(PAGE)
    assert notes == [{"id": "1", "tekst": "Een engel met een harp", "x": 10, "y": 20, "w": 30, "h": 40, "dimx": 100, "dimy": 200}]


def test_extracted_files():
    assert wikitekst.extracted_files(PAGE) == ["File:Saint A.jpg", "File:Saint B.jpg"]


def test_plain_text():
    assert wikitekst.plain_text("{{nl|1=Een ''wapen''}} <br/>[[Category:X|y]] {{Other}} &amp; meer") == "Een wapen y & meer"
    assert wikitekst.plain_text("a" * 20, limit=5) == "aaaaa…"


def test_note_regions_scale_to_the_page():
    file = {"mid": "M1"}
    page = {"breedte": 1000, "hoogte": 1000}
    [obj] = regios.note_regions(file, page, wikitekst.image_notes(PAGE))
    assert obj["box"] == {"x": 100, "y": 100, "w": 300, "h": 200}
    assert obj["bron"] == "commons" and obj["soort"] == "notitie"
    assert obj["bijschrift"]["tekst"] == "Een engel met een harp"


# -- Rights labels -----------------------------------------------------------------------------


def labels(text, meta=None, parsed=None):
    return rechten.file_labels(text, meta, parsed)


def test_plain_public_domain_is_in_order():
    parsed = {"auteursrechtstatus": [{"waarde": sdc.PUBLIC_DOMAIN}]}
    result = labels("== {{int:license-header}} ==\n{{PD-art|PD-old-70}}", parsed=parsed)
    assert result["labels"] == ["in_orde"] and result["upload_toegestaan"] and result["publiek_domein"]


def test_public_domain_needs_the_sdc_status_too():
    assert not labels("== {{int:license-header}} ==\n{{PD-old-70}}")["publiek_domein"]


def test_cc_by_needs_attribution_and_is_not_public_domain():
    parsed = {"auteursrechtstatus": [{"waarde": sdc.PUBLIC_DOMAIN}]}
    result = labels("== License ==\n{{self|cc-by-sa-4.0}}", {"LicenseShortName": "CC BY-SA 4.0"}, parsed)
    assert result["labels"] == ["naamsvermelding"] and result["naamsvermelding_verplicht"]
    assert not result["publiek_domein"]


@pytest.mark.parametrize(
    "text, label",
    [
        ("{{Delete|reason=copyvio}}\n{{PD-old}}", "ter_discussie"),
        ("{{Copyvio|source}}", "ter_discussie"),
        ("{{No permission since|month=May}}", "ter_discussie"),
        ("{{Flickrreview}}\n{{cc-by-2.0}}", "ter_discussie"),
        ("{{LicenseReview}}", "ter_discussie"),
        ("{{Trademarked}}\n{{PD-textlogo}}", "merk"),
        ("{{Personality rights}}\n{{cc-zero}}", "persoonlijkheidsrechten"),
        ("{{PD-US-only}}", "alleen_vs"),
    ],
)
def test_rights_signals(text, label):
    result = labels(text)
    assert result["label"] == label
    assert result["upload_toegestaan"] == (label != "ter_discussie")
    assert result["redenen"]
    # The same reasons as codes, for the interface in English too (one per reason).
    assert len(result["reden_codes"]) == len(result["redenen"])
    assert all(set(r) == {"code", "detail"} for r in result["reden_codes"])


def test_confirmed_flickr_review_is_fine():
    assert labels("== {{int:license-header}} ==\n{{flickrreview|File Upload Bot|2013-10-03}}\n{{PD-old}}")["upload_toegestaan"]


def test_object_labels():
    file_rights = {"labels": ["persoonlijkheidsrechten", "naamsvermelding"]}
    flower = rechten.object_labels(file_rights, {"label": "flower"})
    assert flower["labels"] == ["naamsvermelding"]
    portrait = rechten.object_labels(file_rights, {"label": "portrait"})
    assert portrait["label"] == "persoonlijkheidsrechten"
    logo = rechten.object_labels({"labels": ["in_orde"]}, {"label": "x", "beschrijving": {"soort": "logo"}})
    assert logo["labels"] == ["merk"]
    assert rechten.default_checked(["naamsvermelding"]) and not rechten.default_checked(["merk"])


# -- Regions (7.5) --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, box",
    [
        ("pct:50,25,10,20", {"x": 500, "y": 250, "w": 100, "h": 200}),
        ("pct:95,0,10,10", {"x": 950, "y": 0, "w": 50, "h": 100}),  # clamped to the image
        ("100,200,300,400", {"x": 100, "y": 200, "w": 300, "h": 400}),  # IIIF pixels
        ("PCT: 0, 0, 100, 100", {"x": 0, "y": 0, "w": 1000, "h": 1000}),
        ("full", None),
        ("pct:120,0,10,10", None),
        ("", None),
    ],
)
def test_parse_region(value, box):
    assert regios.parse_region(value, 1000, 1000) == box


def test_depicts_regions_of_the_book_of_hours(book):
    page = {"breedte": book["breedte"], "hoogte": book["hoogte"]}
    objects = regios.depicts_regions(book, page, book["_labels"])
    assert len(objects) == 13
    catherine = next(o for o in objects if o["wikidata"] == "Q179718")
    # pct:35.5814,68.7074,21.0853,24.2104 on 804 x 890 pixels
    assert catherine["box"] == {"x": 286, "y": 611, "w": 170, "h": 216}
    assert catherine["label_en"] == "Catherine of Alexandria"
    assert catherine["herkomst"]["p2677"].startswith("pct:35.58")
    assert catherine["herkomst"]["mid"] == "M83565772"
    assert len({o["id"] for o in objects}) == 13


def test_odd_commons_data_is_skipped_not_a_crash():
    from cutter import regios, wikitekst

    assert regios.parse_region("pct:1.2.3,5,10,10", 100, 100) is None
    assert regios.parse_region("nan,0,10,10", 100, 100) is None
    text = "{{ImageNote|id=1|x=1|y=1|w=5|h=5|dimx=nan|dimy=100}}Noot{{ImageNoteEnd|id=1}}"
    assert wikitekst.image_notes(text) == []
