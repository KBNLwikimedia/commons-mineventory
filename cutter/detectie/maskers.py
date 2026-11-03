"""Decoding object masks to rasters and PNGs, lazily and cached on disk."""

import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image


def decode_raster(mask_data):
    """Row-major uint8 array (height, width) of 0/1 for a mask description.

    No mask (regions from Commons, manual rectangles) is a full rectangle.
    """
    if not mask_data:
        return np.ones((1, 1), dtype=np.uint8)
    width, height = mask_data["width"], mask_data["height"]
    encoding = mask_data["encoding"]
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
    buffer = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


class MaskCache:
    """Decoded mask PNGs on disk, keyed by the mask description."""

    def __init__(self, directory):
        self.directory = Path(directory)

    def png(self, mask_data):
        key = hashlib.sha1(repr(sorted((mask_data or {}).items())).encode()).hexdigest()
        path = self.directory / key[:2] / f"{key}.png"
        if path.exists():
            return path.read_bytes()
        data = mask_png(mask_data)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data
