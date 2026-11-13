"""Decoding object masks to rasters and PNGs, lazily and cached on disk."""

import base64
import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image

from ..export import encode
from ..opruimen import cached_bytes, sharded
from .basis import DetectionError

MAX_MASK_PIXELS = 200_000_000  # far above any real mask; a larger size is a damaged description


class BadMask(DetectionError, ValueError):
    """A mask that cannot be decoded (wrong size, broken payload): 422, code bad_mask.
    Also a ValueError, so callers that treat an unreadable mask as the box keep doing so."""

    def __init__(self):
        super().__init__("Het masker van dit object is beschadigd en kan niet gelezen worden.", status=422, code="bad_mask")


def decode_raster(mask_data):
    """Row-major uint8 array (height, width) of 0/1 for a mask description.

    No mask (regions from Commons, manual rectangles) is a full rectangle. A mask
    that does not decode (an odd answer of SAM, a damaged file) raises BadMask.
    """
    if not mask_data:
        return np.ones((1, 1), dtype=np.uint8)
    try:
        raster = _decode(mask_data)
    except BadMask:
        raise
    except Exception as exc:  # noqa: BLE001 - whatever the decoder trips over, it is a damaged mask
        raise BadMask() from exc
    if raster.ndim != 2 or 0 in raster.shape:
        raise BadMask()
    return raster


def _decode(mask_data):
    width, height = int(mask_data["width"]), int(mask_data["height"])
    if width <= 0 or height <= 0 or width * height > MAX_MASK_PIXELS:
        raise BadMask()
    encoding = mask_data["encoding"]
    if encoding == "png":  # a group (7.4): the union of its members' masks, as a 1-bit PNG
        image = Image.open(io.BytesIO(base64.b64decode(mask_data["payload"]))).convert("L")
        return (np.asarray(image) >= 128).astype(np.uint8)
    if encoding == "ellips":
        yy, xx = np.mgrid[0:height, 0:width]
        cy, cx = (height - 1) / 2, (width - 1) / 2
        inside = ((xx - cx) / (width / 2)) ** 2 + ((yy - cy) / (height / 2)) ** 2 <= 1
        return inside.astype(np.uint8)
    from meta_sam_parser import SegmentationMask, decode_mask_to_raster

    raster = decode_mask_to_raster(
        SegmentationMask(encoding=encoding, payload=mask_data["payload"], width=width, height=height)
    )
    return np.frombuffer(raster, dtype=np.uint8).reshape(height, width)


def mask_png(mask_data):
    """PNG (white, opaque where the mask is set, transparent elsewhere) at the
    mask's own resolution; the viewer stretches it over the object's box."""
    raster = decode_raster(mask_data)
    rgba = np.zeros(raster.shape + (4,), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = raster * 255
    return encode(Image.fromarray(rgba, "RGBA"), "PNG", optimize=True)


def union_mask(members, box, max_side=4096):
    """The mask of a group (7.4): [(box, raster)] of its members, each raster
    covering its own box, painted onto one raster that covers `box` (the box
    around all of them). Its resolution follows the sharpest member mask,
    at most `max_side` pixels on the longest side. Returns a mask description."""
    scales = [raster.shape[1] / member["w"] for member, raster in members if raster.shape != (1, 1) and member["w"]]
    scale = min(max(scales or [1.0]), max_side / max(box["w"], box["h"]))
    width, height = max(1, round(box["w"] * scale)), max(1, round(box["h"] * scale))
    canvas = np.zeros((height, width), dtype=np.uint8)
    for member, raster in members:
        w, h = max(1, round(member["w"] * scale)), max(1, round(member["h"] * scale))
        x, y = round((member["x"] - box["x"]) * scale), round((member["y"] - box["y"]) * scale)
        part = np.asarray(Image.fromarray(raster * 255, "L").resize((w, h), Image.NEAREST)) >= 128
        x1, y1 = min(width, x + w), min(height, y + h)
        if x1 <= x or y1 <= y:
            continue
        canvas[y:y1, x:x1] |= part[: y1 - y, : x1 - x].astype(np.uint8)
    png = encode(Image.fromarray(canvas * 255, "L").convert("1"), "PNG", optimize=True)
    return {"encoding": "png", "payload": base64.b64encode(png).decode("ascii"), "width": width, "height": height}


class MaskCache:
    """Decoded mask PNGs on disk, keyed by the mask description."""

    def __init__(self, directory):
        self.directory = Path(directory)

    def png(self, mask_data):
        key = hashlib.sha1(repr(sorted((mask_data or {}).items())).encode()).hexdigest()
        return cached_bytes(sharded(self.directory, key, ".png"), lambda: mask_png(mask_data))
