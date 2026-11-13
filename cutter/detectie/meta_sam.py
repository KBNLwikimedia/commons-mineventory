"""MetaSamDetector: SAM 3.1 via the Meta Model API (Responses API).

Request and response format: docs/meta-sam-api.md. Tested only with recorded
or constructed responses; no live calls without explicit permission from Olaf.

The wire format of the mask payload is not documented, so parsing the output
text and decoding masks is left to Meta's official `meta-sam-parser`.
"""

import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from meta_sam_parser import CompletedOutcome, image_segmentation_format

from .. import __version__
from ..export import encode
from .basis import DetectedObject, DetectionError, Detector

logger = logging.getLogger(__name__)

DEFAULT_MAX_WIDTH = 2000  # pixels sent to SAM; boxes are scaled back to the native page
JPEG_QUALITY = 90


@dataclass
class SamRecord:
    """One object from the SAM output, in pixels of the image that was sent.
    `right`/`bottom` are half-open (the wire format's x2/y2 are inclusive).
    `mask` is the parser's SegmentationMask (encoding, payload, width, height)."""

    object_id: str
    left: float
    top: float
    right: float
    bottom: float
    confidence: float | None
    mask: object | None = None


def prepare_image(image, max_width=DEFAULT_MAX_WIDTH):
    """JPEG data URL of the page, at most `max_width` wide.

    Returns (data_url, (sent_width, sent_height), scale) where scale converts
    sent pixels back to native page pixels.
    """
    width, height = image.size
    scale = 1.0
    if width > max_width:
        scale = width / max_width
        image = image.resize((max_width, round(height / scale)))
    data = encode(image.convert("RGB"), "JPEG", quality=JPEG_QUALITY)
    data_url = "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
    return data_url, image.size, scale


def point_prompt(x, y, size):
    """Object prompt for one positive point (documented wire syntax)."""
    w, h = size
    return f"<0f>1<|point;x={int(x)};y={int(y)};w={w};h={h}|>"


def box_prompt(box, size):
    """Object prompt for one box (documented wire syntax), in sent pixels:
    {"x", "y", "w", "h"} becomes x1/y1 (top left) and x2/y2 (bottom right)."""
    w, h = size
    x1, y1 = int(box["x"]), int(box["y"])
    x2, y2 = int(round(box["x"] + box["w"])), int(round(box["y"] + box["h"]))
    return f"<0f>1<|box;x1={x1};y1={y1};x2={x2};y2={y2};w={w};h={h}|>"


def build_request(model, text, data_url, mask_encoding="lossless"):
    """Responses API body for one image and one prompt (noun phrase or object prompt)."""
    return {
        "model": model,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": text},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        "metadata": {"mask_encoding": mask_encoding, "include_confidence": "true"},
        "stream": False,
    }


def extract_output_text(body):
    """The `output_text` of a non-streaming Responses API answer."""
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    parts = []
    for item in body.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    return "".join(parts)


def parse_output(text):
    """Turn SAM output text into SamRecords with Meta's official parser.

    Each object comes as a box record followed by a mask record with the same
    object id. Parser diagnostics (malformed lines) are logged, not fatal.
    """
    if not text.strip():
        return []  # no matches: empty output, not an error
    parser = image_segmentation_format().create_parser()
    parser.push(text, emit=False)
    result = parser.finish(CompletedOutcome()).result
    for diagnostic in result.diagnostics:
        logger.warning("SAM output %s at line %s: %s", diagnostic.code, diagnostic.line, diagnostic.message)

    records = {}
    for record in result.records:
        if record.kind == "box":
            records[record.object_id] = SamRecord(
                object_id=record.object_id,
                left=record.left,
                top=record.top,
                right=record.right,
                bottom=record.bottom,
                confidence=record.confidence,
            )
        elif record.kind == "mask" and record.object_id in records:
            records[record.object_id].mask = record.mask
    return list(records.values())


class MetaSamDetector(Detector):
    def __init__(
        self,
        api_key,
        base_url="https://api.meta.ai/v1",
        model="sam-3.1",
        max_width=DEFAULT_MAX_WIDTH,
        timeout=120,
        session=None,
        parse=parse_output,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_width = max_width
        self.timeout = timeout
        self.session = session or requests.Session()
        self._parse = parse

    # -- Public ---------------------------------------------------------------

    betaald = True

    def detect(self, image, prompt, native_size=None, regions=None):
        data_url, size, scale = self._prepare(image, native_size)
        return self._run(prompt, data_url, size, scale, label=prompt)

    def detect_point(self, image, x, y, native_size=None, regions=None):
        data_url, size, scale = self._prepare(image, native_size)
        text = point_prompt(x / scale, y / scale, size)
        # Box and point prompts always come back as one_bit masks.
        return self._run(text, data_url, size, scale, label="klik", mask_encoding="one_bit")

    def detect_box(self, image, box, native_size=None):
        data_url, size, scale = self._prepare(image, native_size)
        sent = {k: box[k] / scale for k in ("x", "y", "w", "h")}
        text = box_prompt(sent, size)
        # Box and point prompts always come back as one_bit masks.
        return self._run(text, data_url, size, scale, label="regio", mask_encoding="one_bit")

    # -- Internals ------------------------------------------------------------

    def _prepare(self, image, native_size):
        """Data URL, sent size and the scale from sent to native page pixels."""
        data_url, size, scale = prepare_image(image, self.max_width)
        if native_size:
            scale = native_size[0] / size[0]
        return data_url, size, scale

    def _run(self, text, data_url, size, scale, label, mask_encoding="lossless"):
        body = build_request(self.model, text, data_url, mask_encoding)
        output = extract_output_text(self._post(body))
        records = self._parse(output)
        return self.to_objects(records, scale, label, text, size)

    def _post(self, body):
        if not self.api_key:
            raise DetectionError("Geen MODEL_API_KEY ingesteld; live detectie is niet mogelijk.", status=503)
        try:
            response = self.session.post(
                f"{self.base_url}/responses",
                json=body,
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
            raise DetectionError(f"SAM weigerde het verzoek: {detail}".rstrip(": "), status=400)
        if status in (401, 403):
            raise DetectionError("De API-sleutel voor de Meta Model API wordt niet geaccepteerd.", status=503)
        if status == 404:
            raise DetectionError(f"Model '{self.model}' niet gevonden of geen toegang.", status=503)
        if status == 429:
            raise DetectionError("Te veel verzoeken aan de Meta Model API; probeer het zo opnieuw.", status=429, retry=True)
        raise DetectionError(f"De Meta Model API gaf een fout (HTTP {status}).", retry=True)

    def to_objects(self, records, scale, label, prompt, size):
        """Scale records back to native page pixels. Masks stay encoded;
        decoding is slow and happens only when needed (maskers.py)."""
        provenance = {
            "model": self.model,
            "prompt": prompt,
            "tijdstempel": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "appversie": __version__,
            "verstuurde_afmetingen": list(size),
        }
        objects = []
        for record in records:
            mask_data = None
            if record.mask is not None:
                mask_data = {
                    "encoding": str(record.mask.encoding),
                    "payload": record.mask.payload,
                    "width": record.mask.width,
                    "height": record.mask.height,
                }
            objects.append(
                DetectedObject(
                    id=f"sam-{record.object_id}",
                    label=label,
                    score=record.confidence,
                    box={
                        "x": round(record.left * scale),
                        "y": round(record.top * scale),
                        "w": round((record.right - record.left) * scale),
                        "h": round((record.bottom - record.top) * scale),
                    },
                    mask_data=mask_data,
                    herkomst=dict(provenance),
                )
            )
        return objects
