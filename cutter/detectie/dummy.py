"""DummyDetector: a few realistic fake objects per prompt, with elliptical
masks (functional design, chapter 13, phase 1).

Deterministic: the same page and prompt always give the same objects, so the
UI, selection and export can be tested without the Meta Model API.
"""

import hashlib
import random
from datetime import datetime, timezone

from .. import __version__
from .basis import DetectedObject, Detector

MASK_RESOLUTION = 64  # raster width of the elliptical dummy masks


class DummyDetector(Detector):
    model = "dummy"
    betaald = False

    def detect(self, image, prompt, native_size=None, regions=None):
        width, height = native_size or image.size
        rng = random.Random(self._seed(width, height, prompt))
        areas = [r for r in (regions or []) if r["w"] > 80 and r["h"] > 80] or [
            {"x": 0, "y": 0, "w": width, "h": height}
        ]
        count = rng.randint(1, 3)
        return [self._object(rng, rng.choice(areas), prompt, i) for i in range(count)]

    def detect_point(self, image, x, y, native_size=None, regions=None):
        width, height = native_size or image.size
        rng = random.Random(self._seed(width, height, f"punt:{x}:{y}"))
        w, h = rng.randint(150, 400), rng.randint(150, 400)
        area = {
            "x": max(0, min(width - w, x - w // 2)),
            "y": max(0, min(height - h, y - h // 2)),
            "w": w,
            "h": h,
        }
        return [self._object(rng, area, "klik", 0, fill=True)]

    def detect_box(self, image, box, native_size=None):
        width, height = native_size or image.size
        rng = random.Random(self._seed(width, height, f"box:{box}"))
        area = {k: int(box[k]) for k in ("x", "y", "w", "h")}
        return [self._object(rng, area, "regio", 0, fill=True)]

    @staticmethod
    def _seed(width, height, prompt):
        return int(hashlib.sha1(f"{width}x{height}:{prompt}".encode()).hexdigest()[:12], 16)

    def _object(self, rng, area, prompt, index, fill=False):
        if fill:
            w, h, x, y = area["w"], area["h"], area["x"], area["y"]
        else:
            w = max(40, int(area["w"] * rng.uniform(0.25, 0.6)))
            h = max(40, int(area["h"] * rng.uniform(0.15, 0.4)))
            h = min(h, area["h"])
            x = area["x"] + rng.randint(0, max(0, area["w"] - w))
            y = area["y"] + rng.randint(0, max(0, area["h"] - h))
        mask_w = MASK_RESOLUTION
        mask_h = max(1, round(MASK_RESOLUTION * h / w))
        return DetectedObject(
            id=f"dummy-{index}",
            label=prompt,
            score=round(rng.uniform(0.45, 0.97), 3),
            box={"x": x, "y": y, "w": w, "h": h},
            mask_data={"encoding": "ellips", "payload": "", "width": mask_w, "height": mask_h},
            bron="dummy",
            herkomst={
                "model": self.model,
                "prompt": prompt,
                "tijdstempel": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "appversie": __version__,
            },
        )
