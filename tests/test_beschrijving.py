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


def test_the_page_overview_can_be_removed(objects, album, tmp_path):
    service = DescriptionService(DummyVision(), objects, CONFIG, tmp_path / "cache")
    service.inventory(album, 1)
    assert service.forget_inventory(album, 1) == {"verwijderd": True, "inventaris": None}
    assert service.inventory_plan(album, 1)["inventaris"] is None
    assert service.forget_inventory(album, 1) == {"verwijderd": False, "inventaris": None}
    # Asking again without "opnieuw" brings the cached answer back, free.
    again = service.inventory(album, 1)
    assert again["uit_cache"] and again["inventaris"]["zoektermen"]


def test_one_part_of_the_overview_is_asked_again_or_removed_on_its_own(objects, album, tmp_path):
    prompts = []

    class Recording(DummyVision):
        def describe(self, model, prompt, data_url, obj, effort=None, schema=beschrijving.SCHEMA):
            prompts.append((prompt, sorted(schema["properties"])))
            return super().describe(model, prompt, data_url, obj, effort, schema)

    service = DescriptionService(Recording(), objects, CONFIG, tmp_path / "cache")
    first = service.inventory(album, 1)["inventaris"]
    # Only the search terms anew: one call that asks only for terms; the description stays.
    service.forget_inventory(album, 1, "zoektermen")
    kept = service.inventory_plan(album, 1)["inventaris"]
    assert kept["zoektermen"] == [] and kept["samenvatting"] == first["samenvatting"]
    again = service.inventory(album, 1, part="zoektermen")["inventaris"]
    assert prompts[-1][1] == ["zoektermen"] and "samenvatting" not in prompts[-1][0]
    assert again["zoektermen"] == first["zoektermen"] and again["samenvatting"] == first["samenvatting"]
    assert again["delen"]["zoektermen"]["tijdstempel"]
    # Only the description anew: the terms stay.
    again = service.inventory(album, 1, part="beschrijving")["inventaris"]
    assert prompts[-1][1] == sorted(["paginasoort", "paginasoort_en", *beschrijving.SUMMARY_FIELDS, "tekst"])
    assert "zoektermen" not in prompts[-1][0] and again["zoektermen"] == first["zoektermen"]
    # A part is always asked anew (no cache), and removing both parts removes the overview.
    calls = len(prompts)
    service.inventory(album, 1, part="beschrijving")
    assert len(prompts) == calls + 1
    service.forget_inventory(album, 1, "beschrijving")
    assert service.forget_inventory(album, 1, "zoektermen") == {"verwijderd": True, "inventaris": None}
    with pytest.raises(DetectionError):
        service.inventory(album, 1, part="alles")


def test_the_description_of_the_image_keeps_its_versions(objects, album, tmp_path):
    service = DescriptionService(DummyVision(), objects, CONFIG, tmp_path / "cache")
    first = service.inventory(album, 1)["inventaris"]
    service.edit_inventory(album, 1, {"tekst": "Andere tekst."})
    assert service.edit_inventory(album, 1, {"tekst": "Andere tekst."})["inventaris"]["tekst"] == "Andere tekst."  # no change: no version
    assert len(service.inventory_history(album, 1)) == 1
    # A new description (part asked anew) keeps the edited one; its edits do not carry over.
    new = service.inventory(album, 1, part="beschrijving")["inventaris"]
    assert not new.get("bewerkt") and not new.get("ai_origineel")
    versions = service.inventory_history(album, 1)
    assert [v["tekst"] for v in versions][:2] == ["Andere tekst.", first["tekst"]]
    # Removing the description keeps it in the history as well.
    service.forget_inventory(album, 1, "beschrijving")
    assert len(service.inventory_history(album, 1)) == 3
    restored = service.restore_inventory(album, 1, versions[0]["versie"])["inventaris"]
    assert restored["tekst"] == "Andere tekst." and restored["bewerkt"]


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
            if "zoektermen" in schema.get("properties", {}):
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
    http.patch(f"{page}/objecten/{obj['id']}", json={"bijschrift": {"tekst": "Spes mea Deus"}})
    assert http.get(f"{page}/objecten/{obj['id']}/commons").get_json()["bijschrift"] == "Spes mea Deus"


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


def test_detail_levels_change_the_question_and_the_cap():
    from cutter.beschrijving import DETAIL_LEVELS, inventory_instructions, parse_inventory

    normal = inventory_instructions('"x"')
    assert "at most 12 distinct kinds of visual objects, most frequent or most striking first." in normal  # as before the slider
    assert "only the one main subject" in inventory_instructions('"x"', detail="hoofdonderwerp")
    assert "small details" in inventory_instructions('"x"', part="zoektermen", detail="details")
    terms = [{"en": f"thing {i}", "nl": f"ding {i}", "aantal": 1, "waar": ""} for i in range(25)]
    answer = '{"zoektermen": ' + __import__("json").dumps(terms) + "}"
    assert len(parse_inventory(answer, DETAIL_LEVELS["hoofdonderwerp"][0])["zoektermen"]) == 1
    assert len(parse_inventory(answer, DETAIL_LEVELS["details"][0])["zoektermen"]) == 20



def test_group_is_described_by_its_members_only():
    from cutter.beschrijving import build_prompt, group_members

    group = {"bron": "groep", "groep": {"leden": [
        {"label": "lemon"},
        {"label": "bunch of grapes"},
        {"label": "bunch of grapes", "beschrijving": {"onderwerp_en": "bunch of grapes"}},
    ]}}
    members = group_members(group)
    assert members == "lemon (1), bunch of grapes (2)"
    assert group_members({"label": "cat"}) == ""
    prompt = build_prompt({"naam": "x"}, None, None, None, members)
    assert "Describe only these objects" in prompt and "lemon (1)" in prompt



def test_group_prompt_carries_the_members_earlier_descriptions():
    from cutter.beschrijving import build_prompt, group_context, group_members

    group = {"bron": "groep", "groep": {"leden": [
        {"label": "boy", "beschrijving": {"onderwerp_en": "Boy in white sailor suit with box", "beschrijving_en": "A boy with short red hair in a white sailor suit.", "tekst_rond_beeld": "Buiten"}},
        {"label": "cardboard box"},
    ]}}
    context = group_context(group)
    assert context == '- Boy in white sailor suit with box: A boy with short red hair in a white sailor suit. Text around it: "Buiten".'
    prompt = build_prompt({"naam": "x"}, None, None, None, group_members(group), context)
    assert "Earlier AI descriptions of these objects" in prompt and "they may be wrong" in prompt and context in prompt
    assert group_context({"groep": {"leden": [{"label": "box"}]}}) == ""



def test_group_instruction_follows_the_space_around_it():
    from cutter.beschrijving import build_prompt

    tight = build_prompt({"naam": "x"}, None, None, None, "lemon (1), bunch of grapes (1)", None, False)
    wide = build_prompt({"naam": "x"}, None, None, None, "lemon (1), bunch of grapes (1)", None, True)
    assert "ignore everything else" in tight and "use those only as context" not in tight
    assert "use those only as context" in wide and "ignore everything else" not in wide



def test_description_levels_change_the_question():
    from cutter.beschrijving import inventory_instructions

    # All four lengths in one question (wish Olaf, 11-11-2026), for the whole overview and the part.
    for question in (inventory_instructions('"x"'), inventory_instructions('"x"', part="beschrijving")):
        assert "- samenvatting_normaal: one sentence in Dutch about what is visible." in question
        assert "- samenvatting_uitgebreid: a paragraph of three to five sentences" in question
        assert "- samenvatting_kort: a few words" in question and "- samenvatting_caption_en:" in question
        assert "write each one on its own" in question



def test_caption_level_never_longer_than_250():
    from cutter.beschrijving import CAPTION_MAX, cap_caption, inventory_instructions

    assert "at most 230 characters" in inventory_instructions('"x"', part="beschrijving")
    long = "Een gedekte tafel met fruit. " * 20
    capped = cap_caption(long)
    assert len(capped) <= CAPTION_MAX and capped.endswith(".")
    words = "woord " * 80
    capped = cap_caption(words)
    assert len(capped) <= CAPTION_MAX and capped.endswith("…")
    assert cap_caption("Kort.") == "Kort."


def test_commons_context_lists_captions_and_depicts():
    from cutter.beschrijving import commons_context

    file = {"sdc": {
        "captions": {"nl": "De Pieterskerk  in Leiden", "en": ""},
        "beeldt_af": [
            {"soort": "item", "waarde": "Q144", "label": "hond", "label_en": "dog"},
            {"soort": "item", "waarde": "Q144", "label": "hond", "label_en": "dog"},
            {"soort": "item", "waarde": "Q16970", "label": "kerk", "label_en": None},
            {"soort": "somevalue", "waarde": "?", "label": "?"},
        ],
    }}
    text = commons_context(file)
    assert "- caption (nl): De Pieterskerk in Leiden" in text and "(en)" not in text
    assert "- depicts: dog, kerk" in text
    assert commons_context({}) == ""



def test_object_description_length():
    from cutter.beschrijving import build_prompt

    normal = build_prompt({"naam": "x"})
    assert "one or two sentences in Dutch describing what is shown." in normal  # as before: same cache key
    caption = build_prompt({"naam": "x"}, description_level="caption")
    assert "at most 230 characters" in caption and "one or two sentences in Dutch describing" not in caption
    assert "a paragraph of three to five sentences" in build_prompt({"naam": "x"}, description_level="uitgebreid")


def test_detection_clue_tells_what_the_app_knows():
    clue = beschrijving.detection_clue
    sure, source = clue({"bron": "sam", "zoekterm": "table", "score": 0.75})
    assert source == "zoekterm" and '"table"' in sure and "75%" in sure and "probably (part of) what \"table\" describes" in sure
    unsure, _ = clue({"bron": "sam", "zoekterm": "lemon", "score": 0.3})
    assert "unsure" in unsure and "30%" in unsure
    # Your own name beats the search term; a Commons region gives its label.
    named, source = clue({"bron": "sam", "zoekterm": "table", "score": 0.9, "naam": "side table with cloth"})
    assert source == "naam" and "side table with cloth" in named and "table\"" not in named
    assert clue({"bron": "commons", "label": "coat of arms"})[1] == "commons"
    # No clue for a group, a drawn box or a click.
    assert clue({"bron": "groep", "zoekterm": "bottle"}) == ("", None)
    assert clue({"bron": "handmatig", "zoekterm": "rechthoek"}) == ("", None)
    assert clue({"bron": "sam", "zoekterm": "klik", "score": 0.8}) == ("", None)
    # ... unless you named it: your name always goes along (wish Olaf).
    drawn, source = clue({"bron": "handmatig", "zoekterm": "rechthoek", "naam": "silver ewer"})
    assert source == "naam" and "silver ewer" in drawn and "rechthoek" not in drawn
    assert clue({"bron": "sam", "zoekterm": "klik", "naam": "nautilus cup"})[1] == "naam"
    group, source = clue({"bron": "groep", "groep": {"leden": []}, "naam": "fruit bowl"})
    assert source == "naam" and "group as a whole" in group and "fruit bowl" in group
    # It goes into the question.
    prompt = beschrijving.build_prompt({"titel": "File:X.jpg"}, clue=sure)
    assert prompt.endswith(sure)


def test_four_lengths_in_one_call_and_the_slider_is_free(objects, album, tmp_path):
    """All four lengths come in one answer; showing another one is free and keeps the
    hand edits of each length; a version in the history holds all four (wish Olaf)."""
    service = DescriptionService(DummyVision(), objects, CONFIG, tmp_path / "cache")
    first = service.inventory(album, 1)["inventaris"]
    assert set(first["beschrijvingen"]) == set(beschrijving.DESCRIPTION_LEVELS)
    assert first["beschrijvingsniveau"] == "caption" and first["samenvatting"] == first["beschrijvingen"]["caption"]["nl"]
    # Edit the short one, look at the long one, and back: the edit is still there.
    service.edit_inventory(album, 1, {"beschrijvingsniveau": "kort"})
    edited = service.edit_inventory(album, 1, {"samenvatting": "Kort, met de hand uitgebreid."})["inventaris"]
    assert edited["bewerkt"] and edited["ai_origineel"]["samenvatting"] == first["beschrijvingen"]["kort"]["nl"]
    long = service.edit_inventory(album, 1, {"beschrijvingsniveau": "uitgebreid"})["inventaris"]
    assert long["samenvatting"] == first["beschrijvingen"]["uitgebreid"]["nl"] and not long.get("bewerkt")
    back = service.edit_inventory(album, 1, {"beschrijvingsniveau": "kort"})["inventaris"]
    assert back["samenvatting"] == "Kort, met de hand uitgebreid." and back["bewerkt"]
    # The history keeps all four lengths per version; putting one back brings all four.
    history = service.inventory_history(album, 1)
    assert history and set(history[0]["beschrijvingen"]) == set(beschrijving.DESCRIPTION_LEVELS)
    restored = service.restore_inventory(album, 1, history[0]["versie"])["inventaris"]
    assert restored["beschrijvingsniveau"] == "kort" and restored["samenvatting"] == first["beschrijvingen"]["kort"]["nl"]
    # A caption may not grow past 250 characters by hand.
    service.edit_inventory(album, 1, {"beschrijvingsniveau": "caption"})
    with pytest.raises(DetectionError):
        service.edit_inventory(album, 1, {"samenvatting": "x" * 251})
    # A length that was not made (an overview from before 0.39.0): 409.
    store = objects._load_store(album, 1)
    store["inventaris"].pop("beschrijvingen")
    objects._write_store(album, 1, store)
    with pytest.raises(DetectionError) as exc:
        service.edit_inventory(album, 1, {"beschrijvingsniveau": "kort"})
    assert exc.value.code == "length_not_made"


def test_an_unreadable_answer_is_not_kept(objects, album, tmp_path):
    """An answer that is not JSON, or a description without any text, gives an error that
    asks to retry; nothing is stored or cached, so asking again really asks again. A length
    the AI left empty is simply not there; the others work."""

    class Answer(DummyVision):
        def __init__(self, text):
            super().__init__()
            self.text = text

        def describe(self, *args, **kwargs):
            return {"output_text": self.text, "usage": {"input_tokens": 0, "output_tokens": 0}}

    for text in ("Sorry, I cannot see the image.", json.dumps({"paginasoort": "prent", "zoektermen": []})):
        service = DescriptionService(Answer(text), objects, CONFIG, tmp_path / "cache")
        with pytest.raises(DetectionError) as exc:
            service.inventory(album, 1)
        assert exc.value.code == "unreadable_answer" and exc.value.retry
        assert not objects._load_store(album, 1).get("inventaris")
        assert not list((tmp_path / "cache").rglob("*.json"))
    # One length empty: the chosen one is missing, so the first one there is is shown.
    fields = {f"samenvatting_{level}{suffix}": f"{level}{suffix}" for level in beschrijving.DESCRIPTION_LEVELS for suffix in ("", "_en")}
    fields["samenvatting_caption"] = fields["samenvatting_caption_en"] = ""
    service = DescriptionService(Answer(json.dumps({"paginasoort": "prent", "zoektermen": [], **fields})), objects, CONFIG, tmp_path / "cache")
    overview = service.inventory(album, 1)["inventaris"]
    assert "caption" not in overview["beschrijvingen"] and overview["beschrijvingsniveau"] == "kort" and overview["samenvatting"] == "kort"
