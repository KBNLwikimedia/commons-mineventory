"""Commons adapter (functional design 5.1-5.4) on recorded responses."""

import pytest
from conftest import ALBUM, ALBUM_MID, BOOK_OF_HOURS_MID, PDF_MID, FixtureFetcher

from cutter.commons import CommonsClient, CommonsError, parse_input, public, snap_width


@pytest.mark.parametrize(
    "text, expected",
    [
        ("https://commons.wikimedia.org/wiki/File:Album_amicorum_van_Jacob.jpg", {"titel": "File:Album amicorum van Jacob.jpg"}),
        ("https://commons.wikimedia.org/wiki/File:A_b.jpg?uselang=nl#/media/File:A_b.jpg", {"titel": "File:A b.jpg"}),
        ("https://commons.wikimedia.org/wiki/Bestand:A_b.jpg", {"titel": "File:A b.jpg"}),
        ("https://commons.wikimedia.org/w/index.php?title=File:A_b.jpg&oldid=1", {"titel": "File:A b.jpg"}),
        ("https://commons.m.wikimedia.org/wiki/File:A%20%28b%29.jpg", {"titel": "File:A (b).jpg"}),
        ("https://commons.wikimedia.org/w/index.php?curid=28830642", {"pageid": 28830642}),
        ("https://upload.wikimedia.org/wikipedia/commons/6/67/Album_amicorum_%288077131573%29.jpg", {"titel": "File:Album amicorum (8077131573).jpg"}),
        (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Album_amicorum.jpg/800px-Album_amicorum.jpg",
            {"titel": "File:Album amicorum.jpg"},
        ),
        (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Doc.pdf/page2-250px-Doc.pdf.jpg",
            {"titel": "File:Doc.pdf"},
        ),
        ("File:Album amicorum.jpg", {"titel": "File:Album amicorum.jpg"}),
        ("Album_amicorum.jpg", {"titel": "File:Album amicorum.jpg"}),
        ("bestand:album amicorum.jpg", {"titel": "File:Album amicorum.jpg"}),
        ("M28830642", {"pageid": 28830642}),
        ("m28830642", {"pageid": 28830642}),
        ("28830642", {"pageid": 28830642}),
        ("curid=28830642", {"pageid": 28830642}),
    ],
)
def test_parse_input(text, expected):
    result = parse_input(text)
    assert {k: v for k, v in result.items() if v is not None and k != "andere_wiki"} == expected


def test_parse_input_file_page_on_another_wiki_is_looked_up_on_commons():
    result = parse_input("https://nl.wikipedia.org/wiki/Bestand:Voorbeeld.jpg")
    assert result == {"titel": "File:Voorbeeld.jpg", "andere_wiki": "nl.wikipedia.org"}


@pytest.mark.parametrize(
    "text, code",
    [
        ("", "empty_input"),
        ("   ", "empty_input"),
        ("https://upload.wikimedia.org/wikipedia/nl/a/ab/Lokaal.jpg", "not_commons"),
        ("https://example.org/wiki/File:A.jpg", "not_commons"),
    ],
)
def test_parse_input_errors(text, code):
    with pytest.raises(CommonsError) as exc:
        parse_input(text)
    assert exc.value.code == code


def test_snap_width_uses_commons_steps():
    assert snap_width(1000) == 1280  # Commons served 1280 for 1000 (recorded 3-11-2026)
    assert snap_width(1920) == 1920
    assert snap_width(2000) == 3840
    assert snap_width(2000, maximum=1500) == 1500
    assert snap_width(9999) == 3840


def test_load_file_album(album):
    assert album["mid"] == ALBUM_MID
    assert album["titel"] == ALBUM
    assert (album["breedte"], album["hoogte"], album["mime"], album["paginas"]) == (2000, 1429, "image/jpeg", 1)
    assert album["sha1"] and album["origineel_url"].startswith("https://upload.wikimedia.org/")
    assert album["url"].startswith("https://commons.wikimedia.org/wiki/File:Album_amicorum")
    assert album["ondersteund"] and album["uitsnijden_mogelijk"]
    assert "{{PD-art|PD-old-70-1923}}" in album["licentie"]["sjablonen"]
    assert not any("flickrreview" in t.lower() for t in album["licentie"]["sjablonen"])  # never copied
    assert "Album Amicorum" in album["categorieen"]
    assert "PD-old-70-expired" in album["verborgen_categorieen"]
    assert album["datum"].startswith("2010-11-26")
    assert "Koninklijke Bibliotheek" in album["maker"]
    assert album["rechten"]["label"] == "in_orde" and album["rechten"]["upload_toegestaan"]


def test_public_file_hides_raw_material(album):
    shown = public(album)
    assert not any(key.startswith("_") for key in shown)
    assert "_wikitekst" in album


def test_load_file_book_of_hours_regions_and_labels(book):
    assert book["mid"] == BOOK_OF_HOURS_MID
    assert book["regio_aantal"] == 13
    depicts = book["sdc"]["beeldt_af"]
    catherine = next(d for d in depicts if d["waarde"] == "Q179718")
    assert catherine["positie"] == "pct:35.5814,68.7074,21.0853,24.2104"
    assert catherine["label_en"] == "Catherine of Alexandria"


def test_load_file_pdf_has_pages(client):
    pdf = client.load_file("File:Heritage Album Paperwork - Polk Co SO - COMPLETE.pdf")
    assert pdf["mid"] == PDF_MID
    assert pdf["mime"] == "application/pdf" and pdf["paginas"] == 2
    page = client.load_page(pdf, 2)
    assert (page["breedte"], page["hoogte"]) == (1275, 1650)
    assert page["id"].endswith("|2")
    assert "naamsvermelding" in pdf["rechten"]["labels"]


def test_page_out_of_range(album, client):
    with pytest.raises(CommonsError) as exc:
        client.load_page(album, 2)
    assert exc.value.status == 404


def test_page_image_asks_the_nearest_step(album, client, fetcher):
    data = client.page_image(album, 1, 200)
    assert data[:2] == b"\xff\xd8"
    assert any("iiurlwidth=250" in url for url in fetcher.calls)


def test_original_is_fetched_once_and_kept(album, client, fetcher, tmp_path):
    image = client.original_image(album, 1)
    assert image.width > 0
    calls = len(fetcher.calls)
    client.original_image(album, 1)
    assert len(fetcher.calls) == calls  # from cache/originelen
    assert list((tmp_path / "cache" / "originelen").rglob(album["sha1"]))


def test_every_request_carries_maxlag(fetcher, album):
    assert all("maxlag=5" in url for url in fetcher.calls if "api.php" in url)


def _query_with(page):
    return {"batchcomplete": True, "query": {"pages": [page]}}


def test_missing_file_is_reported_with_an_example(tmp_path):
    client = CommonsClient(FixtureFetcher(), cache_dir=tmp_path)
    url = client.api_url(
        {
            "prop": "info|imageinfo|revisions|categories", "redirects": "1",
            "iiprop": "url|size|mime|sha1|extmetadata|bitdepth",
        }
    )
    missing = {"ns": 6, "title": "File:Bestaat niet.jpg", "missing": True}
    client.fetcher.extra = {client.api_url(_file_params("File:Bestaat niet.jpg")): _query_with(missing)}
    with pytest.raises(CommonsError) as exc:
        client.load_file("File:Bestaat niet.jpg")
    assert exc.value.status == 404 and "Example.jpg" in exc.value.message
    assert url  # the helper builds stable URLs


def _file_params(title):
    return {
        "prop": "info|imageinfo|revisions|categories",
        "redirects": "1",
        "iiprop": "url|size|mime|sha1|extmetadata|bitdepth",
        "iiextmetadatafilter": "LicenseShortName|License|LicenseUrl|UsageTerms|Artist|Credit|ImageDescription|DateTimeOriginal|"
        "Attribution|AttributionRequired|Restrictions|Copyrighted|ObjectName",
        "iiextmetadatalanguage": "en",
        "rvprop": "content|ids",
        "rvslots": "main",
        "clprop": "hidden",
        "cllimit": "max",
        "titles": title,
    }


def _svg_page():
    return {
        "pageid": 1, "ns": 6, "title": "File:Logo.svg",
        "imageinfo": [{"url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Logo.svg", "width": 100, "height": 100, "mime": "image/svg+xml", "sha1": "abc", "extmetadata": {}}],
        "revisions": [{"revid": 1, "slots": {"main": {"content": "{{Information}}\n== {{int:license-header}} ==\n{{PD-textlogo}}\n{{Trademarked}}"}}}],
    }


def test_svg_is_not_supported_and_redirects_are_reported(tmp_path):
    client = CommonsClient(FixtureFetcher(), cache_dir=tmp_path)
    data = _query_with(_svg_page())
    data["query"]["redirects"] = [{"from": "File:Old logo.svg", "to": "File:Logo.svg"}]
    client.fetcher.extra = {
        client.api_url(_file_params("File:Old logo.svg")): data,
        client.api_url({"action": "wbgetentities", "ids": "M1"}): {"entities": {"M1": {"id": "M1", "missing": ""}}},
    }
    file = client.load_file("File:Old logo.svg")
    assert file["doorverwezen_van"] == "File:Old logo.svg"
    assert not file["ondersteund"] and "SVG" in file["niet_ondersteund"]
    assert file["niet_ondersteund_code"] == "svg"  # translated in the interface
    assert "merk" in file["rechten"]["labels"]
    with pytest.raises(CommonsError) as exc:
        client.original_image(file, 1)
    assert exc.value.status == 413


def test_titles_exist_and_sha1(client, album):
    result = client.titles_exist(["Category:Alba amicorum", "Category:Does not exist 123456", "File:" + album["naam"]])
    assert result["File:" + album["naam"]] is True
    assert result["Category:Does not exist 123456"] is False
    assert client.files_with_sha1(album["sha1"]) == [album["titel"]]


def test_item_info_labels_and_descriptions(tmp_path):
    client = CommonsClient(FixtureFetcher(), cache_dir=tmp_path)
    url = client.api_url(
        {"action": "wbgetentities", "ids": "Q104526|Q1420", "props": "labels|descriptions", "languages": "nl|en"},
        api=client.wikidata_api,
    )
    client.fetcher.extra = {
        url: {
            "entities": {
                "Q104526": {"labels": {"en": {"value": "pipe"}}, "descriptions": {"en": {"value": "device for smoking"}}},
                "Q1420": {"labels": {"nl": {"value": "auto"}}, "descriptions": {}},
            }
        }
    }
    info = client.item_info(["Q104526", "Q1420", "Q104526", "x"])
    assert info["Q104526"]["beschrijving"] == {"nl": None, "en": "device for smoking"}
    assert info["Q1420"]["beschrijving"] == {"nl": None, "en": None} and info["Q1420"]["label"]["nl"] == "auto"
    assert client.item_info(["Q999"]) == {}  # not reachable: left out, no error
