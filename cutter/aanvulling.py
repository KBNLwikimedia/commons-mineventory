"""The AI-completed version of a cut-out (functional design 7.7, backlog 19b).

Where something stood in front of an object in the original (the boy on the back
of the cat), its cut-out has holes. Muse Image (Meta Model API) can fill them in,
but it *invents* what is missing: the result is not a source. So it is kept apart
from the cut-out, marked as made by AI, and never goes to Commons as a cut-out.

Paid in live mode ($0.01 per image, flat), cached per sent image and question, so
asking again for the same cut-out costs nothing unless "again" is asked.
"""

import base64
import hashlib
import io
from contextlib import nullcontext
from datetime import datetime, timezone

import numpy as np
import requests
from PIL import Image, ImageDraw

from . import __version__
from .detectie.basis import DetectionError
from .opruimen import mark_used

MODEL = "muse-image-1.0"
PRICE_USD = 0.01  # per generated image, whatever the prompt or tools (Meta's price list)
SEND_SIDE = 1536  # longest side of the cut-out sent to the model, in pixels
PROMPT_VERSION = 2  # 2: "Complete it" (the subject may be "an object"); your own name first
# Labels the app gives itself (a click, a drawn rectangle, a region): never a subject for the AI.
INTERNAL_LABELS = {"klik", "rechthoek", "regio"}
WHITE = 236  # a pixel with every channel at or above this counts as background
FILLED_COLOUR = (230, 0, 140, 150)  # magenta, half transparent: what the AI filled in

PROMPT = (
    "This is a cut-out of {name} from a historical image on Wikimedia Commons. "
    "Some parts of it are missing and show as plain white, because something else was in front of it in the original. "
    "Complete it: fill in only the missing parts, in exactly the same drawing style, technique, colours and line work, "
    "so that it looks whole. Do not change anything that is already there, do not add any other objects or text, "
    "and keep the background plain white."
)


def build_request(model, prompt, data_url, size):
    """The JSON body for POST /v1/images/edits: one image back, as PNG, without
    web or image search (the cut-out is the only reference) and without code."""
    return {
        "model": model,
        "prompt": prompt,
        "images": [{"image_url": data_url}],
        "n": 1,
        "size": size,
        "output_format": "png",
        "reasoning_strength": "high",
        "tool_enablement": {"enable_image_search": False, "enable_web_search": False, "enable_shell": False},
    }


class DummyImageEditor:
    """Free stand-in (DETECTIE_MODUS=dummy): the sent image with "AI (dummy)"
    written on it, so the whole flow can be tried without a model."""

    betaald = False

    def edit(self, model, prompt, png, size):
        image = Image.open(io.BytesIO(png)).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, min(image.width, 220), 28], fill=(51, 102, 204))
        draw.text((8, 8), "AI-aangevuld (dummy)", fill=(255, 255, 255))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


class MetaImageEditor:
    """Muse Image via the Meta Model API (POST /v1/images/edits)."""

    betaald = True

    def __init__(self, api_key, base_url="https://api.meta.ai/v1", timeout=180, session=None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def edit(self, model, prompt, png, size):
        if not self.api_key:
            raise DetectionError("Geen MODEL_API_KEY ingesteld; aanvullen is niet mogelijk.", status=503, code="no_api_key")
        data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        try:
            response = self.session.post(
                f"{self.base_url}/images/edits",
                json=build_request(model, prompt, data_url, size),
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise DetectionError("De Meta Model API is niet bereikbaar.", retry=True) from exc
        status = response.status_code
        if status == 200:
            try:
                return base64.b64decode(response.json()["data"][0]["b64_json"])
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                raise DetectionError("Muse Image gaf geen afbeelding terug.", retry=True) from exc
        try:
            detail = (response.json().get("error") or {}).get("message", "")
        except ValueError:
            detail = ""
        if status == 400:
            raise DetectionError(f"Het model weigerde het verzoek: {detail}".rstrip(": "), status=400)
        if status in (401, 403):
            raise DetectionError("De API-sleutel voor de Meta Model API wordt niet geaccepteerd.", status=503)
        if status == 404:
            raise DetectionError(f"Model '{model}' niet gevonden of geen toegang.", status=503)
        if status == 429:
            raise DetectionError(f"Te veel verzoeken aan '{model}'; probeer het zo opnieuw.", status=429, retry=True)
        raise DetectionError(f"De Meta Model API gaf een fout (HTTP {status}).", retry=True)


def make_image_editor(config):
    if config["DETECTIE_MODUS"] == "live":
        return MetaImageEditor(config["MODEL_API_KEY"], base_url=config["META_API_BASE"])
    return DummyImageEditor()


def prepare(png, side=SEND_SIDE):
    """The cut-out as sent: on white (the holes and the background become plain
    white), at most `side` pixels on its longest side. Returns (png bytes, "WxH")."""
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    scale = min(1.0, side / max(image.size))
    if scale < 1:
        image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)
    buffer = io.BytesIO()
    white.convert("RGB").save(buffer, format="PNG", optimize=True)
    return buffer.getvalue(), f"{image.width}x{image.height}"


def white_background(pixels, keep=None, side=400):
    """Where an image on white has its background: the white that is connected to the
    edge of the image, so white inside the subject (a white chest, a highlight) stays.
    The connection is worked out on a copy of at most `side` pixels (fast with numpy
    alone), then applied to the full size. `keep` (a boolean array of the same size)
    is never background: the shape of the original cut-out. Returns a boolean array."""
    height, width = pixels.shape[:2]
    white = pixels.min(axis=2) >= WHITE
    scale = min(1.0, side / max(width, height))
    small_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    small = np.asarray(Image.fromarray(white.astype(np.uint8) * 255, "L").resize(small_size, Image.BOX)) >= 250
    reached = np.zeros_like(small)
    reached[0, :], reached[-1, :], reached[:, 0], reached[:, -1] = small[0, :], small[-1, :], small[:, 0], small[:, -1]
    for _ in range(small.size):  # grow from the edge through white, until nothing changes
        grown = reached.copy()
        grown[1:, :] |= reached[:-1, :]
        grown[:-1, :] |= reached[1:, :]
        grown[:, 1:] |= reached[:, :-1]
        grown[:, :-1] |= reached[:, 1:]
        grown &= small
        if (grown == reached).all():
            break
        reached = grown
    outside = np.asarray(Image.fromarray(reached.astype(np.uint8) * 255, "L").resize((width, height), Image.NEAREST)) >= 128
    background = outside & white
    if keep is not None:
        background &= ~keep
    return background


def subject(obj):
    """What the cut-out shows, for the question: the name you gave it, else the subject of
    its description (English), its caption, for a group its own name or its members (e.g.
    "cardboard box and boy"), else its search term; "an object" when there is only a label
    the app gave itself (a click, a rectangle)."""
    description = obj.get("beschrijving") or {}
    own = obj.get("naam") or description.get("onderwerp_en") or (obj.get("bijschrift") or {}).get("tekst")
    if own:
        return own
    group = obj.get("groep")
    if group:
        if group.get("naam"):
            return group["naam"]
        names = list(dict.fromkeys(subject(m) for m in group.get("leden", [])))
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    label = obj.get("label_en") or obj.get("label") or ""
    return label if label and label.lower() not in INTERNAL_LABELS else "an object"


MAX_PROMPT = 2000  # characters of your own prompt
MAX_HISTORY = 20  # earlier AI-completed versions kept per object


def clean_prompt(text):
    return " ".join(str(text or "").split())[:MAX_PROMPT]


class CompletionService:
    """Ask, keep and serve the AI-completed version of an object's cut-out."""

    def __init__(self, editor, objects, cache_dir):
        self.editor = editor
        self.objects = objects  # DetectionService: object store, Commons client, usage
        self.cache_dir = cache_dir / "aanvullingen"

    def plan(self, file, n, object_id):
        """What is there and what a new one would cost. Free."""
        obj = self.objects._find(file, n, object_id)
        paid = self.editor.betaald
        return {"aangevuld": obj.get("aangevuld"), "model": MODEL, "betaald": paid, "kosten_usd": PRICE_USD if paid else 0.0}

    def _path(self, key):
        return self.cache_dir / key[:2] / f"{key}.png"

    def default_prompt(self, file, n, object_id):
        """The prompt the app would send, with the object's subject (free)."""
        return PROMPT.format(name=subject(self.objects._find(file, n, object_id)))

    def complete(self, file, n, object_id, again=False, user=None, prompt=None):
        """Make the AI-completed version (paid in live mode, cached) and note it on
        the object ("aangevuld"). With `again` the model is really asked anew. With
        `prompt` your own (edited) prompt goes to the model instead of the app's; the
        version before goes to the history ("aangevuld_geschiedenis")."""
        obj = self.objects._find(file, n, object_id)
        sent, size = prepare(self.objects.saved_file(file, n, object_id, "png"))
        name = subject(obj)
        default = PROMPT.format(name=name)
        own = clean_prompt(prompt)
        prompt = own or default
        key = hashlib.sha1(f"{MODEL}|{PROMPT_VERSION}|{prompt}|{hashlib.sha1(sent).hexdigest()}".encode()).hexdigest()
        path = self._path(key)
        cached = path.exists() and not again
        cost = 0.0
        if cached:
            mark_used(path)
        else:
            paid = self.editor.betaald
            booking = self.objects.verbruik.reservation(1, user=user, cost=PRICE_USD) if paid else nullcontext()
            with booking:
                result = self.editor.edit(MODEL, prompt, sent, size)
                if paid:
                    cost = PRICE_USD
                    self.objects.verbruik.register(
                        {"soort": "aanvulling", "bestand": file["mid"], "titel": file["titel"], "pagina": n, "term": f"AI-aangevulde versie ({MODEL})", "model": MODEL},
                        cost=PRICE_USD,
                        user=user,
                    )
            # Always a PNG, whatever came back.
            image = Image.open(io.BytesIO(result))
            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="PNG", optimize=True)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(buffer.getvalue())
        with Image.open(path) as image:
            dimensions = list(image.size)
        note = {
            "sleutel": key,
            "model": MODEL,
            "onderwerp": name,
            "prompt": prompt,  # exactly what went to the model, to show it
            "prompt_versie": PROMPT_VERSION,
            "prompt_eigen": bool(own) and own != default,  # your own, edited prompt
            "afmetingen": dimensions,
            "kosten_usd": cost,
            "uit_cache": cached,
            "tijdstempel": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "appversie": __version__,
        }
        return {"object": self._set_current(file, n, object_id, note), "uit_cache": cached, "budget": self.objects.verbruik.status(user)}

    def _set_current(self, file, n, object_id, note):
        """Make `note` the current version (None: none); the one before goes on top of
        the history, each version once, at most MAX_HISTORY."""
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            obj = self.objects._find_in(store, object_id)
            previous = obj.get("aangevuld")
            keep = {note["sleutel"]} if note else set()
            history = [h for h in obj.get("aangevuld_geschiedenis") or [] if h.get("sleutel") not in keep]
            if previous and previous.get("sleutel") not in keep:
                history = [previous] + [h for h in history if h.get("sleutel") != previous.get("sleutel")]
            obj["aangevuld"] = note
            obj["aangevuld_geschiedenis"] = history[:MAX_HISTORY]
            self.objects._write_store(file, n, store)
            return self.objects.public(file, n, obj)

    def _version(self, file, n, object_id, key):
        """The note of a version: the current one or one from the history; 404 otherwise."""
        obj = self.objects._find(file, n, object_id)
        for note in [obj.get("aangevuld"), *(obj.get("aangevuld_geschiedenis") or [])]:
            if note and note.get("sleutel") == key:
                return note
        raise DetectionError("Deze versie van de AI-aangevulde versie bestaat niet (meer).", status=404, code="not_found")

    def use_version(self, file, n, object_id, key):
        """An earlier version becomes the current one again (free, from the cache)."""
        note = self._version(file, n, object_id, key)
        if not self._path(key).exists():
            raise DetectionError("Het beeld van deze versie is niet meer bewaard (bewaartermijn); vraag opnieuw.", status=410, code="expired")
        return self._set_current(file, n, object_id, {**note, "uit_cache": True})

    def delete_version(self, file, n, object_id, key):
        """Remove an earlier version from the history (the image stays in the cache)."""
        self._version(file, n, object_id, key)
        with self.objects.lock:
            store = self.objects._load_store(file, n)
            obj = self.objects._find_in(store, object_id)
            obj["aangevuld_geschiedenis"] = [h for h in obj.get("aangevuld_geschiedenis") or [] if h.get("sleutel") != key]
            self.objects._write_store(file, n, store)
            return self.objects.public(file, n, obj)

    def _completed_path(self, file, n, object_id, key=None):
        note = self._version(file, n, object_id, key) if key else self.objects._find(file, n, object_id).get("aangevuld")
        path = self._path(note["sleutel"]) if note else None
        if not path or not path.exists():
            raise DetectionError("Er is (nog) geen AI-aangevulde versie van dit object.", status=404, code="not_found")
        mark_used(path)
        return path

    def image(self, file, n, object_id, key=None):
        """The PNG of the AI-completed version with a transparent background, like the
        cut-out (Muse Image always returns an opaque image on white); 404 when there is
        none (or it expired). Made once and cached next to the image itself. With `key`
        an earlier version (for the carousel)."""
        completed_path = self._completed_path(file, n, object_id, key)
        path = completed_path.with_name(completed_path.stem + "_transparant.png")
        if path.exists():
            mark_used(path)
            return path.read_bytes()
        completed = Image.open(completed_path).convert("RGB")
        cutout = Image.open(io.BytesIO(self.objects.saved_file(file, n, object_id, "png"))).convert("RGBA")
        shape = np.asarray(cutout.getchannel("A").resize(completed.size, Image.BILINEAR)) >= 128
        background = white_background(np.asarray(completed), keep=shape)
        rgba = completed.convert("RGBA")
        rgba.putalpha(Image.fromarray(np.where(background, 0, 255).astype(np.uint8), "L"))
        buffer = io.BytesIO()
        rgba.save(buffer, format="PNG", optimize=True)
        path.write_bytes(buffer.getvalue())
        return buffer.getvalue()

    def filled_overlay(self, file, n, object_id):
        """A transparent PNG, the size of the AI-completed version, that colours what
        the AI filled in: where the cut-out had no shape (outside its mask) and the
        completed version is not white. Approximate: the model draws the whole image
        anew and may shift it a little. Cached next to the completed version."""
        completed_path = self._completed_path(file, n, object_id)
        path = completed_path.with_name(completed_path.stem + "_ingevuld.png")
        if path.exists():
            mark_used(path)
            return path.read_bytes()
        completed = Image.open(completed_path).convert("RGB")
        cutout = Image.open(io.BytesIO(self.objects.saved_file(file, n, object_id, "png"))).convert("RGBA")
        shape = np.asarray(cutout.getchannel("A").resize(completed.size, Image.BILINEAR)) >= 128
        painted = np.asarray(completed).min(axis=2) < WHITE
        filled = painted & ~shape
        overlay = np.zeros(filled.shape + (4,), dtype=np.uint8)
        overlay[filled] = FILLED_COLOUR
        buffer = io.BytesIO()
        Image.fromarray(overlay, "RGBA").save(buffer, format="PNG", optimize=True)
        path.write_bytes(buffer.getvalue())
        return buffer.getvalue()

    def forget(self, file, n, object_id):
        """Remove the current version from the object; it goes to the history, and the
        image stays in the cache (free to get back with "Use this version")."""
        self.objects._find(file, n, object_id)
        return self._set_current(file, n, object_id, None)

