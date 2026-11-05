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

import requests
from PIL import Image, ImageDraw

from . import __version__
from .detectie.basis import DetectionError
from .opruimen import mark_used

MODEL = "muse-image-1.0"
PRICE_USD = 0.01  # per generated image, whatever the prompt or tools (Meta's price list)
SEND_SIDE = 1536  # longest side of the cut-out sent to the model, in pixels
PROMPT_VERSION = 1

PROMPT = (
    "This is a cut-out of {name} from a historical image on Wikimedia Commons. "
    "Some parts of it are missing and show as plain white, because something else was in front of it in the original. "
    "Complete the {name}: fill in only the missing parts, in exactly the same drawing style, technique, colours and line work, "
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


def subject(obj):
    """What the cut-out shows, in English, for the question."""
    description = obj.get("beschrijving") or {}
    return description.get("onderwerp_en") or (obj.get("bijschrift") or {}).get("tekst") or obj.get("label_en") or obj.get("label") or "object"


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

    def complete(self, file, n, object_id, again=False, user=None):
        """Make the AI-completed version (paid in live mode, cached) and note it on
        the object ("aangevuld"). With `again` the model is really asked anew."""
        obj = self.objects._find(file, n, object_id)
        sent, size = prepare(self.objects.saved_file(file, n, object_id, "png"))
        name = subject(obj)
        prompt = PROMPT.format(name=name)
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
            "prompt_versie": PROMPT_VERSION,
            "afmetingen": dimensions,
            "kosten_usd": cost,
            "uit_cache": cached,
            "tijdstempel": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "appversie": __version__,
        }
        return {"object": self.objects.set_field(file, n, object_id, "aangevuld", note), "uit_cache": cached, "budget": self.objects.verbruik.status(user)}

    def image(self, file, n, object_id):
        """The PNG of the AI-completed version; 404 when there is none (or it expired)."""
        note = self.objects._find(file, n, object_id).get("aangevuld")
        path = self._path(note["sleutel"]) if note else None
        if not path or not path.exists():
            raise DetectionError("Er is (nog) geen AI-aangevulde versie van dit object.", status=404, code="not_found")
        mark_used(path)
        return path.read_bytes()

    def forget(self, file, n, object_id):
        """Remove the note from the object; the image stays in the cache (free to get back)."""
        self.objects._find(file, n, object_id)
        return self.objects.set_field(file, n, object_id, "aangevuld", None)

