"""Description with Muse Spark (6.2, 6.3) on constructed answers; no live calls."""

import json
from pathlib import Path

import pytest

from cutter import beschrijving
from cutter.beschrijving import DescriptionService, DummyVision, MetaVision, choose_model, parse_answer
from cutter.detectie.basis import DetectionError
from cutter.detectie.dienst import DetectionService
from cutter.detectie.dummy import DummyDetector
from cutter.verbruik import Verbruik

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "muse" / "beschrijving_wapen.json").read_text(encoding="utf-8"))

CONFIG = {
    "BEELDMODEL": "muse-spark-1.3",
    "BEELDMODEL_RECHTENVRIJ": "muse-spark-1.3-contributor",
    "BEELDMODEL_CONTRIBUTOR": True,
    "BEELDMODEL_REDENEREN": "low",
}


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


def test_parse_answer_with_suggestions():
    answer = parse_answer(beschrijving.output_text(FIXTURE))
    assert answer["soort"] == "wapen"
    assert answer["onderwerp_en"] == "Coat of arms of Jacob van Bronckhorst van Batenburg"
    assert answer["beschrijving_en"].startswith("A crowned shield")
    # Q-ids are dropped, duplicates removed, at most three.
    assert answer["wikidata_suggesties"] == ["coat of arms", "Jacob van Bronckhorst van Batenburg", "heraldry"]


def test_parse_answer_unreadable():
    answer = parse_answer("Ik zie een wapen.")
    assert answer["soort"] == "anders" and answer["zekerheid"] == "laag"
    assert answer["beschrijving"] == "Ik zie een wapen." and answer["wikidata_suggesties"] == []


def file_with(labels, public_domain):
    return {"rechten": {"labels": labels, "publiek_domein": public_domain}}


def test_hint_goes_into_the_prompt_and_the_cache_key():
    from cutter.beschrijving import build_prompt, clean_hint

    file = {"titel": "File:X.jpg", "naam": "X"}
    assert "Instruction from the user" not in build_prompt(file)
    prompt = build_prompt(file, None, "  alleen de\n jongen ")
    assert prompt.endswith("Instruction from the user for this question (follow it; it overrides the context above where they differ): alleen de jongen")
    assert len(clean_hint("x" * 500)) == 300


def test_margin_is_clamped_and_changes_the_crop():
    from PIL import Image

    from cutter.beschrijving import clean_margin, model_input

    assert clean_margin(None) == 0.25 and clean_margin("x") == 0.25
    assert clean_margin(-1) == 0 and clean_margin(3) == 1 and clean_margin(0.33) == 0.35
    page = Image.new("RGB", (1000, 1000), "white")
    box = {"x": 400, "y": 400, "w": 100, "h": 100}
    assert model_input(page, 1000, box, 0)[1] == (100, 100)
    assert model_input(page, 1000, box, 0.5)[1] == (200, 200)
    data, _ = model_input(page, 1000, box, 0.5, outline=True)
    framed = Image.open(__import__("io").BytesIO(data)).convert("RGB")
    assert framed.getpixel((51, 100))[0] > 180 and framed.getpixel((51, 100))[1] < 120  # the red outline


def test_choose_model():
    assert choose_model(file_with(["in_orde"], True), CONFIG)["model"] == "muse-spark-1.3-contributor"
    assert choose_model(file_with(["naamsvermelding"], False), CONFIG)["model"] == "muse-spark-1.3"
    blocked = choose_model(file_with(["persoonlijkheidsrechten"], True), CONFIG)
    assert blocked["model"] == "muse-spark-1.3" and "persoonlijkheidsrechten" in blocked["reden"]
    off = choose_model(file_with(["in_orde"], True), {**CONFIG, "BEELDMODEL_CONTRIBUTOR": False})
    assert off["model"] == "muse-spark-1.3" and "staat uit" in off["reden"]
    # A code the interface translates, with the blocking labels.
    assert choose_model(file_with(["in_orde"], True), CONFIG)["reden_code"] == "publiek_domein"
    assert (blocked["reden_code"], blocked["labels"]) == ("rechtenlabel", ["persoonlijkheidsrechten"])
    assert off["reden_code"] == "contributor_uit"
    assert choose_model(file_with(["naamsvermelding"], False), CONFIG)["reden_code"] == "niet_vrij"


def test_prompt_has_commons_context(book):
    prompt = beschrijving.build_prompt(book)
    assert "Book of Hours of Philip of Burgundy" in prompt
    assert "Catherine of Alexandria" in prompt  # existing depicts
    assert "never Q-ids" in prompt


def test_meta_vision_request():
    session = FakeSession(FakeResponse(200, FIXTURE))
    vision = MetaVision("test-key", session=session)
    body = vision.describe("muse-spark-1.3", "vraag", "data:image/jpeg;base64,xx", {}, effort="low")
    sent = session.calls[0]
    assert sent["url"].endswith("/responses") and sent["headers"]["Authorization"] == "Bearer test-key"
    assert sent["json"]["reasoning"] == {"effort": "low"}
    assert sent["json"]["text"]["format"]["schema"]["properties"]["wikidata_suggesties"]["maxItems"] == 3
    assert body is FIXTURE


@pytest.mark.parametrize("status, code", [(429, 429), (401, 503), (404, 503), (400, 400)])
def test_meta_vision_errors(status, code):
    vision = MetaVision("k", session=FakeSession(FakeResponse(status, {"error": {"message": "nee"}})))
    with pytest.raises(DetectionError) as exc:
        vision.describe("m", "p", "d", {})
    assert exc.value.status == code


def test_meta_vision_without_key():
    with pytest.raises(DetectionError) as exc:
        MetaVision(None).describe("m", "p", "d", {})
    assert exc.value.code == "no_api_key"


class FixtureVision:
    betaald = True

    def __init__(self):
        self.calls = 0

    def describe(self, model, prompt, data_url, obj, effort=None, schema=beschrijving.SCHEMA):
        self.calls += 1
        return FIXTURE


@pytest.fixture
def objects(client, tmp_path):
    return DetectionService(DummyDetector(), client, tmp_path / "cache", tmp_path / "uitvoer", Verbruik(tmp_path / "verbruik", 500))


def test_describe_is_stored_cached_and_logged(objects, book, tmp_path):
    region = objects.detect(book, 1, modus="commons")["objecten"][0]
    vision = FixtureVision()
    service = DescriptionService(vision, objects, CONFIG, tmp_path / "cache")
    plan = service.plan(book, 1, region["id"])
    assert plan["betaald"] and plan["kosten_schatting_usd"] > 0
    result = service.describe(book, 1, region["id"], user="OlafJanssen")
    assert result["object"]["beschrijving"]["soort"] == "wapen"
    assert result["object"]["beschrijving"]["tokens"]["invoer"] == 1400
    assert not result["uit_cache"]
    again = service.describe(book, 1, region["id"])
    assert again["uit_cache"] and vision.calls == 1
    [entry] = objects.verbruik.entries()
    assert entry["soort"] == "beschrijving" and entry["bestand"] == book["mid"] and entry["gebruiker"] == "OlafJanssen"
    service.remove(book, 1, region["id"])
    assert "beschrijving" not in objects._find(book, 1, region["id"])


def test_contributor_refused_when_not_allowed(objects, client, tmp_path):
    pdf = client.load_file("File:Heritage Album Paperwork - Polk Co SO - COMPLETE.pdf")
    obj = objects.rectangle(pdf, 1, {"x": 0, "y": 0, "w": 100, "h": 100})["object"]
    service = DescriptionService(DummyVision(), objects, CONFIG, tmp_path / "cache")
    with pytest.raises(DetectionError) as exc:
        service.describe(pdf, 1, obj["id"], model="contributor")
    assert exc.value.status == 409


def test_dummy_description_and_inventory(objects, album, tmp_path):
    obj = objects.detect(album, 1, "wapen")["objecten"][0]
    service = DescriptionService(DummyVision(), objects, CONFIG, tmp_path / "cache")
    described = service.describe(album, 1, obj["id"])["object"]["beschrijving"]
    assert described["onderwerp_en"] == "Coat of arms" and described["kosten_usd"] == 0.0
    overview = service.inventory(album, 1)["inventaris"]
    assert overview["zoektermen"][0] == {"en": "coat of arms", "nl": "wapen", "aantal": 2, "waar": "bovenaan"}
    assert service.inventory_plan(album, 1)["inventaris"]["paginasoort"]
    assert service.inventory_plan(album, 1)["inventaris"]["samenvatting_en"]
    assert service.inventory_plan(album, 1)["inventaris"]["tekst"]
    assert objects.verbruik.entries() == []  # dummy is free


def test_caption_goes_into_the_question_and_the_cache_key(objects, album, tmp_path):
    obj = objects.rectangle(album, 1, {"x": 0, "y": 0, "w": 300, "h": 300})["object"]
    prompts = []

    class Recording(FixtureVision):
        def describe(self, model, prompt, data_url, o, effort=None, schema=beschrijving.SCHEMA):
            prompts.append(prompt)
            return super().describe(model, prompt, data_url, o, effort, schema)

    service = DescriptionService(Recording(), objects, CONFIG, tmp_path / "cache")
    service.describe(album, 1, obj["id"])
    assert prompts[-1].endswith("Caption of this cut-out (given by the user or a file note on Commons): none")
    objects.set_caption(album, 1, obj["id"], {"tekst": "Wapen van Bronckhorst"})
    again = service.describe(album, 1, obj["id"])
    assert not again["uit_cache"]  # another caption: a new question
    assert '"Wapen van Bronckhorst"' in prompts[-1]


def test_page_text_goes_into_the_question_and_the_cache_key(objects, album, tmp_path):
    obj = objects.rectangle(album, 1, {"x": 0, "y": 0, "w": 300, "h": 300})["object"]
    prompts = []

    class Recording(FixtureVision):
        def describe(self, model, prompt, data_url, o, effort=None, schema=beschrijving.SCHEMA):
            prompts.append(prompt)
            if schema is beschrijving.INVENTORY_SCHEMA:
                return DummyVision().describe(model, prompt, data_url, o, effort, schema)
            return super().describe(model, prompt, data_url, o, effort, schema)

    service = DescriptionService(Recording(), objects, CONFIG, tmp_path / "cache")
    first = service.describe(album, 1, obj["id"])["object"]["beschrijving"]
    assert "Text read earlier" not in prompts[-1] and not first["paginatekst"]
    service.inventory(album, 1)  # the dummy overview reads a text under the image
    again = service.describe(album, 1, obj["id"])
    assert not again["uit_cache"]  # with the page text: a new question
    assert "Voorbeeldtekst onder de afbeelding (dummy)." in prompts[-1]
    assert again["object"]["beschrijving"]["paginatekst"]
    assert len(service.history(album, 1, obj["id"])) >= 1  # the first answer is kept


def test_concept_api_includes_the_caption(http):
    page = "/api/v1/bestand/M28830642/pagina/1"
    obj = http.post(page + "/detecties", json={"rechthoek": {"x": 0, "y": 0, "w": 100, "h": 100}}).get_json()["object"]
    http.patch(f"{page}/object/{obj['id']}", json={"bijschrift": {"tekst": "Spes mea Deus"}})
    assert http.get(f"{page}/object/{obj['id']}/commons").get_json()["bijschrift"] == "Spes mea Deus"


def test_inventory_keeps_text_lines():
    from cutter.beschrijving import parse_inventory

    answer = r'{"paginasoort": "prent", "samenvatting": "x", "tekst": "Gaarne  helpen zij\n\nAlles gaat de auto in.", "zoektermen": []}'
    assert parse_inventory(answer)["tekst"] == "Gaarne helpen zij\nAlles gaat de auto in."
    assert parse_inventory("geen json")["tekst"] == ""


def test_hand_edits_are_versions_in_the_history(objects, album, tmp_path):
    """Earlier descriptions as version history: every hand edit keeps the version before it."""
    obj = objects.rectangle(album, 1, {"x": 0, "y": 0, "w": 300, "h": 300})["object"]
    service = DescriptionService(DummyVision(), objects, CONFIG, tmp_path / "cache")
    ai = service.describe(album, 1, obj["id"])["object"]["beschrijving"]
    service.edit(album, 1, obj["id"], {"tekst_in_beeld": "Eerste lezing"})
    service.edit(album, 1, obj["id"], {"tekst_in_beeld": "Tweede lezing"})
    service.edit(album, 1, obj["id"], {"tekst_in_beeld": "Tweede lezing"})  # unchanged: no new version
    history = service.history(album, 1, obj["id"])
    texts = [h.get("tekst_in_beeld") for h in history]
    assert "Eerste lezing" in texts and ai.get("tekst_in_beeld") in texts and "Tweede lezing" not in texts
    assert len({h["versie"] for h in history}) == len(history)  # every version has its own id
    hand = next(h for h in history if h.get("tekst_in_beeld") == "Eerste lezing")
    assert hand["bewerkt_op"] and hand["versie"] == hand["bewerkt_op"]
    restored = service.restore(album, 1, obj["id"], version=hand["versie"])
    assert restored["beschrijving"]["tekst_in_beeld"] == "Eerste lezing"
    assert "Tweede lezing" in [h.get("tekst_in_beeld") for h in service.history(album, 1, obj["id"])]


def test_an_earlier_version_can_be_deleted(objects, album, tmp_path):
    obj = objects.rectangle(album, 1, {"x": 0, "y": 0, "w": 300, "h": 300})["object"]
    service = DescriptionService(DummyVision(), objects, CONFIG, tmp_path / "cache")
    service.describe(album, 1, obj["id"])
    service.edit(album, 1, obj["id"], {"tekst_in_beeld": "Mijn lezing"})
    history = service.history(album, 1, obj["id"])
    ai = history[0]  # the AI answer before the edit (also still in the cache)
    left = service.forget_version(album, 1, obj["id"], ai["versie"])
    assert ai["versie"] not in [h["versie"] for h in left]
    assert ai["versie"] not in [h["versie"] for h in service.history(album, 1, obj["id"])]  # not back from the cache
    assert objects._find(album, 1, obj["id"])["beschrijving"]["tekst_in_beeld"] == "Mijn lezing"  # the current one stays
    with pytest.raises(DetectionError):
        service.forget_version(album, 1, obj["id"], "nooit")
