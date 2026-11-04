"""Description of a cut-out by a vision-language model ("Wat staat hierop?"),
and an overview of a whole page ("Wat staat op deze pagina?") that suggests
search terms for SAM (functional design 6.2, 6.3 and 7.6). Taken over from the
Delpher Uitsnijder (docs/beeld-taalmodel.md there).

Only on request, per object, through POST; never automatically and never via
a GET. Uses Muse Spark on the same Meta Model API and key as SAM. Context for
the model is the Commons description, caption, visible categories and
existing depicts items, explicitly as help and not as the truth. The answer is
in Dutch and English, with at most three search terms for depicts
(`wikidata_suggesties`); the app looks those up on Wikidata for free and the
user chooses the item. The model never makes up Q-ids.

Model choice (6.3): the cheap Contributor variant (Meta may train on the
input) only for public-domain files (P6216 = Q19652 and a PD licence template,
no CC) without the labels trademark, personality rights or original under
discussion, and only when switched on; Standard otherwise.

Tested only with constructed responses; no live calls without explicit
permission from Olaf.
"""

import base64
import hashlib
import io
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from . import __version__
from .detectie.basis import DetectionError
from .opruimen import mark_used

logger = logging.getLogger(__name__)

PROMPT_VERSION = 2  # 1: Dutch and English, wikidata_suggesties (0.1.0); 2: the cut-out's own caption (0.4.0)
MARGIN = 0.25  # share of the box added on every side, so text around the image comes along
MAX_MARGIN = 1.0  # the user may choose 0 to 100 % (in steps of 5 %)
MAX_SIDE = 1024  # pixels of the image sent to the model
MAX_PREVIEW_SIDE = 4000  # the larger preview in the lightbox, to read the text (never sent)
CONTEXT_CHARS = 800  # at most this much of the Commons description in the question
MAX_SUGGESTIONS = 3
BLOCKING_LABELS = {"merk", "persoonlijkheidsrechten", "ter_discussie"}  # no Contributor (6.3)

# USD per million tokens (input, output); docs/beeld-taalmodel.md of the Delpher Uitsnijder.
PRICES = {
    "muse-spark-1.3": (1.25, 4.25),
    "muse-spark-1.3-contributor": (0.10, 0.20),
    "muse-wonder-1.0": (4.00, 20.00),
}
# Input, output tokens per call, measured in the Delpher Uitsnijder (2-11-2026);
# the answer is now bilingual, so the output estimates are a little higher.
ESTIMATE_TOKENS = (1500, 2400)
ESTIMATE_OUTPUT_PER_EFFORT = {"minimal": 600, "low": 1100, "medium": 1800}
EFFORTS = ("minimal", "low", "medium", "high", "xhigh", "max")  # "none" gives HTTP 400 on Muse Spark

KINDS = [
    "logo", "portret", "persoon", "foto", "tekening", "gravure", "schilderij", "miniatuur", "kaart",
    "grafiek", "strip", "advertentie", "wapen", "initiaal", "ornament", "gebouw", "dier", "plant",
    "handschrift", "anders",
]

SCHEMA = {
    "type": "object",
    "properties": {
        "soort": {"type": "string", "enum": KINDS},
        "onderwerp": {"type": "string"},
        "onderwerp_en": {"type": "string"},
        "bedrijf_of_naam": {"type": ["string", "null"]},
        "tekst_in_beeld": {"type": ["string", "null"]},
        "tekst_rond_beeld": {"type": ["string", "null"]},
        "beschrijving": {"type": "string"},
        "beschrijving_en": {"type": "string"},
        "zekerheid": {"type": "string", "enum": ["hoog", "middel", "laag"]},
        "wikidata_suggesties": {"type": "array", "items": {"type": "string"}, "maxItems": MAX_SUGGESTIONS},
    },
    "required": [
        "soort", "onderwerp", "onderwerp_en", "bedrijf_of_naam", "tekst_in_beeld", "tekst_rond_beeld",
        "beschrijving", "beschrijving_en", "zekerheid", "wikidata_suggesties",
    ],
    "additionalProperties": False,
}
TEXT_FIELDS = [k for k, v in SCHEMA["properties"].items() if v["type"] != "array"]

INSTRUCTIONS = """You look at a cut-out from an image on Wikimedia Commons. The cut-out shows one object (for example a coat of arms, portrait, figure, drawing, initial, map or photograph) with a margin around it; the object is in the middle.

Answer in JSON with these fields:
- soort: what the object is, one of: {kinds}.
- onderwerp: what is depicted, as a short Dutch noun phrase of 2 to 8 words without an article, e.g. "wapen van de familie Van Bronckhorst", "heilige Catharina met rad". This becomes the caption.
- onderwerp_en: the same in English, e.g. "Coat of arms of the Van Bronckhorst family". This starts the new file name.
- bedrijf_of_naam: the person, family, company or place it belongs to, if a name is legible or clearly given in the context; otherwise null. Do not guess.
- tekst_in_beeld: the text that is legible inside the object itself, verbatim. null if none.
- tekst_rond_beeld: legible text directly above, below or beside the object in the margin, verbatim. null if none.
- beschrijving: one or two sentences in Dutch describing what is shown.
- beschrijving_en: the same in English.
- zekerheid: hoog, middel or laag: how sure you are about the name and the description.
- wikidata_suggesties: at most {max_suggestions} short English search terms for Wikidata items this cut-out depicts (e.g. "coat of arms", "Catherine of Alexandria"). Search terms only, never Q-ids.

The image is {title} on Wikimedia Commons. Context from the file page (may be incomplete or wrong, do not treat it as the truth):
- Description: {description}
- Caption: {caption}
- Categories: {categories}
- Already marked as depicted: {depicts}
- Caption of this cut-out (given by the user or a file note on Commons): {cutout_caption}"""


# A one-off hint from the user for "Ask again" (e.g. "only the boy"): part of
# the question, not of the caption; at most this many characters.
MAX_HINT = 300
PAGE_TEXT_INSTRUCTION = """

Text read earlier in the whole image this cut-out comes from (in and under the picture; read by a model, so it may contain errors):
<<<
{text}
>>>
Use it as context where it helps to name or describe the cut-out (e.g. a caption or verse about what is shown). For tekst_in_beeld and tekst_rond_beeld, only give text you can see in the cut-out itself; you may use this text to read it more accurately."""
MAX_PAGE_TEXT = 2000

HINT_INSTRUCTION = """

Instruction from the user for this question (follow it; it overrides the context above where they differ): {hint}"""

# Earlier descriptions kept per object, newest first, to choose from again.
MAX_HISTORY = 30

# The texts of a description the user may change by hand, in both languages.
EDITABLE = ("onderwerp", "onderwerp_en", "beschrijving", "beschrijving_en", "tekst_in_beeld", "tekst_rond_beeld")


def price(model):
    return PRICES.get(model, PRICES["muse-spark-1.3"])


def cost(model, input_tokens, output_tokens):
    p_in, p_out = price(model)
    return round((input_tokens * p_in + output_tokens * p_out) / 1_000_000, 6)


def estimate(model, effort=None, input_tokens=None):
    output = ESTIMATE_OUTPUT_PER_EFFORT.get(effort, ESTIMATE_TOKENS[1])
    return cost(model, input_tokens or ESTIMATE_TOKENS[0], output)


# -- Page overview ("Wat staat op deze pagina?") --------------------------------

INVENTORY_VERSION = 3  # 2: kind and summary also in English; 3: the text in and under the image
PAGE_WIDTH = 1600  # pixels of the page image sent to the model
ESTIMATE_PAGE_INPUT = 3000  # tokens: a whole page at 1600 px plus the question
MAX_TERMS = 12

INVENTORY_SCHEMA = {
    "type": "object",
    "properties": {
        "paginasoort": {"type": "string"},
        "paginasoort_en": {"type": "string"},
        "samenvatting": {"type": "string"},
        "samenvatting_en": {"type": "string"},
        "tekst": {"type": "string"},
        "zoektermen": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "en": {"type": "string"},
                    "nl": {"type": "string"},
                    "aantal": {"type": "integer"},
                    "waar": {"type": "string"},
                },
                "required": ["en", "nl", "aantal", "waar"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["paginasoort", "paginasoort_en", "samenvatting", "samenvatting_en", "tekst", "zoektermen"],
    "additionalProperties": False,
}

INVENTORY_INSTRUCTIONS = """You look at one whole image on Wikimedia Commons: {publication}.

List the visual objects in this image (not text), so that an open-vocabulary object detector (SAM) can find them. Answer in JSON:
- paginasoort: the kind of image in Dutch, a few words (e.g. "albumblad met wapens", "prent", "kaart", "pagina uit een getijdenboek").
- paginasoort_en: the same in English.
- samenvatting: one sentence in Dutch about what is visible.
- samenvatting_en: the same sentence in English.
- tekst: all text you can read in the image, including captions or verses printed under or around the picture, transcribed literally in its own language and spelling, with a newline between separate lines or blocks. Read it carefully; mark a word you cannot read with [?]. Leave it empty when there is no text.
- zoektermen: at most {max_terms} distinct kinds of visual objects, most frequent or most striking first. For each:
  - en: a short English noun phrase for the detector, singular, 1-3 words, concrete and visual (e.g. "portrait", "coat of arms", "saint", "angel", "decorated initial", "ship", "map", "flower", "ornament").
  - nl: the same in Dutch.
  - aantal: how many you see (an estimate).
  - waar: where in the image, in Dutch (e.g. "linksboven", "onderste helft").
Only list what you can actually see; do not guess. In zoektermen, skip plain text and borders."""


def parse_inventory(text):
    """The overview from the answer; terms are cleaned, de-duplicated and capped."""
    match = re.search(r"\{.*\}", text or "", re.S)
    try:
        data = json.loads(match.group(0)) if match else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return {"paginasoort": "", "paginasoort_en": "", "samenvatting": " ".join((text or "").split())[:300], "samenvatting_en": "", "tekst": "", "zoektermen": []}
    terms, seen = [], set()
    for entry in data.get("zoektermen") or []:
        if not isinstance(entry, dict):
            continue
        en = " ".join(str(entry.get("en") or "").lower().split())
        if not en or en in seen or len(en) > 40:
            continue
        seen.add(en)
        try:
            count = max(1, int(entry.get("aantal") or 1))
        except (TypeError, ValueError):
            count = 1
        terms.append({"en": en, "nl": " ".join(str(entry.get("nl") or en).split()), "aantal": count, "waar": str(entry.get("waar") or "")})
        if len(terms) == MAX_TERMS:
            break
    return {
        "paginasoort": " ".join(str(data.get("paginasoort") or "").split()),
        "paginasoort_en": " ".join(str(data.get("paginasoort_en") or "").split()),
        "samenvatting": " ".join(str(data.get("samenvatting") or "").split()),
        "samenvatting_en": " ".join(str(data.get("samenvatting_en") or "").split()),
        # The text in the image keeps its line breaks (verses, captions in two columns).
        "tekst": "\n".join(" ".join(line.split()) for line in str(data.get("tekst") or "").splitlines() if line.strip())[:2000],
        "zoektermen": terms,
    }


# ---------------------------------------------------------------------------
# Model choice
# ---------------------------------------------------------------------------


def choose_model(file, config):
    """The model for a file, with the reason (6.3). Contributor only when it
    is switched on, the file is public domain (P6216 and a PD template, no CC)
    and none of the labels trademark, personality rights or under discussion
    apply. Anything else goes to Standard.

    Returns {"model", "rechtenvrij", "reden", "reden_code", "labels"}: the
    reason as Dutch text (for logs and usage) and as a code the interface
    translates."""
    standard = config["BEELDMODEL"]
    rights = file.get("rechten") or {}
    blocking = BLOCKING_LABELS & set(rights.get("labels", []))
    free = bool(rights.get("publiek_domein")) and not blocking
    if free and config["BEELDMODEL_CONTRIBUTOR"]:
        return {
            "model": config["BEELDMODEL_RECHTENVRIJ"],
            "rechtenvrij": True,
            "reden": "Publiek domein: auteursrechtstatus Q19652 en een PD-sjabloon, zonder rechtenlabels.",
            "reden_code": "publiek_domein",
            "labels": [],
        }
    if free:
        code, reason = "contributor_uit", "Publiek domein, maar de goedkope Contributor-route staat uit (BEELDMODEL_CONTRIBUTOR)."
    elif blocking:
        code, reason = "rechtenlabel", "Rechtenlabel op het origineel: " + ", ".join(sorted(blocking)) + "."
    else:
        code, reason = "niet_vrij", "Niet (zeker) publiek domein: een licentie met voorwaarden, of geen auteursrechtstatus Q19652."
    return {"model": standard, "rechtenvrij": False, "reden": reason, "reden_code": code, "labels": sorted(blocking)}


# ---------------------------------------------------------------------------
# Request and response
# ---------------------------------------------------------------------------


def clean_margin(margin):
    """The margin as a share of the box, 0 to MAX_MARGIN in steps of 0.05;
    MARGIN when not given or not a number."""
    try:
        value = float(margin)
    except (TypeError, ValueError):
        return MARGIN
    if value != value:  # NaN
        return MARGIN
    return round(min(MAX_MARGIN, max(0.0, value)) * 20) / 20


def model_input(page_image, page_width, box, margin=MARGIN, max_side=MAX_SIDE, outline=False):
    """(JPEG bytes, size) of the box plus a margin, at most `max_side` pixels:
    what the model sees. With `outline` the box is drawn in red, for the
    preview in the interface only (never sent to the model)."""
    scale = page_image.width / page_width
    dx, dy = box["w"] * margin, box["h"] * margin
    left = max(0, int((box["x"] - dx) * scale))
    top = max(0, int((box["y"] - dy) * scale))
    right = min(page_image.width, round((box["x"] + box["w"] + dx) * scale))
    bottom = min(page_image.height, round((box["y"] + box["h"] + dy) * scale))
    crop = page_image.crop((left, top, max(left + 1, right), max(top + 1, bottom))).convert("RGB")
    factor = max_side / max(crop.size)
    if factor < 1:
        crop = crop.resize((max(1, round(crop.width * factor)), max(1, round(crop.height * factor))))
    else:
        factor = 1.0
    if outline:
        draw = ImageDraw.Draw(crop)
        x0 = (box["x"] * scale - left) * factor
        y0 = (box["y"] * scale - top) * factor
        x1 = ((box["x"] + box["w"]) * scale - left) * factor
        y1 = ((box["y"] + box["h"]) * scale - top) * factor
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(221, 51, 51), width=max(2, round(max(crop.size) / 250)))
    buffer = io.BytesIO()
    crop.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue(), crop.size


def crop_with_margin(page_image, page_width, box, margin=MARGIN, max_side=MAX_SIDE):
    """JPEG data URL of the box plus a margin, at most `max_side` pixels."""
    data, size = model_input(page_image, page_width, box, margin, max_side)
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii"), size


def context(file):
    """The Commons context for the question (6.2): description, caption,
    visible categories and existing depicts items, shortened."""
    summary = file.get("sdc") or {}
    captions = summary.get("captions") or {}
    caption = captions.get("en") or captions.get("nl") or next(iter(captions.values()), None)
    description = " ".join((file.get("beschrijving") or "").split())
    if len(description) > CONTEXT_CHARS:
        description = description[:CONTEXT_CHARS].rstrip() + "…"
    depicts = [d.get("label_en") or d.get("label") for d in summary.get("beeldt_af", [])]
    return {
        "description": f'"{description}"' if description else "none",
        "caption": f'"{caption}"' if caption else "none",
        "categories": ", ".join(file.get("categorieen") or []) or "none",
        "depicts": ", ".join(dict.fromkeys(d for d in depicts if d)) or "none",
    }


def clean_hint(hint):
    """The user's hint as one line, at most MAX_HINT characters ("" if none)."""
    return " ".join(str(hint or "").split())[:MAX_HINT]


def build_prompt(file, caption=None, hint=None, page_text=None):
    caption = " ".join((caption or "").split())[:CONTEXT_CHARS]
    prompt = INSTRUCTIONS.format(
        kinds=", ".join(KINDS),
        max_suggestions=MAX_SUGGESTIONS,
        title=f'"{file.get("naam") or file.get("titel")}"',
        cutout_caption=f'"{caption}"' if caption else "none",
        **context(file),
    )
    page_text = (page_text or "").strip()[:MAX_PAGE_TEXT]
    if page_text:
        prompt += PAGE_TEXT_INSTRUCTION.format(text=page_text)
    hint = clean_hint(hint)
    return prompt + HINT_INSTRUCTION.format(hint=hint) if hint else prompt


def build_request(model, prompt, data_url, effort=None, schema=SCHEMA, name="beschrijving"):
    """Responses API body: one image and the question, JSON as output.
    `effort` sets `reasoning.effort`; without it the model chooses (and
    reasons a lot: ~2000 billed output tokens)."""
    body = {
        "model": model,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        "text": {"format": {"type": "json_schema", "name": name, "schema": schema, "strict": True}},
        "stream": False,
    }
    if effort:
        body["reasoning"] = {"effort": effort}
    return body


def output_text(body):
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    return "".join(
        content.get("text", "")
        for item in body.get("output") or []
        for content in item.get("content") or []
        if content.get("type") == "output_text"
    )


def parse_answer(text):
    """The JSON object in the answer (also inside a ```json block). Unknown
    fields are dropped; an unreadable answer becomes the description itself
    with low certainty. Suggestions that look like Q-ids are dropped."""
    match = re.search(r"\{.*\}", text or "", re.S)
    try:
        data = json.loads(match.group(0)) if match else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        result = {key: None for key in TEXT_FIELDS}
        result.update(
            {
                "soort": "anders",
                "beschrijving": " ".join((text or "").split())[:500] or "Geen antwoord.",
                "zekerheid": "laag",
                "wikidata_suggesties": [],
            }
        )
        return result
    result = {}
    for key in TEXT_FIELDS:
        value = data.get(key)
        result[key] = " ".join(value.split()) if isinstance(value, str) and value.strip() else None
    if result["soort"] not in KINDS:
        result["soort"] = "anders"
    if result["zekerheid"] not in ("hoog", "middel", "laag"):
        result["zekerheid"] = "laag"
    result["beschrijving"] = result["beschrijving"] or ""
    suggestions = data.get("wikidata_suggesties") if isinstance(data.get("wikidata_suggesties"), list) else []
    cleaned = []
    for term in suggestions:
        term = " ".join(str(term or "").split())
        if term and len(term) <= 80 and not re.fullmatch(r"[Qq]\d+", term) and term.lower() not in {t.lower() for t in cleaned}:
            cleaned.append(term)
    result["wikidata_suggesties"] = cleaned[:MAX_SUGGESTIONS]
    return result


def usage_tokens(body):
    """(input, output, reasoning) tokens; reasoning is part of output."""
    usage = body.get("usage") or {}
    reasoning = (usage.get("output_tokens_details") or {}).get("reasoning_tokens")
    return usage.get("input_tokens"), usage.get("output_tokens"), reasoning


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DummyVision:
    """Free stand-in for development (DETECTIE_MODUS=dummy): a fixed answer
    built from the object's label, so the whole flow can be tried."""

    betaald = False

    def describe(self, model, prompt, data_url, obj, effort=None, schema=SCHEMA):
        if schema is INVENTORY_SCHEMA:
            answer = {
                "paginasoort": "voorbeeldafbeelding (dummy)",
                "paginasoort_en": "example image (dummy)",
                "samenvatting": "Voorbeeldoverzicht (dummy, geen echt model).",
                "samenvatting_en": "Example overview (dummy, no real model).",
                "tekst": "Voorbeeldtekst onder de afbeelding (dummy).",
                "zoektermen": [
                    {"en": "coat of arms", "nl": "wapen", "aantal": 2, "waar": "bovenaan"},
                    {"en": "portrait", "nl": "portret", "aantal": 1, "waar": "midden"},
                    {"en": "decorated initial", "nl": "initiaal", "aantal": 1, "waar": "linksboven"},
                ],
            }
            return {"output_text": json.dumps(answer), "usage": {"input_tokens": 0, "output_tokens": 0}}
        label = obj.get("label_en") or obj.get("label") or "object"
        dutch = obj.get("label_nl") or label
        answer = {
            "soort": {"logo": "logo", "coat of arms": "wapen", "portrait": "portret"}.get(label, "anders"),
            "onderwerp": f"voorbeeld van een {dutch}",
            "onderwerp_en": label[:1].upper() + label[1:],
            "bedrijf_of_naam": None,
            "tekst_in_beeld": None,
            "tekst_rond_beeld": None,
            "beschrijving": f"Voorbeeldbeschrijving (dummy, geen echt model) van een {dutch}.",
            "beschrijving_en": f"Example description (dummy, not a real model) of a {label}.",
            "zekerheid": "laag",
            "wikidata_suggesties": [label],
        }
        return {"output_text": json.dumps(answer), "usage": {"input_tokens": 0, "output_tokens": 0}}


class MetaVision:
    """Muse Spark via the Meta Model API (Responses API)."""

    betaald = True

    def __init__(self, api_key, base_url="https://api.meta.ai/v1", timeout=90, session=None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def describe(self, model, prompt, data_url, obj, effort=None, schema=SCHEMA):
        if not self.api_key:
            raise DetectionError("Geen MODEL_API_KEY ingesteld; een beschrijving is niet mogelijk.", status=503, code="no_api_key")
        try:
            response = self.session.post(
                f"{self.base_url}/responses",
                json=build_request(model, prompt, data_url, effort, schema, "beschrijving" if schema is SCHEMA else "pagina"),
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise DetectionError("De Meta Model API is niet bereikbaar.", retry=True) from exc
        if response.status_code == 200:
            return response.json()
        try:
            detail = (response.json().get("error") or {}).get("message", "")
        except ValueError:
            detail = ""
        status = response.status_code
        if status == 400:
            raise DetectionError(f"Het model weigerde het verzoek: {detail}".rstrip(": "), status=400)
        if status in (401, 403):
            raise DetectionError("De API-sleutel voor de Meta Model API wordt niet geaccepteerd.", status=503)
        if status == 404:
            raise DetectionError(f"Model '{model}' niet gevonden of geen toegang.", status=503)
        if status == 429:
            # Never fall back to the more expensive model silently.
            raise DetectionError(
                f"Te veel verzoeken aan '{model}'; probeer het zo opnieuw, of kies Standard.", status=429, retry=True
            )
        raise DetectionError(f"De Meta Model API gaf een fout (HTTP {status}).", retry=True)


def make_vision(config):
    if config["DETECTIE_MODUS"] == "live":
        return MetaVision(config["MODEL_API_KEY"], base_url=config["META_API_BASE"])
    return DummyVision()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DescriptionService:
    """Describe objects of the detection service and store the result on the
    object (`beschrijving`), cached per file SHA-1, object box, model and
    prompt version."""

    def __init__(self, vision, objects, config, cache_dir):
        self.vision = vision
        self.objects = objects  # DetectionService: object store, Commons client, usage
        self.config = config
        self.cache_dir = Path(cache_dir) / "beschrijvingen"

    def _model(self, file, wanted):
        choice = choose_model(file, self.config)
        if wanted in (None, "", "auto"):
            return choice
        if wanted == "standaard":
            return {"model": self.config["BEELDMODEL"], "rechtenvrij": choice["rechtenvrij"], "reden": "Standard gekozen.", "reden_code": "standaard_gekozen", "labels": []}
        if wanted == "contributor":
            if choice["model"] != self.config["BEELDMODEL_RECHTENVRIJ"]:
                raise DetectionError(f"Contributor is voor dit bestand niet toegestaan. {choice['reden']}", status=409, code="contributor_not_allowed")
            return choice
        raise DetectionError("Geef model als 'auto', 'standaard' of 'contributor'.", status=400)

    def _effort(self):
        effort = self.config.get("BEELDMODEL_REDENEREN")
        return effort if effort in EFFORTS else None

    def plan(self, file, n, object_id, user=None):
        """What a description would cost, without calling anything."""
        obj = self.objects._find(file, n, object_id)
        choice = choose_model(file, self.config)
        paid = self.vision.betaald
        return {
            "beschrijving": obj.get("beschrijving"),
            "model": choice["model"],
            "reden": choice["reden"],
            "reden_code": choice["reden_code"],
            "labels": choice["labels"],
            "rechtenvrij": choice["rechtenvrij"],
            "betaald": paid,
            "redeneren": self._effort(),
            "kosten_schatting_usd": estimate(choice["model"], self._effort()) if paid else 0.0,
            "kosten_standaard_usd": estimate(self.config["BEELDMODEL"], self._effort()) if paid else 0.0,
            "budget": self.objects.verbruik.status(user),
        }

    @staticmethod
    def _caption(obj):
        return ((obj.get("bijschrift") or {}).get("tekst") or "").strip()

    def _page_text(self, file, n):
        """The text the page overview read in and under the whole image ("" if none)."""
        overview = self.objects._load_store(file, n).get("inventaris") or {}
        return (overview.get("tekst") or "").strip()[:MAX_PAGE_TEXT]

    def _cache_path(self, file, n, obj, model, hint="", margin=MARGIN, page_text=""):
        # The caption, a hint and the margin are part of the question, so another
        # one is another (cached) answer. With the defaults the key is as before.
        key = f"{file['sha1']}|{n}|{obj['box']}|{self._caption(obj)}|{model}|{self._effort()}|{PROMPT_VERSION}"
        if hint:
            key += f"|hint:{hint}"
        if margin != MARGIN:
            key += f"|marge:{margin}"
        if page_text:
            key += f"|paginatekst:{hashlib.sha1(page_text.encode()).hexdigest()}"
        digest = hashlib.sha1(key.encode()).hexdigest()
        return self.cache_dir / digest[:2] / f"{digest}.json"

    def _source_image(self, file, n):
        """The page image to crop from: the original when it can be used,
        otherwise the largest standard rendering."""
        client = self.objects.client
        if file.get("uitsnijden_mogelijk"):
            return client.original_image(file, n)
        return Image.open(io.BytesIO(client.page_image(file, n, 3840)))

    def model_preview(self, file, n, object_id, margin=None, max_side=None):
        """JPEG of what the model would see with this margin, the box outlined
        in red. `max_side` (up to MAX_PREVIEW_SIDE) gives a larger version, to
        read and check the text in the image. Free: nothing is sent to the model."""
        obj = self.objects._find(file, n, object_id)
        page = self.objects.client.load_page(file, n)
        side = max(MAX_SIDE, min(int(max_side or MAX_SIDE), MAX_PREVIEW_SIDE))
        data, _size = model_input(self._source_image(file, n), page["breedte"], obj["box"], clean_margin(margin), side, outline=True)
        return data

    def describe(self, file, n, object_id, model=None, again=False, user=None, hint=None, margin=None):
        """Describe an object (paid in live mode) and store the answer on it.
        `hint` is an extra instruction from the user for this question;
        `margin` the share of the box shown around it (default MARGIN)."""
        obj = self.objects._find(file, n, object_id)
        choice = self._model(file, model)
        hint = clean_hint(hint)
        margin = clean_margin(margin)
        # The text read in the whole image (page overview) goes along as context.
        page_text = self._page_text(file, n)
        path = self._cache_path(file, n, obj, choice["model"], hint, margin, page_text)
        if path.exists() and not again:
            mark_used(path)
            description = json.loads(path.read_text(encoding="utf-8"))
            description["uit_cache"] = True
            return self._store(file, n, object_id, description, user)

        effort = self._effort()
        if self.vision.betaald:
            self.objects.verbruik.check(1, user=user, cost=estimate(choice["model"], effort))
        page = self.objects.client.load_page(file, n)
        data_url, size = crop_with_margin(self._source_image(file, n), page["breedte"], obj["box"], margin)
        prompt = build_prompt(file, self._caption(obj), hint, page_text)

        body = self.vision.describe(choice["model"], prompt, data_url, self.objects.public(file, n, obj), effort)
        tokens_in, tokens_out, tokens_reasoning = usage_tokens(body)
        if self.vision.betaald:
            amount = cost(choice["model"], tokens_in, tokens_out) if tokens_in is not None else estimate(choice["model"], effort)
        else:
            amount = 0.0
        description = {
            **parse_answer(output_text(body)),
            "model": choice["model"],
            "model_reden": choice["reden"],
            "model_reden_code": choice["reden_code"],
            "model_reden_labels": choice["labels"],
            "rechtenvrij": choice["rechtenvrij"],
            "redeneren": effort,
            "tokens": {"invoer": tokens_in, "uitvoer": tokens_out, "waarvan_redeneren": tokens_reasoning},
            "kosten_usd": amount,
            "verstuurde_afmetingen": list(size),
            "promptversie": PROMPT_VERSION,
            "aanwijzing": hint or None,
            "marge": margin,
            "paginatekst": bool(page_text),
            "tijdstempel": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "appversie": __version__,
        }
        if self.vision.betaald:
            self.objects.verbruik.register(
                {
                    "soort": "beschrijving",
                    "bestand": file["mid"],
                    "titel": file["titel"],
                    "pagina": n,
                    "object": object_id,
                    "term": f"Wat staat hierop? ({choice['model']})",
                    "model": choice["model"],
                    "redeneren": effort,
                    "tokens": description["tokens"],
                },
                cost=amount,
                user=user,
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(description, ensure_ascii=False, indent=2), encoding="utf-8")
        description["uit_cache"] = False
        return self._store(file, n, object_id, description, user)

    # -- History of descriptions ------------------------------------------------

    @staticmethod
    def _same(a, b):
        """Whether two descriptions are the same answer (same time, question and texts)."""
        keys = ("tijdstempel", "aanwijzing", "marge", "paginatekst", *EDITABLE)
        return all((a or {}).get(k) == (b or {}).get(k) for k in keys)

    def _keep_in_history(self, obj):
        """Put the current description on top of the object's history (not twice)."""
        current = obj.get("beschrijving")
        if not current:
            return
        history = [h for h in obj.get("beschrijving_geschiedenis", []) if not self._same(h, current)]
        obj["beschrijving_geschiedenis"] = [current, *history][:MAX_HISTORY]

    def _cached_variants(self, file, n, obj):
        """Answers for this object that are still in the cache: one per
        combination of model, hint and margin asked so far. So descriptions
        from before the history existed can be chosen again too."""
        combos = {("", MARGIN)}
        for path in self.cache_dir.glob("*/*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if "beschrijving" in data:
                combos.add((data.get("aanwijzing") or "", clean_margin(data.get("marge"))))
        models = dict.fromkeys([self.config["BEELDMODEL"], self.config["BEELDMODEL_RECHTENVRIJ"]])
        page_texts = dict.fromkeys(["", self._page_text(file, n)])
        found = []
        for model in models:
            for (hint, margin), page_text in ((c, p) for c in combos for p in page_texts):
                path = self._cache_path(file, n, obj, model, hint, margin, page_text)
                if path.exists():
                    try:
                        found.append(json.loads(path.read_text(encoding="utf-8")))
                    except (OSError, ValueError):
                        continue
        return found

    def history(self, file, n, object_id):
        """Earlier descriptions of an object, newest first: the kept history,
        plus answers still in the cache. Without the current one. Free."""
        obj = self.objects._find(file, n, object_id)
        current = obj.get("beschrijving")
        entries = list(obj.get("beschrijving_geschiedenis", []))
        for variant in self._cached_variants(file, n, obj):
            if not any(self._same(variant, e) or e.get("tijdstempel") == variant.get("tijdstempel") for e in entries):
                entries.append({k: v for k, v in variant.items() if k != "uit_cache"})
        entries = [e for e in entries if not (current and e.get("tijdstempel") == current.get("tijdstempel") and self._same(e, current))]
        return sorted(entries, key=lambda e: e.get("tijdstempel") or "", reverse=True)

    def restore(self, file, n, object_id, timestamp, edited=None):
        """Make an earlier description (by its tijdstempel; `edited` picks the
        hand-edited or the AI version when both exist) the current one again;
        the current one goes into the history. Free."""
        candidates = [e for e in self.history(file, n, object_id) if e.get("tijdstempel") == timestamp]
        if edited is not None:
            candidates = [e for e in candidates if bool(e.get("bewerkt")) == bool(edited)] or candidates
        if not candidates:
            raise DetectionError("Die eerdere beschrijving bestaat niet (meer).", status=404, code="not_found")
        chosen = candidates[0]
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            obj = self.objects._find_in(store, object_id)
            self._keep_in_history(obj)
            obj["beschrijving_geschiedenis"] = [h for h in obj.get("beschrijving_geschiedenis", []) if not self._same(h, chosen)]
            obj["beschrijving"] = chosen
            self.objects._write_store(file, n, store)
        return self.objects.public(file, n, obj)

    def _store(self, file, n, object_id, description, user=None):
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            obj = self.objects._find_in(store, object_id)
            new = {k: v for k, v in description.items() if k != "uit_cache"}
            if not self._same(obj.get("beschrijving"), new):
                self._keep_in_history(obj)
            obj["beschrijving"] = new
            self.objects._write_store(file, n, store)
        result = self.objects.public(file, n, obj)
        return {"object": result, "uit_cache": description["uit_cache"], "budget": self.objects.verbruik.status(user)}

    def edit(self, file, n, object_id, changes):
        """Change the texts of the stored description by hand. The first time
        a field changes, its AI text is kept in "ai_origineel", so the UI can
        go back to it. Free: never calls the model."""
        unknown = set(changes) - set(EDITABLE)
        if unknown or not all(isinstance(v, str) for v in changes.values()):
            raise DetectionError(f"Alleen deze velden zijn te bewerken: {', '.join(EDITABLE)}.", status=400, code="invalid_body")
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            obj = self.objects._find_in(store, object_id)
            description = obj.get("beschrijving")
            if not description:
                raise DetectionError("Dit object heeft nog geen beschrijving.", status=409, code="no_description")
            original = description.setdefault("ai_origineel", {})
            for field, value in changes.items():
                value = value.strip()
                if field not in original:
                    original[field] = description.get(field) or ""
                description[field] = value
                if value == original[field]:
                    original.pop(field)
            if not original:
                description.pop("ai_origineel")
            description["bewerkt"] = bool(original)
            self.objects._write_store(file, n, store)
        return self.objects.public(file, n, obj)

    def remove(self, file, n, object_id):
        """Forget the stored description (the cached answer stays, so asking
        again with the same model is free)."""
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            obj = self.objects._find_in(store, object_id)
            self._keep_in_history(obj)  # removed, but it can be chosen again
            obj.pop("beschrijving", None)
            self.objects._write_store(file, n, store)
        return self.objects.public(file, n, obj)

    # -- Page overview ("Wat staat op deze pagina?") ---------------------------

    def inventory_plan(self, file, n, user=None):
        """The stored overview of a page (or None) and what a new one would
        cost. Free: never calls the model."""
        store = self.objects._load_store(file, n)
        choice = choose_model(file, self.config)
        paid = self.vision.betaald
        return {
            "inventaris": store.get("inventaris"),
            "model": choice["model"],
            "reden": choice["reden"],
            "redeneren": self._effort(),
            "betaald": paid,
            "kosten_schatting_usd": estimate(choice["model"], self._effort(), ESTIMATE_PAGE_INPUT) if paid else 0.0,
            "budget": self.objects.verbruik.status(user),
        }

    def _inventory_cache_path(self, file, n, model):
        key = f"pagina|{file['sha1']}|{n}|{model}|{self._effort()}|{INVENTORY_VERSION}"
        digest = hashlib.sha1(key.encode()).hexdigest()
        return self.cache_dir / digest[:2] / f"{digest}.json"

    def inventory(self, file, n, model=None, again=False, user=None):
        """Ask the model what is on the whole page (paid in live mode, cached)
        and keep the overview in the page's store ("inventaris")."""
        choice = self._model(file, model)
        path = self._inventory_cache_path(file, n, choice["model"])
        if path.exists() and not again:
            mark_used(path)
            overview = json.loads(path.read_text(encoding="utf-8"))
            return self._store_inventory(file, n, overview, cached=True, user=user)

        effort = self._effort()
        if self.vision.betaald:
            self.objects.verbruik.check(1, user=user, cost=estimate(choice["model"], effort, ESTIMATE_PAGE_INPUT))
        image = Image.open(io.BytesIO(self.objects.client.page_image(file, n, PAGE_WIDTH))).convert("RGB")
        if image.width > PAGE_WIDTH:
            image = image.resize((PAGE_WIDTH, round(image.height * PAGE_WIDTH / image.width)))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        data_url = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
        publication = f'"{file.get("naam")}"' + (f", page {n}" if file.get("paginas", 1) > 1 else "")
        prompt = INVENTORY_INSTRUCTIONS.format(publication=publication, max_terms=MAX_TERMS)

        body = self.vision.describe(choice["model"], prompt, data_url, None, effort, schema=INVENTORY_SCHEMA)
        tokens_in, tokens_out, tokens_reasoning = usage_tokens(body)
        if self.vision.betaald:
            amount = cost(choice["model"], tokens_in, tokens_out) if tokens_in is not None else estimate(choice["model"], effort, ESTIMATE_PAGE_INPUT)
        else:
            amount = 0.0
        overview = {
            **parse_inventory(output_text(body)),
            "model": choice["model"],
            "model_reden": choice["reden"],
            "redeneren": effort,
            "tokens": {"invoer": tokens_in, "uitvoer": tokens_out, "waarvan_redeneren": tokens_reasoning},
            "kosten_usd": amount,
            "verstuurde_afmetingen": list(image.size),
            "versie": INVENTORY_VERSION,
            "tijdstempel": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "appversie": __version__,
        }
        if self.vision.betaald:
            self.objects.verbruik.register(
                {
                    "soort": "inventaris",
                    "bestand": file["mid"],
                    "titel": file["titel"],
                    "pagina": n,
                    "term": f"Wat staat op deze pagina? ({choice['model']})",
                    "model": choice["model"],
                    "redeneren": effort,
                    "tokens": overview["tokens"],
                },
                cost=amount,
                user=user,
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")
        return self._store_inventory(file, n, overview, cached=False, user=user)

    def _store_inventory(self, file, n, overview, cached, user=None):
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            store["inventaris"] = overview
            self.objects._write_store(file, n, store)
        return {"inventaris": overview, "uit_cache": cached, "budget": self.objects.verbruik.status(user)}
