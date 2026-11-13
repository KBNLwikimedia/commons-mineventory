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
from contextlib import nullcontext
import hashlib
import json
import time
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import ImageDraw

from . import __version__
from .detectie.meta_sam import extract_output_text
from .concept import MAX_CAPTION
from .detectie.basis import INTERNAL_LABELS, DetectionError
from .detectie.meta_api import MetaClient
from .export import encode
from .opruimen import cached_bytes, mark_used, sharded
from .commons import open_image
from .opslag import read_json, write_json

logger = logging.getLogger(__name__)


def _is_dict(data):
    return isinstance(data, dict)


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
ESTIMATE_OUTPUT_PER_EFFORT = {"minimal": 600, "low": 1100, "medium": 1800, "high": 3000}
# The reasoning efforts you may choose when asking a part of the page overview anew (wish Olaf
# 13-11-2026); higher costs more, so the scale stops at "high".
CHOSEN_EFFORTS = ("low", "medium", "high")
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
- beschrijving: {description_rule}
- beschrijving_en: {description_rule_en}
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
MAX_FIELD = 4000  # characters per text field of an answer (a long verse fits; a runaway answer not)
PAGE_TEXT_INSTRUCTION = """

Text read earlier in the whole image this cut-out comes from (in and under the picture; read by a model, so it may contain errors):
<<<
{text}
>>>
Use it as context where it helps to name or describe the cut-out (e.g. a caption or verse about what is shown). For tekst_in_beeld and tekst_rond_beeld, only give text you can see in the cut-out itself; you may use this text to read it more accurately."""
MAX_PAGE_TEXT = 2000

HINT_INSTRUCTION = """

Instruction from the user for this question (follow it; it overrides the context above where they differ): {hint}"""

# What the app already knows about the object, as a clue (wish Olaf, 8-11-2026): the name the
# user gave it, its region label on Commons, or the search term the image detection (SAM)
# found it with and how sure it was. A clue, not the truth: the model checks what it sees.
CLUE_SURE = 0.5  # below this certainty the detection is called unsure
PLACEHOLDER_TERMS = {"rechthoek", "klik"}  # what the app calls a drawn box and a click
CLUE_NAME = """

The user named this object: "{name}". Take this as what it shows, unless the image clearly shows something else."""
CLUE_GROUP_NAME = """

The user named this group as a whole: "{name}". Take this as what the objects together show, unless the image clearly shows something else."""
CLUE_COMMONS = """

On Wikimedia Commons this region of the image is marked as "{name}" (by a person; it may be incomplete). Take this as what it shows, unless the image clearly shows something else."""
CLUE_TERM = """

An image detector (SAM) found this object when searching for "{term}" (certainty {pct}%). It is probably (part of) what "{term}" describes, or something related to it. Check what you see; if it is something else, describe what it really is."""
CLUE_TERM_UNSURE = """

An image detector (SAM) found this object when searching for "{term}", but it was unsure (certainty {pct}%). It may be (part of) what "{term}" describes, or something else entirely; describe what you actually see."""
# The other words it was found with ("Also found as", wish Olaf 13-11-2026), after the clue.
CLUE_ALSO = """ The image detector also found it when searching for {words}."""


def also_found(obj):
    """The other words the image detection found this object with ("Also found as"): the
    English word that was searched, with the highest certainty, without its own term and
    without clicks or drawn boxes. [(word, score or None)], in the order found."""
    own = {str(obj.get(k) or "").strip().lower() for k in ("zoekterm", "label")}
    words = {}
    for entry in obj.get("ook") or []:
        word = " ".join(str(entry.get("label") or entry.get("zoekterm") or "").split())[:80]
        key = word.lower()
        if not word or key in own or key in INTERNAL_LABELS:
            continue
        score = entry.get("score")
        if key not in words or (score is not None and (words[key][1] is None or score > words[key][1])):
            words[key] = (word, score)
    return list(words.values())


def also_found_sentence(obj):
    """CLUE_ALSO for the words in also_found, or "" when there are none."""
    found = also_found(obj)
    if not found:
        return ""
    parts = [f'"{word}" (certainty {round(score * 100)}%)' if score is not None else f'"{word}"' for word, score in found]
    words = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return CLUE_ALSO.format(words=words)


def detection_clue(obj):
    """The clue sentence for an object (with its leading blank line), and what it was based on;
    ("", None) when there is none. A name the user gave (the pencil) always goes along, for
    every kind of object: found, drawn, clicked or a group (wish Olaf, 8-11-2026). Without a
    name there is none for a group (its members are named already), a drawn box or a click."""
    name = " ".join(str(obj.get("naam") or "").split())[:120]
    is_group = obj.get("bron") == "groep" or bool(obj.get("groep"))
    also = "" if is_group else also_found_sentence(obj)  # "Also found as" goes along (wish Olaf)
    if name:
        return (CLUE_GROUP_NAME if is_group else CLUE_NAME).format(name=name) + also, "naam"
    if is_group:
        return "", None
    if obj.get("bron") == "commons":
        label = " ".join(str(obj.get("label_item") or obj.get("label") or "").split())[:120]
        return (CLUE_COMMONS.format(name=label) + also, "commons") if label else ("", None)
    # A box drawn by hand ("rechthoek") or a click ("klik") has no real search term.
    if obj.get("bron") == "handmatig":
        return "", None
    term = " ".join(str(obj.get("zoekterm") or "").split())[:80]
    if not term or term.lower() in PLACEHOLDER_TERMS:
        return "", None
    score = obj.get("score")
    if score is None:
        return CLUE_TERM.format(term=term, pct="unknown").replace(" (certainty unknown%)", "") + also, "zoekterm"
    template = CLUE_TERM if score >= CLUE_SURE else CLUE_TERM_UNSURE
    return template.format(term=term, pct=round(score * 100)) + also, "zoekterm"


# A group (7.4): its box also shows what lies between its members, so the question
# says what the group is made of and to look at those only (wish Olaf, 5-11-2026).
GROUP_INSTRUCTION = """

This cut-out is a group of several objects that belong together: {members}. Describe only these objects, together; ignore everything else that is visible in the image, also between them."""
# With space around the cut-out (the margin slider), the surroundings are there to be used:
# as context, e.g. a caption printed under the picture, not as part of the subject.
GROUP_INSTRUCTION_CONTEXT = """

This cut-out is a group of several objects that belong together: {members}. Describe only these objects, together, as the subject. The image also shows some of their surroundings: use those only as context, for instance text printed around them (a caption), but do not describe other things as part of the subject."""


def group_members(obj):
    """What a group consists of, in English, e.g. "lemon (1), bunch of grapes (2)";
    "" for an object that is not a group."""
    counts = {}
    for member in (obj.get("groep") or {}).get("leden", []):
        description = member.get("beschrijving") or {}
        label = member.get("label_en") or member.get("label") or ""
        if label.lower() in INTERNAL_LABELS:
            label = ""
        name = member.get("naam") or description.get("onderwerp_en") or (member.get("bijschrift") or {}).get("tekst") or label or "object"
        name = " ".join(str(name).split())[:60]
        counts[name] = counts.get(name, 0) + 1
    return ", ".join(f"{name} ({count})" for name, count in counts.items())


# What the members of a group were described as before, alone (wish Olaf, 6-11-2026): context
# for the group as a whole. Marked as earlier answers that may be wrong, so the image counts.
GROUP_CONTEXT_INSTRUCTION = """

Earlier AI descriptions of these objects, each made of that object on its own (they may be wrong; what you see in the image counts):
{lines}"""
MAX_MEMBER_CONTEXT = 400  # characters per member
MAX_GROUP_CONTEXT = 2400  # characters for all members together


def member_context(member):
    """One member's earlier description as one line of context ("" without one):
    its subject and description in English, and the text read in and around it."""
    description = member.get("beschrijving") or {}
    text = " ".join(str(description.get("beschrijving_en") or "").split())
    if not text:
        return ""
    name = description.get("onderwerp_en") or (member.get("bijschrift") or {}).get("tekst") or member.get("label_en") or member.get("label") or "object"
    line = f"- {' '.join(str(name).split())[:60]}: {text}"
    for key, label in (("tekst_in_beeld", "Text in it"), ("tekst_rond_beeld", "Text around it")):
        read = " ".join(str(description.get(key) or "").split())
        if read:
            line += f' {label}: "{read}".'
    return line[:MAX_MEMBER_CONTEXT]


COMMONS_CONTEXT_INSTRUCTION = """
What Commons already says about this image, entered by people (use it as context, for names and meaning; still describe and list only what you can see, and do not copy it word for word):
{context}"""
MAX_COMMONS_CONTEXT = 1500


def commons_context(file):
    """The captions and the depicts (P180) items already on the file, as context
    for the AI (backlog 26); "" when there are none. Free: read with the file."""
    sdc_summary = file.get("sdc") or {}
    lines = []
    for lang, text in sorted((sdc_summary.get("captions") or {}).items()):
        if text:
            lines.append(f"- caption ({lang}): {' '.join(str(text).split())}")
    names = []
    for statement in sdc_summary.get("beeldt_af") or []:
        if statement.get("soort") != "item":
            continue
        name = statement.get("label_en") or statement.get("label") or statement.get("waarde")
        if name and name not in names:
            names.append(name)
    if names:
        lines.append(f"- depicts: {', '.join(names)}")
    return "\n".join(lines)[:MAX_COMMONS_CONTEXT]


def group_context(obj):
    """The earlier descriptions of a group's members, one line each; "" when none has one."""
    lines = [line for line in (member_context(m) for m in (obj.get("groep") or {}).get("leden", [])) if line]
    return "\n".join(lines)[:MAX_GROUP_CONTEXT]


# Earlier descriptions kept per object, newest first, to choose from again.
MAX_HISTORY = 30

# The texts of a description the user may change by hand, in both languages.
EDITABLE = ("onderwerp", "onderwerp_en", "bedrijf_of_naam", "beschrijving", "beschrijving_en", "tekst_in_beeld", "tekst_rond_beeld")


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

# How many kinds of objects the search terms ask for (the slider at "Beschrijf deze
# afbeelding", functional design 7.6): from the one main subject to many small details.
# Level -> (at most this many terms, the rule for the terms in the question).
# "normaal" is the question as it was before the slider, so its answers stay in the cache.
DETAIL_LEVELS = {
    "hoofdonderwerp": (1, "only the one main subject of the image: the single most important thing it shows."),
    "hoofdzaken": (3, "at most 3 distinct kinds of visual objects: only the main subjects, large and prominent."),
    "normaal": (MAX_TERMS, "at most 12 distinct kinds of visual objects, most frequent or most striking first."),
    "details": (20, "up to 20 distinct kinds of visual objects, also small details (such as insects, small animals, buttons, jewellery, ornaments, things in the background), most striking first."),
}
DEFAULT_DETAIL = "normaal"

CAPTION_MAX = MAX_CAPTION  # characters: the limit of a caption (label) in the structured data on Commons
CAPTION_ASK = 230  # what the question asks for, to leave some room


def cap_caption(text, limit=CAPTION_MAX):
    """A text of at most `limit` characters: cut after the last whole sentence that fits,
    else after the last whole word, with "…" (which counts)."""
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    head = text[:limit]
    end = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if end >= limit // 2:
        return head[: end + 1]
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return cut + "…"

# How long the description of the whole image is (the slider at "Beschrijving laten maken",
# wish Olaf 6-11-2026). Level -> (rule for samenvatting, rule for samenvatting_en).
# "normaal" is the question as it was before the slider, so its answers stay in the cache.
DESCRIPTION_LEVELS = {
    "kort": ("a few words in Dutch: what the image shows, at most one short sentence.", "the same in English."),
    "normaal": ("one sentence in Dutch about what is visible.", "the same sentence in English."),
    # A caption for the structured data on Commons (wish Olaf, 6-11-2026): at most 250 characters
    # (Commons:File captions). Asked a little shorter; cut to the limit afterwards if needed.
    "caption": (
        f"a caption in Dutch for Wikimedia Commons: one or two plain sentences about what is shown, as rich as fits (who or what, where, what happens, notable details), at most {CAPTION_ASK} characters, no markup, no links.",
        f"the same caption in English, also at most {CAPTION_ASK} characters.",
    ),
    "uitgebreid": (
        "a paragraph of three to five sentences in Dutch: what is shown, the composition, notable details, colours and style.",
        "the same paragraph in English.",
    ),
}
DEFAULT_DESCRIPTION_LEVEL = "normaal"
# A new description of the whole image is a Commons caption unless asked otherwise (wish Olaf,
# 11-11-2026): rich, but never longer than 250 characters, so it can go to Commons as it is.
PAGE_DEFAULT_DESCRIPTION_LEVEL = "caption"
# All four lengths come in one call (wish Olaf, 11-11-2026): the slider then switches between
# them for free. One field per length and language in the answer.
SUMMARY_FIELDS = tuple(f"samenvatting_{level}{suffix}" for level in DESCRIPTION_LEVELS for suffix in ("", "_en"))
SUMMARY_LINES = "\n".join(f"- samenvatting_{level}: {{rule_{level}}}\n- samenvatting_{level}_en: {{rule_{level}_en}}" for level in DESCRIPTION_LEVELS)
SUMMARY_RULES = {
    **{f"rule_{level}": rule for level, (rule, _) in DESCRIPTION_LEVELS.items()},
    **{f"rule_{level}_en": rule_en for level, (_, rule_en) in DESCRIPTION_LEVELS.items()},
}
SUMMARY_NOTE = "The four samenvatting lengths are separate descriptions of the same image: write each one on its own, do not just cut a longer one."

INVENTORY_SCHEMA = {
    "type": "object",
    "properties": {
        "paginasoort": {"type": "string"},
        "paginasoort_en": {"type": "string"},
        **{field: {"type": "string"} for field in SUMMARY_FIELDS},
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
    "required": ["paginasoort", "paginasoort_en", *SUMMARY_FIELDS, "tekst", "zoektermen"],
    "additionalProperties": False,
}

INVENTORY_INSTRUCTIONS = """You look at one whole image on Wikimedia Commons: {publication}.

List the visual objects in this image (not text), so that an open-vocabulary object detector (SAM) can find them. Answer in JSON:
- paginasoort: the kind of image in Dutch, a few words (e.g. "albumblad met wapens", "prent", "kaart", "pagina uit een getijdenboek").
- paginasoort_en: the same in English.
{summaries}
- tekst: all text you can read in the image, including captions or verses printed under or around the picture, transcribed literally in its own language and spelling, with a newline between separate lines or blocks. Read it carefully; mark a word you cannot read with [?]. Leave it empty when there is no text.
- zoektermen: {terms_rule} For each:
  - en: a short English noun phrase for the detector, singular, 1-3 words, concrete and visual (e.g. "portrait", "coat of arms", "saint", "angel", "decorated initial", "ship", "map", "flower", "ornament").
  - nl: the same in Dutch.
  - aantal: how many you see (an estimate).
  - waar: where in the image, in Dutch (e.g. "linksboven", "onderste helft").
Only list what you can actually see; do not guess. In zoektermen, skip plain text and borders. {summary_note}"""


# The two parts of the overview that can be asked again (or removed) on their own
# (since 0.29.0): the description of the image, and the search terms for SAM.
INVENTORY_PARTS = {
    "beschrijving": ("paginasoort", "paginasoort_en", "samenvatting", "samenvatting_en", "tekst"),
    "zoektermen": ("zoektermen",),
}
# What each part asks the model for: the description asks all four lengths.
INVENTORY_ASK = {
    "beschrijving": ("paginasoort", "paginasoort_en", *SUMMARY_FIELDS, "tekst"),
    "zoektermen": ("zoektermen",),
}
PART_INTRO = {
    "beschrijving": "Describe this image. Answer in JSON:",
    "zoektermen": "List the visual objects in this image (not text), so that an open-vocabulary object detector (SAM) can find them. Answer in JSON:",
}


PART_LOG = {"beschrijving": " – beschrijving opnieuw", "zoektermen": " – zoektermen opnieuw"}


# The description of the image (the "beschrijving" part), and what says how it was made.
PAGE_DESCRIPTION = INVENTORY_PARTS["beschrijving"]
DESCRIPTION_META = ("bewerkt", "bewerkt_op", "ai_origineel")


def page_description_made(overview):
    """Model and time of the AI description: of the part asked anew, else of the overview."""
    overview = overview or {}
    return (overview.get("delen") or {}).get("beschrijving") or overview


def page_description_version(overview):
    """The id of the current description: when it was edited by hand, else made."""
    overview = overview or {}
    return overview.get("bewerkt_op") or page_description_made(overview).get("tijdstempel") or ""


SHOWN = (("nl", "samenvatting"), ("en", "samenvatting_en"))


def sync_description_length(overview):
    """Write the shown summary (with its own AI original) back into its length in
    "beschrijvingen", so each length keeps its hand edits (wish Olaf, 11-11-2026)."""
    lengths, level = overview.get("beschrijvingen"), overview.get("beschrijvingsniveau")
    if not isinstance(lengths, dict) or not lengths or level not in DESCRIPTION_LEVELS:
        return
    original = overview.get("ai_origineel") or {}
    entry = {lang: overview.get(field) or "" for lang, field in SHOWN}
    ai = {lang: original[field] for lang, field in SHOWN if field in original}
    if ai:
        entry["ai_origineel"] = ai
    lengths[level] = entry


def show_description_length(overview, level):
    """Show another length: its text, with its own hand edits and AI original, becomes
    the summary of the overview. Free; the other lengths stay as they are."""
    sync_description_length(overview)
    entry = (overview.get("beschrijvingen") or {}).get(level) or {}
    for lang, field in SHOWN:
        overview[field] = entry.get(lang) or ""
    shown_fields = {field for _, field in SHOWN}
    original = {k: v for k, v in (overview.get("ai_origineel") or {}).items() if k not in shown_fields}
    original.update({field: entry["ai_origineel"][lang] for lang, field in SHOWN if lang in (entry.get("ai_origineel") or {})})
    if original:
        overview["ai_origineel"] = original
    else:
        overview.pop("ai_origineel", None)
    if "bewerkt" in overview or original:
        overview["bewerkt"] = bool(original)
    overview["beschrijvingsniveau"] = level


def page_description_snapshot(overview):
    """The description of the overview as a version for the history: all four lengths."""
    overview = json.loads(json.dumps(overview))
    sync_description_length(overview)
    made = page_description_made(overview)
    snapshot = {k: overview.get(k) or "" for k in PAGE_DESCRIPTION}
    if overview.get("beschrijvingen"):
        snapshot["beschrijvingen"] = overview["beschrijvingen"]
    snapshot.update({"model": made.get("model"), "tijdstempel": made.get("tijdstempel"), "versie": page_description_version(overview)})
    # How long it was asked to be (the Length slider); before the slider every one was "normaal".
    snapshot["beschrijvingsniveau"] = overview.get("beschrijvingsniveau") or DEFAULT_DESCRIPTION_LEVEL
    snapshot.update({k: overview[k] for k in DESCRIPTION_META if overview.get(k)})
    return json.loads(json.dumps(snapshot))


def inventory_schema(part=None):
    """The answer format for the whole overview, or for one part of it."""
    if part is None:
        return INVENTORY_SCHEMA
    keys = INVENTORY_ASK[part]
    return {
        "type": "object",
        "properties": {k: v for k, v in INVENTORY_SCHEMA["properties"].items() if k in keys},
        "required": list(keys),
        "additionalProperties": False,
    }


def inventory_instructions(publication, part=None, detail=DEFAULT_DETAIL):
    """The question for the whole overview, or for one part: the same field
    descriptions as the whole question, so both parts stay alike. `detail`
    (DETAIL_LEVELS) says how many kinds of objects the search terms ask for.
    The description comes in all four lengths (DESCRIPTION_LEVELS) at once."""
    rules = {"terms_rule": DETAIL_LEVELS[detail][1], "summary_note": SUMMARY_NOTE, **SUMMARY_RULES}
    template = INVENTORY_INSTRUCTIONS.replace("{summaries}", SUMMARY_LINES)
    if part is None:
        return template.format(publication=publication, **rules)
    keys, kept, keep = INVENTORY_ASK[part], [], False
    for line in template.splitlines():
        field = re.match(r"- (\w+):", line)
        if field:
            keep = field.group(1) in keys
        elif not line.startswith("  "):
            keep = False
        if keep:
            kept.append(line)
    end = {
        "beschrijving": "Only describe what you can actually see; do not guess. {summary_note}",
        "zoektermen": "Only list what you can actually see; do not guess. In zoektermen, skip plain text and borders.",
    }[part]
    text = f"You look at one whole image on Wikimedia Commons: {{publication}}.\n\n{PART_INTRO[part]}\n" + "\n".join(kept) + "\n" + end
    return text.format(publication=publication, **rules)


def parse_inventory(text, max_terms=MAX_TERMS):
    """The overview from the answer; terms are cleaned, de-duplicated and capped."""
    match = re.search(r"\{.*\}", text or "", re.S)
    try:
        data = json.loads(match.group(0)) if match else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        # Not JSON: "inventory" does not keep this as an answer (it says so and asks to retry).
        return {"paginasoort": "", "paginasoort_en": "", "samenvatting": " ".join((text or "").split())[:300], "samenvatting_en": "", "tekst": "", "zoektermen": [], "onleesbaar": True}
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
        if len(terms) == max_terms:
            break
    clean = lambda key: " ".join(str(data.get(key) or "").split())  # noqa: E731
    lengths = {}
    for level in DESCRIPTION_LEVELS:
        nl, en = clean(f"samenvatting_{level}"), clean(f"samenvatting_{level}_en")
        if level == "caption":  # never longer than Commons allows
            nl, en = cap_caption(nl), cap_caption(en)
        if nl or en:
            lengths[level] = {"nl": nl, "en": en}
    return {
        "paginasoort": clean("paginasoort"),
        "paginasoort_en": clean("paginasoort_en"),
        # The shown length; "inventory" puts the chosen one here (an answer in the old format has it).
        "samenvatting": clean("samenvatting"),
        "samenvatting_en": clean("samenvatting_en"),
        "beschrijvingen": lengths,
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


MAX_OWN_PROMPT = 12000  # characters of a prompt of your own ("What is this?", wish Olaf)
MAX_PROMPT_HISTORY = 20  # earlier prompts of your own kept per object


def clean_own_prompt(text):
    """A prompt of your own: its lines kept (the app's prompt has a structure), trailing
    spaces and empty lines at the ends removed, at most MAX_OWN_PROMPT characters."""
    lines = [line.rstrip() for line in str(text or "").replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip()[:MAX_OWN_PROMPT]


def apply_own_prompt(holder, text, key="prompt_eigen", history_key="prompt_geschiedenis"):
    """Make `text` the prompt of your own on `holder` (an object, or a page store); None or
    "": back to the app's prompt. The one before goes on top of the history, each text once,
    at most MAX_PROMPT_HISTORY."""
    text = clean_own_prompt(text)
    previous = holder.get(key)
    history = [h for h in holder.get(history_key) or [] if h.get("tekst") != text]
    if previous and previous.get("tekst") != text:
        history = [previous] + [h for h in history if h.get("tekst") != previous.get("tekst")]
    if text:
        holder[key] = {"tekst": text, "bewaard_op": datetime.now(timezone.utc).isoformat(timespec="milliseconds")}
    else:
        holder.pop(key, None)
    holder[history_key] = history[:MAX_PROMPT_HISTORY]


# Your own prompt for asking a part of the page overview anew (wish Olaf 13-11-2026): the
# description and the search terms each have one, kept in the page store under these keys
# (your prompt, your earlier ones).
PAGE_PROMPT_KEYS = {
    "beschrijving": ("inventaris_prompt_eigen", "inventaris_prompt_geschiedenis"),
    "zoektermen": ("zoektermen_prompt_eigen", "zoektermen_prompt_geschiedenis"),
}


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
    return encode(crop, "JPEG", quality=88), crop.size


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


# How long the description of one object is (the Length slider in the AI modifiers, wish
# Olaf 6-11-2026): the same stops as for the whole image. "normaal" keeps the question as it
# was, so earlier answers stay in the cache.
OBJECT_DESCRIPTION_LEVELS = {
    "kort": ("a few words in Dutch: what the object is, at most one short sentence.", "the same in English."),
    "normaal": ("one or two sentences in Dutch describing what is shown.", "the same in English."),
    "caption": None,  # filled in below: the Commons caption rule of DESCRIPTION_LEVELS
    "uitgebreid": (
        "a paragraph of three to five sentences in Dutch: what is shown, notable details, colours and style.",
        "the same paragraph in English.",
    ),
}


OBJECT_DESCRIPTION_LEVELS["caption"] = DESCRIPTION_LEVELS["caption"]


def build_prompt(file, caption=None, hint=None, page_text=None, group=None, members_context=None, surroundings=False, description_level=DEFAULT_DESCRIPTION_LEVEL, clue=""):
    caption = " ".join((caption or "").split())[:CONTEXT_CHARS]
    rule, rule_en = OBJECT_DESCRIPTION_LEVELS.get(description_level) or OBJECT_DESCRIPTION_LEVELS[DEFAULT_DESCRIPTION_LEVEL]
    prompt = INSTRUCTIONS.format(
        description_rule=rule,
        description_rule_en=rule_en,
        kinds=", ".join(KINDS),
        max_suggestions=MAX_SUGGESTIONS,
        title=f'"{file.get("naam") or file.get("titel")}"',
        cutout_caption=f'"{caption}"' if caption else "none",
        **context(file),
    )
    prompt += clue or ""  # what the app already knows about this object (detection_clue)
    # The markers that frame the text cannot occur in it (a text that "closes" its own block).
    page_text = (page_text or "").replace("<<<", "").replace(">>>", "").strip()[:MAX_PAGE_TEXT]
    if page_text:
        prompt += PAGE_TEXT_INSTRUCTION.format(text=page_text)
    if group:
        prompt += (GROUP_INSTRUCTION_CONTEXT if surroundings else GROUP_INSTRUCTION).format(members=group)
        if members_context:
            prompt += GROUP_CONTEXT_INSTRUCTION.format(lines=members_context)
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


# The text of a Responses API answer: the same for SAM and Muse Spark (meta_sam.py).
output_text = extract_output_text


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
        # Capped: an answer can never be longer than a field reasonably is (MAX_FIELD).
        result[key] = " ".join(value.split())[:MAX_FIELD] if isinstance(value, str) and value.strip() else None
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
    """(input, output, reasoning) tokens; reasoning is part of output. A count that is no
    whole number of at least 0 (a string, NaN, a negative) is None: the cost is then estimated."""
    usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
    details = usage.get("output_tokens_details") if isinstance(usage.get("output_tokens_details"), dict) else {}

    def count(value):
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None

    input_tokens, output_tokens = count(usage.get("input_tokens")), count(usage.get("output_tokens"))
    if output_tokens is None:
        input_tokens = None  # half a count gives half a price: estimate instead
    return input_tokens, output_tokens, count(details.get("reasoning_tokens"))


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DummyVision:
    """Free stand-in for development (DETECTIE_MODUS=dummy): a fixed answer
    built from the object's label, so the whole flow can be tried."""

    betaald = False

    def describe(self, model, prompt, data_url, obj, effort=None, schema=SCHEMA):
        if "zoektermen" in schema.get("properties", {}) or "paginasoort" in schema.get("properties", {}):
            lengths = {
                "kort": ("Voorbeeld (dummy).", "Example (dummy)."),
                "normaal": ("Voorbeeldoverzicht (dummy, geen echt model).", "Example overview (dummy, no real model)."),
                "caption": ("Voorbeeldbijschrift voor Commons (dummy, geen echt model): wat er op de afbeelding te zien is.", "Example caption for Commons (dummy, no real model): what the image shows."),
                "uitgebreid": (
                    "Een uitgebreide voorbeeldbeschrijving (dummy, geen echt model). Ze noemt wat er te zien is, de compositie en opvallende details. Zo kun je de schuif uitproberen.",
                    "An extensive example description (dummy, no real model). It names what is shown, the composition and notable details. So you can try the slider.",
                ),
            }
            answer = {
                "paginasoort": "voorbeeldafbeelding (dummy)",
                "paginasoort_en": "example image (dummy)",
                **{f"samenvatting_{level}": nl for level, (nl, _) in lengths.items()},
                **{f"samenvatting_{level}_en": en for level, (_, en) in lengths.items()},
                "tekst": "Voorbeeldtekst onder de afbeelding (dummy).",
                "zoektermen": [
                    {"en": "coat of arms", "nl": "wapen", "aantal": 2, "waar": "bovenaan"},
                    {"en": "portrait", "nl": "portret", "aantal": 1, "waar": "midden"},
                    {"en": "decorated initial", "nl": "initiaal", "aantal": 1, "waar": "linksboven"},
                ],
            }
            if "small details" in prompt:  # the slider at "details": more terms, to try it
                answer["zoektermen"] += [
                    {"en": en, "nl": nl, "aantal": 1, "waar": "verspreid"}
                    for en, nl in (("flower", "bloem"), ("bird", "vogel"), ("ornament", "ornament"), ("insect", "insect"), ("button", "knoop"))
                ]
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
        self.client = MetaClient(api_key, base_url, timeout, session)

    @property
    def session(self):
        return self.client.session

    def describe(self, model, prompt, data_url, obj, effort=None, schema=SCHEMA):
        return self.client.post_json(
            "/responses",
            build_request(model, prompt, data_url, effort, schema, "beschrijving" if schema is SCHEMA else "pagina"),
            model,
            "Geen MODEL_API_KEY ingesteld; een beschrijving is niet mogelijk.",
            no_key_code="no_api_key",
            # Never fall back to the more expensive model silently.
            busy=f"Te veel verzoeken aan '{model}'; probeer het zo opnieuw, of kies Standard.",
        )


def make_vision(config):
    if config["DETECTIE_MODUS"] == "live":
        return MetaVision(config["MODEL_API_KEY"], base_url=config["META_API_BASE"])
    return DummyVision()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def effort_of(config):
    """The configured reasoning effort (BEELDMODEL_REDENEREN), or None when it is not one of EFFORTS."""
    effort = config.get("BEELDMODEL_REDENEREN")
    return effort if effort in EFFORTS else None


def _apply_hand_edit(target, changes):
    """Write hand-edited fields (already stripped) into `target` (a description or a
    page overview), keeping what the AI said under "ai_origineel" while a field
    differs from it, and mark the version as edited ("bewerkt", "bewerkt_op")."""
    original = target.setdefault("ai_origineel", {})
    for field, value in changes.items():
        if field not in original:
            original[field] = target.get(field) or ""
        target[field] = value
        if value == original[field]:
            original.pop(field)
    if not original:
        target.pop("ai_origineel")
    target["bewerkt"] = bool(original)
    target["bewerkt_op"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")  # unique per version


class DescriptionService:
    """Describe objects of the detection service and store the result on the
    object (`beschrijving`), cached per file SHA-1, object box, model and
    prompt version."""

    def __init__(self, vision, objects, config, cache_dir):
        self.vision = vision
        self.objects = objects  # DetectionService: object store, Commons client, usage
        self.config = config
        self.cache_dir = Path(cache_dir) / "beschrijvingen"
        self._combos = None  # (time, {(hint, margin)}) — see _asked_combinations

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
        return effort_of(self.config)

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
        return sharded(self.cache_dir, hashlib.sha1(key.encode()).hexdigest(), ".json")

    def _source_image(self, file, n):
        """The page image to crop from: the original when it can be used,
        otherwise the largest standard rendering."""
        client = self.objects.client
        if file.get("uitsnijden_mogelijk"):
            return client.original_image(file, n)
        return open_image(client.page_image(file, n, 3840))

    def model_preview(self, file, n, object_id, margin=None, max_side=None):
        """JPEG of what the model would see with this margin, the box outlined
        in red. `max_side` (up to MAX_PREVIEW_SIDE) gives a larger version, to
        read and check the text in the image. Free: nothing is sent to the model."""
        obj = self.objects._find(file, n, object_id)
        side = max(MAX_SIDE, min(int(max_side or MAX_SIDE), MAX_PREVIEW_SIDE))
        margin = clean_margin(margin)
        # Made once per box, margin and size, then from the cache (cleaned up with the cut-outs).
        key = hashlib.sha1(f"{file['sha1']}|{n}|{obj['box']}|{margin}|{side}|invoer".encode()).hexdigest()

        def make():
            page = self.objects.client.load_page(file, n)
            return model_input(self._source_image(file, n), page["breedte"], obj["box"], margin, side, outline=True)[0]

        return cached_bytes(sharded(self.cache_dir.parent / "uitsneden", key, ".jpg"), make)

    def _question(self, file, n, obj, hint, margin, group_focus, description_level):
        """The parts of the question about an object: the prompt as it goes to the model,
        and what goes into the cache key. Checks the description level."""
        if description_level is None:
            description_level = (obj.get("beschrijving") or {}).get("beschrijvingsniveau") or DEFAULT_DESCRIPTION_LEVEL
        if description_level not in OBJECT_DESCRIPTION_LEVELS:
            raise DetectionError(f"Onbekend beschrijvingsniveau '{description_level}'; kies uit {', '.join(OBJECT_DESCRIPTION_LEVELS)}.", status=400, code="invalid_body")
        # The text read in the whole image (page overview) goes along as context.
        page_text = self._page_text(file, n)
        # A group: the instruction to look at its members only, unless switched off ("Only these
        # objects"); with space around it, the surroundings may serve as context (7.4).
        group = group_members(obj) if group_focus else ""
        members_context = group_context(obj) if group else ""
        surroundings = bool(group) and margin > 0
        clue, clue_source = detection_clue(obj)
        standard = build_prompt(file, self._caption(obj), hint, page_text, group, members_context, surroundings, description_level, clue)
        own = ((obj.get("prompt_eigen") or {}).get("tekst") or "").strip()
        prompt = (own + HINT_INSTRUCTION.format(hint=hint) if hint else own) if own else standard
        return {
            "prompt": prompt,
            "standard": standard,
            "own": own,
            "clue": "" if own else clue,
            "clue_source": None if own else clue_source,
            "beschrijvingsniveau": description_level,
            "page_text": page_text,
            "group": group,
            "members_context": members_context,
            "surroundings": surroundings,
        }

    def prompt_preview(self, file, n, object_id, hint=None, margin=None, group_focus=True, description_level=None):
        """The prompt a question about this object would send, with these settings (the image
        goes along separately). Free: nothing is sent to the model."""
        obj = self.objects._find(file, n, object_id)
        question = self._question(file, n, obj, clean_hint(hint), clean_margin(margin), group_focus, description_level)
        return {
            "prompt": question["prompt"],
            # The app's own prompt for these settings, and the one you wrote (null: none).
            "standaard_prompt": question["standard"],
            "eigen": bool(question["own"]),
            "eigen_prompt": obj.get("prompt_eigen"),
            "geschiedenis": obj.get("prompt_geschiedenis") or [],
            "beschrijvingsniveau": question["beschrijvingsniveau"],
            "marge": clean_margin(margin),
            "aanwijzing": clean_hint(hint) or None,
        }

    def _set_own_prompt(self, file, n, object_id, text):
        """Make `text` the prompt of your own (None or "": back to the app's prompt); the
        one before goes on top of the history, each text once, at most MAX_PROMPT_HISTORY."""
        with self.objects.editing(file, n, object_id) as (_store, obj):
            apply_own_prompt(obj, text)

    def save_prompt(self, file, n, object_id, text):
        """Your own prompt for this object (free; nothing goes to the model)."""
        self.objects._find(file, n, object_id)
        if not isinstance(text, str) or not text.strip():
            raise DetectionError("Geef een 'prompt' (tekst); terug naar de prompt van de app gaat met DELETE.", status=400, code="invalid_body")
        self._set_own_prompt(file, n, object_id, text)

    def reset_prompt(self, file, n, object_id):
        """Back to the app's prompt; yours goes to the history (free)."""
        self.objects._find(file, n, object_id)
        self._set_own_prompt(file, n, object_id, None)

    def forget_prompt_version(self, file, n, object_id, version):
        """Remove an earlier prompt from the history; `version` is its "bewaard_op" (free)."""
        obj = self.objects._find(file, n, object_id)
        if not any(h.get("bewaard_op") == version for h in obj.get("prompt_geschiedenis") or []):
            raise DetectionError("Deze eerdere prompt bestaat niet (meer).", status=404, code="not_found")
        with self.objects.editing(file, n, object_id) as (_store, obj):
            obj["prompt_geschiedenis"] = [h for h in obj.get("prompt_geschiedenis") or [] if h.get("bewaard_op") != version]

    def _booking(self, user, model, effort, input_tokens=None):
        """A paid call books its estimated cost while it runs (Verbruik.reservation):
        parallel requests cannot together pass the daily limit or budget."""
        if not self.vision.betaald:
            return nullcontext()
        return self.objects.verbruik.reservation(1, user=user, cost=estimate(model, effort, input_tokens))

    def _tokens_and_cost(self, body, model, effort, input_tokens=None):
        """The tokens of an answer and what it cost: by the tokens, or else the estimate (free: 0)."""
        tokens_in, tokens_out, tokens_reasoning = usage_tokens(body)
        if not self.vision.betaald:
            amount = 0.0
        elif tokens_in is not None:
            amount = cost(model, tokens_in, tokens_out)
        else:
            amount = estimate(model, effort, input_tokens)
        return {"invoer": tokens_in, "uitvoer": tokens_out, "waarvan_redeneren": tokens_reasoning}, amount

    def describe(self, file, n, object_id, model=None, again=False, user=None, hint=None, margin=None, group_focus=True, description_level=None):
        """Describe an object (paid in live mode) and store the answer on it.
        `hint` is an extra instruction from the user for this question;
        `margin` the share of the box shown around it (default MARGIN)."""
        obj = self.objects._find(file, n, object_id)
        choice = self._model(file, model)
        hint = clean_hint(hint)
        margin = clean_margin(margin)
        # The length of the description (the slider): without one, what the last answer used.
        question = self._question(file, n, obj, hint, margin, group_focus, description_level)
        description_level = question["beschrijvingsniveau"]
        page_text, group, members_context, surroundings = question["page_text"], question["group"], question["members_context"], question["surroundings"]
        # The members (and what they were described as) go into the cache key too: an answer
        # from before the group instruction, or from before a member was described, is not reused.
        key_hint = hint + (f"|groep: {group}" + ("|omgeving" if surroundings else "") if group else "") + (f"|context: {hashlib.sha1(members_context.encode()).hexdigest()[:12]}" if members_context else "")
        if description_level != DEFAULT_DESCRIPTION_LEVEL:  # "normaal" keeps the key from before the slider
            key_hint += f"|beschrijving={description_level}"
        if question["clue"]:  # the clue (name, label or search term) is part of the question
            key_hint += f"|aanwijzing detectie: {hashlib.sha1(question['clue'].encode()).hexdigest()[:12]}"
        if question["own"]:  # another prompt is another question
            key_hint += f"|eigen prompt: {hashlib.sha1(question['own'].encode()).hexdigest()[:12]}"
        path = self._cache_path(file, n, obj, choice["model"], key_hint, margin, page_text)
        # A saved answer that went meanwhile, or is unreadable (kept aside), counts as none.
        description = read_json(path, None, valid=_is_dict) if self.objects.counts_for_file(file, path) and not again else None
        if description is not None:
            mark_used(path)
            description["uit_cache"] = True
            return self._store(file, n, object_id, description, user)

        effort = self._effort()
        with self._booking(user, choice["model"], effort):
            page = self.objects.client.load_page(file, n)
            data_url, size = crop_with_margin(self._source_image(file, n), page["breedte"], obj["box"], margin)
            prompt = question["prompt"]

            body = self.vision.describe(choice["model"], prompt, data_url, self.objects.public(file, n, obj), effort)
            tokens, amount = self._tokens_and_cost(body, choice["model"], effort)
            answer = parse_answer(output_text(body))
            if description_level == "caption":  # never longer than a caption on Commons may be
                for key in ("beschrijving", "beschrijving_en"):
                    if answer.get(key):
                        answer[key] = cap_caption(answer[key])
            description = {
                **answer,
                "beschrijvingsniveau": description_level,
                "model": choice["model"],
                "model_reden": choice["reden"],
                "model_reden_code": choice["reden_code"],
                "model_reden_labels": choice["labels"],
                "rechtenvrij": choice["rechtenvrij"],
                "redeneren": effort,
                "tokens": tokens,
                "kosten_usd": amount,
                "verstuurde_afmetingen": list(size),
                "promptversie": PROMPT_VERSION,
                "aanwijzing": hint or None,
                "prompt_eigen": bool(question["own"]),  # asked with a prompt of your own
                "detectie_aanwijzing": question["clue_source"],  # naam, commons, zoekterm or None
                "alleen_naar": group or None,  # a group: the AI was asked to look at its members only
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
        write_json(path, description)
        description["uit_cache"] = False
        return self._store(file, n, object_id, description, user)

    # -- History of descriptions ------------------------------------------------

    @staticmethod
    def _same(a, b):
        """Whether two descriptions are the same version (same answer, question, edit and texts)."""
        keys = ("tijdstempel", "bewerkt_op", "aanwijzing", "marge", "paginatekst", *EDITABLE)
        return all((a or {}).get(k) == (b or {}).get(k) for k in keys)

    @staticmethod
    def version(description):
        """The id of a version: when it was made, by the AI (tijdstempel) or by hand (bewerkt_op)."""
        return (description or {}).get("bewerkt_op") or (description or {}).get("tijdstempel") or ""

    def _keep_in_history(self, obj):
        """Put the current description on top of the object's history (not twice)."""
        current = obj.get("beschrijving")
        if not current:
            return
        history = [h for h in obj.get("beschrijving_geschiedenis", []) if not self._same(h, current)]
        obj["beschrijving_geschiedenis"] = [current, *history][:MAX_HISTORY]

    def _asked_combinations(self):
        """Every (hint, margin) asked so far, from the description cache. Read
        once a minute at most: the cache can hold thousands of answers."""
        now = time.monotonic()
        if self._combos is None or now - self._combos[0] > 60:
            combos = set()
            for path in self.cache_dir.glob("*/*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if "beschrijving" in data:
                    combos.add((data.get("aanwijzing") or "", clean_margin(data.get("marge"))))
            self._combos = (now, combos)
        return set(self._combos[1])

    def _cached_variants(self, file, n, obj):
        """Answers for this object that are still in the cache: one per
        combination of model, hint and margin asked so far. So descriptions
        from before the history existed can be chosen again too."""
        combos = {("", MARGIN)} | self._asked_combinations()
        models = dict.fromkeys([self.config["BEELDMODEL"], self.config["BEELDMODEL_RECHTENVRIJ"]])
        page_texts = dict.fromkeys(["", self._page_text(file, n)])
        found = []
        for model in models:
            for (hint, margin), page_text in ((c, p) for c in combos for p in page_texts):
                path = self._cache_path(file, n, obj, model, hint, margin, page_text)
                if self.objects.counts_for_file(file, path):
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
        entries = [e for e in entries if not (current and self._same(e, current))]
        # Versions the user deleted stay away, also when the answer is still in the cache.
        hidden = set(obj.get("beschrijving_verborgen", []))
        entries = [e for e in entries if self.version(e) not in hidden]
        # Every version, by the AI or by hand, with its own id ("versie"), newest first.
        return sorted(({**e, "versie": self.version(e)} for e in entries), key=lambda e: e["versie"], reverse=True)

    def forget_version(self, file, n, object_id, version):
        """Delete one earlier version from the history. An AI answer still in the
        cache is hidden for this object (the cache itself is shared and stays).
        The current description cannot be deleted this way. Free."""
        if not any(e["versie"] == version for e in self.history(file, n, object_id)):
            raise DetectionError("Die eerdere versie bestaat niet (meer).", status=404, code="not_found")
        with self.objects.editing(file, n, object_id) as (_store, obj):
            obj["beschrijving_geschiedenis"] = [h for h in obj.get("beschrijving_geschiedenis", []) if self.version(h) != version]
            hidden = obj.setdefault("beschrijving_verborgen", [])
            if version not in hidden:
                hidden.append(version)
            del hidden[:-200]  # the most recent 200 are plenty
        return self.history(file, n, object_id)

    def restore(self, file, n, object_id, timestamp=None, edited=None, version=None):
        """Make an earlier version the current one again: by its `version` (see
        version()), or by its tijdstempel (`edited` picks the hand-edited or the
        AI version when both exist). The current one goes into the history. Free."""
        entries = self.history(file, n, object_id)
        if version:
            candidates = [e for e in entries if e["versie"] == version]
        else:
            candidates = [e for e in entries if e.get("tijdstempel") == timestamp]
            if edited is not None:
                candidates = [e for e in candidates if bool(e.get("bewerkt")) == bool(edited)] or candidates
        if not candidates:
            raise DetectionError("Die eerdere beschrijving bestaat niet (meer).", status=404, code="not_found")
        chosen = candidates[0]
        with self.objects.editing(file, n, object_id) as (_store, obj):
            self._keep_in_history(obj)
            chosen = {k: v for k, v in chosen.items() if k != "versie"}
            obj["beschrijving_geschiedenis"] = [h for h in obj.get("beschrijving_geschiedenis", []) if not self._same(h, chosen)]
            obj["beschrijving"] = chosen
        return self.objects.public(file, n, obj)

    def _store(self, file, n, object_id, description, user=None):
        with self.objects.editing(file, n, object_id) as (_store, obj):
            new = {k: v for k, v in description.items() if k != "uit_cache"}
            if not self._same(obj.get("beschrijving"), new):
                self._keep_in_history(obj)
            obj["beschrijving"] = new
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
            if all((description.get(field) or "") == value.strip() for field, value in changes.items()):
                return self.objects.public(file, n, obj)  # nothing changes: no new version
            # Version history: the version as it was goes into the history first, so
            # a hand edit can be undone later, like an AI answer (Eerdere beschrijvingen).
            self._keep_in_history(obj)
            obj["beschrijving_geschiedenis"][0] = json.loads(json.dumps(obj["beschrijving_geschiedenis"][0]))
            description = obj["beschrijving"] = json.loads(json.dumps(description))
            _apply_hand_edit(description, {field: value.strip() for field, value in changes.items()})
            self.objects._write_store(file, n, store)
        return self.objects.public(file, n, obj)

    def remove(self, file, n, object_id):
        """Forget the stored description (the cached answer stays, so asking
        again with the same model is free)."""
        with self.objects.editing(file, n, object_id) as (_store, obj):
            self._keep_in_history(obj)  # removed, but it can be chosen again
            obj.pop("beschrijving", None)
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
            # What asking a part anew costs per reasoning effort you may choose (wish Olaf).
            "kosten_per_redeneren": {e: (estimate(choice["model"], e, ESTIMATE_PAGE_INPUT) if paid else 0.0) for e in CHOSEN_EFFORTS},
            "budget": self.objects.verbruik.status(user),
        }

    def _inventory_cache_path(self, file, n, model, part=None, detail=DEFAULT_DETAIL):
        key = f"pagina|{file['sha1']}|{n}|{model}|{self._effort()}|{INVENTORY_VERSION}" + (f"|{part}" if part else "")
        # Each detail level has its own answer; "normaal" keeps the key from before the slider.
        if detail != DEFAULT_DETAIL and part != "beschrijving":
            key += f"|detail={detail}"
        # Since 0.39.0 the description comes in all four lengths: an answer of its own.
        if part != "zoektermen":
            key += "|lengtes"
        return sharded(self.cache_dir, hashlib.sha1(key.encode()).hexdigest(), ".json")

    def inventory(self, file, n, model=None, again=False, user=None, part=None, detail=None, description_level=None, hint=None, effort=None):
        """Ask the model what is on the whole page (paid in live mode, cached)
        and keep the overview in the page's store ("inventaris"). With `part`
        ("beschrijving" or "zoektermen") only that part is asked anew, always a
        new answer; the other part of the stored overview stays as it is.
        `detail` (DETAIL_LEVELS) sets how many kinds of objects the search
        terms ask for; without it, the level of the stored overview.
        Asking a part anew may also take a `hint` (an extra instruction, added at the end of the
        prompt) and an `effort` (CHOSEN_EFFORTS; else the configured one), wish Olaf 13-11-2026."""
        hint = clean_hint(hint) if part is not None else ""
        if effort is not None and (part is None or effort not in CHOSEN_EFFORTS):
            raise DetectionError(f"Onbekend redeneerniveau '{effort}'; kies uit {', '.join(CHOSEN_EFFORTS)} (alleen bij één deel).", status=400, code="invalid_body")
        if part is not None and part not in INVENTORY_PARTS:
            raise DetectionError(f"Onbekend deel '{part}'; kies uit {', '.join(INVENTORY_PARTS)}.", status=404, code="not_found")
        if detail is None:
            detail = (self.objects._load_store(file, n).get("inventaris") or {}).get("detailniveau") or DEFAULT_DETAIL
        if detail not in DETAIL_LEVELS:
            raise DetectionError(f"Onbekend detailniveau '{detail}'; kies uit {', '.join(DETAIL_LEVELS)}.", status=400, code="invalid_body")
        if description_level is None:
            description_level = (self.objects._load_store(file, n).get("inventaris") or {}).get("beschrijvingsniveau") or PAGE_DEFAULT_DESCRIPTION_LEVEL
        if description_level not in DESCRIPTION_LEVELS:
            raise DetectionError(f"Onbekend beschrijvingsniveau '{description_level}'; kies uit {', '.join(DESCRIPTION_LEVELS)}.", status=400, code="invalid_body")
        choice = self._model(file, model)
        path = self._inventory_cache_path(file, n, choice["model"], part, detail)
        # Asking a part anew may go with a prompt of your own (wish Olaf 13-11-2026).
        own = self._own_page_prompt(file, n, part) if part in PAGE_PROMPT_KEYS else ""
        overview = read_json(path, None, valid=_is_dict) if self.objects.counts_for_file(file, path) and not again and part is None else None
        if overview is not None:
            mark_used(path)
            if (overview.get("beschrijvingen") or {}).get(description_level):
                show_description_length(overview, description_level)
            return self._store_inventory(file, n, overview, cached=True, user=user)

        effort = effort or self._effort()
        with self._booking(user, choice["model"], effort, ESTIMATE_PAGE_INPUT):
            image = open_image(self.objects.client.page_image(file, n, PAGE_WIDTH)).convert("RGB")
            if image.width > PAGE_WIDTH:
                image = image.resize((PAGE_WIDTH, round(image.height * PAGE_WIDTH / image.width)))
            data_url = "data:image/jpeg;base64," + base64.b64encode(encode(image, "JPEG", quality=85)).decode("ascii")
            prompt = own or self._inventory_prompt(file, n, part, detail)
            if hint:
                prompt += HINT_INSTRUCTION.format(hint=hint)

            body = self.vision.describe(choice["model"], prompt, data_url, None, effort, schema=inventory_schema(part))
            tokens, amount = self._tokens_and_cost(body, choice["model"], effort, ESTIMATE_PAGE_INPUT)
            parsed = parse_inventory(output_text(body), DETAIL_LEVELS[detail][0])
            # An answer that is not JSON, or a description without any text, is no answer: the
            # call is booked (it was made), but nothing is stored or cached, so asking again
            # really asks again instead of bringing back the broken answer for free.
            unreadable = parsed.pop("onleesbaar", False) or (
                part != "zoektermen" and not parsed.get("beschrijvingen") and not parsed.get("samenvatting") and not parsed.get("samenvatting_en")
            )
            if part is not None:
                keys = (*INVENTORY_PARTS[part], *(("beschrijvingen",) if part == "beschrijving" else ()))
                parsed = {k: parsed[k] for k in keys}
            if part != "beschrijving":
                parsed["detailniveau"] = detail
            if part != "zoektermen":
                lengths = parsed.get("beschrijvingen") or {}
                if lengths:  # show the chosen length, or else the first one there is
                    level = description_level if description_level in lengths else next(iter(lengths))
                    show_description_length(parsed, level)  # nothing shown yet, so nothing to keep
                else:
                    parsed["beschrijvingsniveau"] = description_level
            overview = {
                **parsed,
                **({"prompt_eigen": True} if own else {}),  # asked with a prompt of your own
                **({"aanwijzing": hint} if hint else {}),
                "model": choice["model"],
                "model_reden": choice["reden"],
                "redeneren": effort,
                "tokens": tokens,
                "kosten_usd": amount,
                "verstuurde_afmetingen": list(image.size),
                "versie": INVENTORY_VERSION,
                "tijdstempel": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "appversie": __version__,
            }
            if self.vision.betaald:
                self.objects.verbruik.register(
                    {
                        "soort": "inventaris",
                        "bestand": file["mid"],
                        "titel": file["titel"],
                        "pagina": n,
                        "term": f"Wat staat op deze pagina?{PART_LOG.get(part, '')} ({choice['model']})",
                        "deel": part,
                        "model": choice["model"],
                        "redeneren": effort,
                        "tokens": overview["tokens"],
                    },
                    cost=amount,
                    user=user,
                )
        if unreadable:
            raise DetectionError(
                "Het antwoord van de AI was onleesbaar of zonder beschrijving; er is niets bewaard. Probeer het opnieuw.",
                status=502,
                retry=True,
                code="unreadable_answer",
            )
        write_json(path, overview)
        if part is not None:
            return self._store_inventory_part(file, n, part, overview, user=user)
        return self._store_inventory(file, n, overview, cached=False, user=user)

    def _inventory_prompt(self, file, n, part=None, detail=DEFAULT_DETAIL):
        """The app's prompt for the overview, or for one part: the question, and what people
        already put on Commons (backlog 26)."""
        publication = f'"{file.get("naam")}"' + (f", page {n}" if file.get("paginas", 1) > 1 else "")
        prompt = inventory_instructions(publication, part, detail)
        known = commons_context(file)
        if known:
            prompt += COMMONS_CONTEXT_INSTRUCTION.format(context=known)
        return prompt

    # -- Your own prompt for asking the description or the search terms anew (wish Olaf 13-11-2026) --
    # Like "What is this?" for an object: you change the app's prompt, the next "anew" of that
    # part uses it, and your earlier prompts are kept. The answer format (the fields) stays the
    # app's, so the answer still fits. Kept in the page store, so "Start over" removes it.

    @staticmethod
    def _prompt_keys(part):
        if part not in PAGE_PROMPT_KEYS:
            raise DetectionError(f"Onbekend deel '{part}'; kies uit {', '.join(PAGE_PROMPT_KEYS)}.", status=404, code="not_found")
        return PAGE_PROMPT_KEYS[part]

    def _own_page_prompt(self, file, n, part="beschrijving"):
        own = self.objects._load_store(file, n).get(self._prompt_keys(part)[0]) or {}
        return (own.get("tekst") or "").strip()

    def page_prompt_preview(self, file, n, part="beschrijving", detail=None):
        """The prompt asking this part anew would send for the whole image (the image goes along
        separately), the app's own, yours and your earlier ones. For the search terms the app's
        prompt follows `detail` (else the level of the stored overview). Free."""
        key, history_key = self._prompt_keys(part)
        store = self.objects._load_store(file, n)
        if part == "zoektermen":
            detail = detail or (store.get("inventaris") or {}).get("detailniveau") or DEFAULT_DETAIL
            if detail not in DETAIL_LEVELS:
                raise DetectionError(f"Onbekend detailniveau '{detail}'; kies uit {', '.join(DETAIL_LEVELS)}.", status=400, code="invalid_body")
        standard = self._inventory_prompt(file, n, part, detail or DEFAULT_DETAIL)
        own = self._own_page_prompt(file, n, part)
        return {
            "deel": part,
            "prompt": own or standard,
            "standaard_prompt": standard,
            "eigen": bool(own),
            "eigen_prompt": store.get(key),
            "geschiedenis": store.get(history_key) or [],
            **({"detailniveau": detail} if part == "zoektermen" else {}),
        }

    def _set_page_prompt(self, file, n, part, text):
        key, history_key = self._prompt_keys(part)
        with self.objects.editing_store(file, n) as store:
            apply_own_prompt(store, text, key, history_key)
        return self.page_prompt_preview(file, n, part)

    def save_page_prompt(self, file, n, text, part="beschrijving"):
        """Your own prompt for asking this part anew (free)."""
        self._prompt_keys(part)
        if not isinstance(text, str) or not text.strip():
            raise DetectionError("Geef een 'prompt' (tekst); terug naar de prompt van de app gaat met DELETE.", status=400, code="invalid_body")
        return self._set_page_prompt(file, n, part, text)

    def reset_page_prompt(self, file, n, part="beschrijving"):
        """Back to the app's prompt; yours goes to the history (free)."""
        return self._set_page_prompt(file, n, part, None)

    def forget_page_prompt_version(self, file, n, version, part="beschrijving"):
        """Remove an earlier prompt from the history; `version` is its "bewaard_op" (free)."""
        _key, history_key = self._prompt_keys(part)
        with self.objects.editing_store(file, n) as store:
            history = store.get(history_key) or []
            if not any(h.get("bewaard_op") == version for h in history):
                raise DetectionError("Deze eerdere prompt bestaat niet (meer).", status=404, code="not_found")
            store[history_key] = [h for h in history if h.get("bewaard_op") != version]
        return self.page_prompt_preview(file, n, part)

    def forget_inventory(self, file, n, part=None):
        """Remove the page overview from the page, or one part of it: the
        description ("beschrijving": kind, summary and the text read in and under
        the image, which then no longer goes along as context for "Wat staat
        hierop?") or the search terms ("zoektermen"). Without parts left, the
        overview goes entirely. The cached answer stays, so asking "Wat staat op
        deze pagina?" again brings the first answer back for free. Objects found
        with its terms stay. Free."""
        if part is not None and part not in INVENTORY_PARTS:
            raise DetectionError(f"Onbekend deel '{part}'; kies uit {', '.join(INVENTORY_PARTS)}.", status=404, code="not_found")
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            overview = store.get("inventaris")
            if not overview:
                return {"verwijderd": False, "inventaris": None}
            if part in (None, "beschrijving"):
                self._keep_page_description(store)
            if part is None:
                store.pop("inventaris")
            else:
                if part == "beschrijving":
                    for key in (*DESCRIPTION_META, "beschrijvingen"):
                        overview.pop(key, None)
                for key in INVENTORY_PARTS[part]:
                    overview[key] = [] if key == "zoektermen" else ""
                (overview.get("delen") or {}).pop(part, None)
                if not any(overview.get(key) for keys in INVENTORY_PARTS.values() for key in keys):
                    store.pop("inventaris")
            self.objects._write_store(file, n, store)
        return {"verwijderd": True, "inventaris": store.get("inventaris")}

    def _store_inventory_part(self, file, n, part, answer, user=None):
        """Put one newly asked part into the stored overview; the other part
        stays. When and how each part was asked anew is under "delen"."""
        fields = {k: answer[k] for k in INVENTORY_PARTS[part]}
        if part == "beschrijving":
            fields["beschrijvingen"] = answer.get("beschrijvingen") or {}
        meta = {k: v for k, v in answer.items() if k not in fields}
        own_prompt = meta.pop("prompt_eigen", False)  # kept per part, under "delen"
        part_hint = meta.pop("aanwijzing", "")
        with self.objects.editing_store(file, n) as store:
            current = dict(store.get("inventaris") or {})
            if part == "beschrijving":
                self._keep_page_description(store)
                for key in DESCRIPTION_META:  # a new AI description: no hand edits on top
                    current.pop(key, None)
            empty = {k: [] if k == "zoektermen" else "" for keys in INVENTORY_PARTS.values() for k in keys}
            overview = {**empty, **meta, **current, **fields}
            overview.pop("prompt_eigen", None)
            overview.pop("aanwijzing", None)
            overview["delen"] = {**(overview.get("delen") or {}), part: {**meta, **({"prompt_eigen": True} if own_prompt else {}), **({"aanwijzing": part_hint} if part_hint else {})}}
            if "detailniveau" in answer:  # the search terms asked anew at another level
                overview["detailniveau"] = answer["detailniveau"]
            if "beschrijvingsniveau" in answer:  # the description asked anew at another length
                overview["beschrijvingsniveau"] = answer["beschrijvingsniveau"]
            store["inventaris"] = overview
        return {"inventaris": overview, "uit_cache": False, "budget": self.objects.verbruik.status(user)}

    def _store_inventory(self, file, n, overview, cached, user=None):
        with self.objects.editing_store(file, n) as store:
            if page_description_version(store.get("inventaris")) != page_description_version(overview):
                self._keep_page_description(store)
            store["inventaris"] = overview
        return {"inventaris": overview, "uit_cache": cached, "budget": self.objects.verbruik.status(user)}

    # -- The description of the whole image: by hand, and its earlier versions --

    def _keep_page_description(self, store):
        """Put the current description of the page overview into its history
        ("inventaris_geschiedenis", newest first, at most 30), once per version."""
        overview = store.get("inventaris") or {}
        if not any(overview.get(k) for k in PAGE_DESCRIPTION):
            return
        snapshot = page_description_snapshot(overview)
        history = [h for h in store.get("inventaris_geschiedenis", []) if h.get("versie") != snapshot["versie"]]
        store["inventaris_geschiedenis"] = [snapshot, *history][:30]

    def edit_inventory(self, file, n, changes):
        """Change the description of the overview by hand (kind, summary, text
        read). The first time a field changes, its AI text is kept in
        "ai_origineel"; the version before goes into the history. Free.
        "beschrijvingsniveau" shows another of the four lengths (the slider, free,
        no new version); a summary edited then belongs to that length."""
        changes = dict(changes or {})
        level = changes.pop("beschrijvingsniveau", None)
        unknown = set(changes) - set(PAGE_DESCRIPTION)
        if (not changes and level is None) or unknown or not all(isinstance(v, str) for v in changes.values()):
            raise DetectionError(f"Alleen deze velden zijn te bewerken: {', '.join(PAGE_DESCRIPTION)}, en beschrijvingsniveau.", status=400, code="invalid_body")
        if any(len(v) > MAX_FIELD for v in changes.values()):
            raise DetectionError(f"Een tekst is hooguit {MAX_FIELD} tekens.", status=400, code="invalid_body")
        if level is not None and level not in DESCRIPTION_LEVELS:
            raise DetectionError(f"Onbekend beschrijvingsniveau '{level}'; kies uit {', '.join(DESCRIPTION_LEVELS)}.", status=400, code="invalid_body")
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            overview = store.get("inventaris")
            if not overview:
                raise DetectionError("Deze pagina heeft nog geen AI-overzicht.", status=409, code="no_overview")
            if level is not None and level != overview.get("beschrijvingsniveau"):
                if not (overview.get("beschrijvingen") or {}).get(level):
                    raise DetectionError("Deze lengte is nog niet gemaakt: vraag de beschrijving opnieuw, dan komen alle vier de lengtes.", status=409, code="length_not_made")
                overview = store["inventaris"] = json.loads(json.dumps(overview))
                show_description_length(overview, level)
                self.objects._write_store(file, n, store)
            changes = {field: value.strip() for field, value in changes.items()}
            if overview.get("beschrijvingsniveau") == "caption" and any(len(changes.get(field, "")) > CAPTION_MAX for _, field in SHOWN):
                raise DetectionError(f"Een Commons-caption is hooguit {CAPTION_MAX} tekens.", status=400, code="invalid_body")
            if all((overview.get(field) or "") == value for field, value in changes.items()):
                return {"inventaris": overview}  # nothing changes: no new version
            self._keep_page_description(store)
            overview = store["inventaris"] = json.loads(json.dumps(overview))
            _apply_hand_edit(overview, changes)
            sync_description_length(overview)
            self.objects._write_store(file, n, store)
        return {"inventaris": overview}

    def inventory_history(self, file, n):
        """Earlier descriptions of the image (by the AI or by hand), newest first,
        each with its "versie"; the current one is left out. Free."""
        store = self.objects._load_store(file, n)
        overview = store.get("inventaris") or {}
        # Only a description that is there counts as current (a removed one is all history).
        current = page_description_version(overview) if any(overview.get(k) for k in PAGE_DESCRIPTION) else None
        entries = [h for h in store.get("inventaris_geschiedenis", []) if h.get("versie") != current]
        return sorted(entries, key=lambda h: h.get("versie") or "", reverse=True)

    def restore_inventory(self, file, n, version):
        """Make an earlier description of the image the current one again; the
        current one goes into the history. The search terms stay. Free."""
        with self.objects.editing_store(file, n) as store:
            chosen = next((h for h in store.get("inventaris_geschiedenis", []) if h.get("versie") == version), None)
            if chosen is None:
                raise DetectionError("Die eerdere beschrijving bestaat niet (meer).", status=404, code="not_found")
            self._keep_page_description(store)
            overview = json.loads(json.dumps(store.get("inventaris") or {"zoektermen": []}))
            shown = overview.get("beschrijvingsniveau")
            for key in (*DESCRIPTION_META, "beschrijvingen"):
                overview.pop(key, None)
            overview.update({k: chosen.get(k) or "" for k in PAGE_DESCRIPTION})
            overview.update({k: chosen[k] for k in DESCRIPTION_META if chosen.get(k)})
            overview["beschrijvingsniveau"] = chosen.get("beschrijvingsniveau") or DEFAULT_DESCRIPTION_LEVEL
            if chosen.get("beschrijvingen"):  # all four lengths come back; the slider stays where it was
                overview["beschrijvingen"] = json.loads(json.dumps(chosen["beschrijvingen"]))
                if shown in overview["beschrijvingen"] and shown != overview["beschrijvingsniveau"]:
                    show_description_length(overview, shown)
            overview["delen"] = {**(overview.get("delen") or {}), "beschrijving": {"model": chosen.get("model"), "tijdstempel": chosen.get("tijdstempel")}}
            overview.setdefault("model", chosen.get("model"))
            overview.setdefault("tijdstempel", chosen.get("tijdstempel"))
            store["inventaris"] = overview
            store["inventaris_geschiedenis"] = [h for h in store["inventaris_geschiedenis"] if h.get("versie") != version]
        return {"inventaris": overview, "geschiedenis": self.inventory_history(file, n)}

    def forget_inventory_version(self, file, n, version):
        """Delete one earlier description of the image. Free."""
        with self.objects.editing_store(file, n) as store:
            history = store.get("inventaris_geschiedenis", [])
            if not any(h.get("versie") == version for h in history):
                raise DetectionError("Die eerdere beschrijving bestaat niet (meer).", status=404, code="not_found")
            store["inventaris_geschiedenis"] = [h for h in history if h.get("versie") != version]
        return {"geschiedenis": self.inventory_history(file, n)}
