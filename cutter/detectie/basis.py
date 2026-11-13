"""Detector interface shared by DummyDetector and MetaSamDetector.

The app only talks to `Detector`; which implementation is used is decided by
configuration (DETECTIE_MODUS=dummy|live).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# Labels the app gives objects itself (a click, a drawn rectangle, a region):
# not a real name, never a subject for the AI.
INTERNAL_LABELS = frozenset({"klik", "rechthoek", "regio"})


#: Fixed error codes per HTTP status, which the UI translates (functional design 3).
DEFAULT_CODES = {
    400: "bad_request",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "too_large",
    415: "unsupported",
    422: "unprocessable",
    429: "limit_reached",
    501: "not_implemented",
    502: "upstream_error",
    503: "unavailable",
}


class DetectionError(Exception):
    """A user-facing error (message in Dutch, plus a fixed code for the UI)."""

    def __init__(self, message, status=502, retry=False, code=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.retry = retry
        self.code = code or DEFAULT_CODES.get(status, "error")


@dataclass
class DetectedObject:
    """One detected object on a page.

    `box` is in native page pixels ({"x", "y", "w", "h"}). `mask_data` describes
    a raster that covers the box, possibly at a lower resolution; it is decoded
    only when needed (see maskers.py), because decoding SAM masks is slow:
    {"encoding": "lossless" | "one_bit" | "ellips", "payload": str, "width": int, "height": int}.
    """

    id: str
    label: str
    score: float | None
    box: dict
    mask_data: dict | None = None
    bron: str = "sam"
    herkomst: dict = field(default_factory=dict)

    def to_dict(self):
        """JSON-friendly representation, including the undecoded mask."""
        return {
            "id": self.id,
            "bron": self.bron,
            "label": self.label,
            "score": self.score,
            "box": self.box,
            "masker": self.mask_data,
            "herkomst": self.herkomst,
        }


class Detector(ABC):
    """Finds objects in a page image."""

    #: Short name used in provenance and cache keys, e.g. "dummy" or "sam-3.1".
    model = "onbekend"
    #: True when calls cost money (they count towards the daily limit).
    betaald = False

    @abstractmethod
    def detect(self, image, prompt, native_size=None, regions=None):
        """All instances of one concept (a short English noun phrase).

        `image` is a PIL image of the page, possibly smaller than the original;
        `native_size` = (width, height) of the original page, to which boxes
        are scaled. `regions` (optional) are rectangles in native pixels where
        objects are likely; only the dummy detector uses them.
        """

    def detect_point(self, image, x, y, native_size=None, regions=None):
        """The object under a point (native page pixels). Optional."""
        raise DetectionError("Deze detector ondersteunt geen klikprompts.", status=501)

    def detect_box(self, image, box, native_size=None):
        """The object inside a box (native pixels), e.g. a region from Commons. Optional."""
        raise DetectionError("Deze detector ondersteunt geen boxprompts.", status=501)
