from conftest import ALBUM_MID

from cutter.concept import sdc_entity_ids
from cutter.weergave import clean_html

PAGE = f"/api/v1/bestand/{ALBUM_MID}/pagina/1"


def test_clean_html_keeps_text_and_tables_and_drops_the_rest():
    html = clean_html(
        '<div class="mw-parser-output"><style>.a{}</style><table><tr><td colspan="2" onclick="x()">Cel</td></tr></table>'
        '<img src="//upload.wikimedia.org/a.png" alt="A"><a href="/wiki/Category:X">X</a><a href="javascript:alert(1)">Y</a>'
        '<script>alert(1)</script><span style="color:red">rood</span><span style="background:url(http://x)">bg</span></div>'
    )
    assert '<td colspan="2">Cel</td>' in html
    assert '<a href="https://commons.wikimedia.org/wiki/Category:X" target="_blank" rel="noopener">X</a>' in html
    assert "<img" not in html and "<style" not in html and "<script" not in html and "alert" not in html
    assert "onclick" not in html and "javascript:" not in html and "url(" not in html
    assert '<span style="color:red">rood</span>' in html and "<span>bg</span>" in html
    assert html.endswith("</div>")


def test_clean_html_turns_wikidata_images_into_icons():
    html = clean_html(
        '<a href="https://www.wikidata.org/wiki/Q1526131" title="wikidata:Q1526131"><img src="//upload.wikimedia.org/w.svg" alt="wikidata:Q1526131"></a>'
        '<a href="https://www.wikidata.org/wiki/Q1#P571" title="Edit this at Wikidata"><img src="//upload.wikimedia.org/p.svg"></a>'
        '<a href="/wiki/File:Logo.svg"><img src="//upload.wikimedia.org/l.svg"></a>'
    )
    assert 'title="wikidata:Q1526131" target="_blank" rel="noopener"><span class="cc-ikoon cc-ikoon-wikidata" title="Wikidata"></span></a>' in html
    assert "cc-ikoon-bewerken" in html
    assert html.count('<span class="cc-ikoon') == 2 and "<img" not in html


def test_sdc_entity_ids_from_claims_and_qualifiers():
    data = {
        "claims": [
            {"mainsnak": {"property": "P180", "datavalue": {"value": {"id": "Q1420"}}}},
            {
                "mainsnak": {"property": "P6216", "datavalue": {"value": {"id": "Q19652"}}},
                "qualifiers": {"P1001": [{"property": "P1001", "datavalue": {"value": {"id": "Q30"}}}]},
            },
            {"mainsnak": {"property": "P571", "datavalue": {"value": {"time": "+1920-00-00T00:00:00Z"}}}},
        ]
    }
    assert sdc_entity_ids(data) == ["P180", "Q1420", "P6216", "Q19652", "P1001", "Q30", "P571"]


def test_rendered_wikitext_and_sdc_labels(http):
    obj = http.post(PAGE + "/detecties", json={"prompt": "wapen"}).get_json()["objecten"][0]
    url = f"{PAGE}/object/{obj['id']}/commons"
    concept = http.get(url).get_json()
    assert "sdc_labels" in concept
    rendered = http.get(url + "/weergave").get_json()["html"]
    assert 'class="fileinfotpl"' in rendered
    assert "<img" not in rendered and "<script" not in rendered
