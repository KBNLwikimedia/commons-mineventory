"""Saving cut-outs and exporting (functional design 9.5 and 11).

- `cutout`: a transparent PNG of an object (the mask as alpha channel) and its
  black-and-white mask, from the original at full resolution.
- `crop_jpeg`: the rectangle as JPG (quality 95, the default for Commons).
- `file_zip`: everything saved for a file as one zip, with the wikitext of the
  Commons concept per cut-out.

IIIF annotations follow later (backlog).
"""

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from . import __version__

JPEG_QUALITY = 95

DISCLAIMER = (
    "Dit is een experiment. Het is geen officiële dienst van de KB, nationale bibliotheek, "
    "of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend."
)


def _png(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _rect(box, scale):
    x0 = int(box["x"] * scale)
    y0 = int(box["y"] * scale)
    x1 = max(x0 + 1, round((box["x"] + box["w"]) * scale))
    y1 = max(y0 + 1, round((box["y"] + box["h"]) * scale))
    return x0, y0, x1, y1


def cutout(page_image, box, scale, raster):
    """(transparent PNG, mask PNG) for an object.

    `box` is in native page pixels, `scale` converts them to `page_image`
    pixels, and `raster` is the 0/1 mask covering the box (any resolution).
    The mask is stretched over the box; bilinear scaling gives soft edges in
    the alpha channel, the separate mask PNG is thresholded to pure black/white.
    """
    crop = page_image.crop(_rect(box, scale)).convert("RGBA")
    alpha = Image.fromarray(raster * 255, "L").resize(crop.size, Image.BILINEAR)
    crop.putalpha(alpha)
    mask = alpha.point(lambda value: 255 if value >= 128 else 0)
    return _png(crop), _png(mask)


def crop_jpeg(page_image, box, scale, quality=JPEG_QUALITY):
    """JPEG of a rectangle of the page (native pixels, scaled by `scale`)."""
    buffer = io.BytesIO()
    page_image.crop(_rect(box, scale)).convert("RGB").save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def readme(file):
    """LEESMIJ.txt for a file's zip: source, licence and disclaimer."""
    licence = file.get("licentie") or {}
    lines = [
        file.get("titel") or file.get("mid") or "",
        f"Commons: {file.get('url')}",
        f"M-id: {file.get('mid')}",
        f"Licentie van het origineel: {licence.get('kort') or 'onbekend'}",
        f"Maker: {file.get('maker') or 'onbekend'}",
        "",
        "Inhoud:",
        "- bestand.json: de gegevens van het origineel op Commons.",
        "- pagina_<n>/objecten.json: de objecten met box (pixels van het origineel),",
        "  label, score, herkomst, beschrijving en het Commons-concept.",
        "- pagina_<n>/jpg/<object-id>.jpg: de uitsnede als JPG (de rechthoek), in de",
        "  volledige resolutie van het origineel.",
        "- pagina_<n>/png/<object-id>.png: de uitsnede in de vorm van het object,",
        "  transparant erbuiten (alleen voor objecten met een masker).",
        "- pagina_<n>/maskers/<object-id>_mask.png: het masker in zwart-wit.",
        "- wikitekst/<object-id>.txt: de voorgestelde wikitekst voor Commons.",
        "",
        "Een uitsnede is een afgeleid werk en valt onder de licentie van het origineel.",
        "Vermeld bij hergebruik de maker en de licentie, en het origineel als bron.",
        "",
        f"Gemaakt met Commons Cutter {__version__} op {datetime.now(timezone.utc).isoformat(timespec='seconds')}.",
        DISCLAIMER,
    ]
    return "\n".join(lines) + "\n"


def file_zip(folder, wikitexts=None):
    """Zip of everything saved for a file (its output folder): bestand.json,
    LEESMIJ.txt, per page the object store and the saved cut-outs of objects
    still on the page, and the wikitext per cut-out ({object id: text}).

    Returns (zip bytes, number of saved objects).
    """
    folder = Path(folder)
    meta_path = folder / "bestand.json"
    file = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    wikitexts = wikitexts or {}
    buffer = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for store_path in sorted(folder.glob("pagina_*/objecten.json")):
            store = json.loads(store_path.read_text(encoding="utf-8"))
            saved = [o for o in store.get("objecten", []) if o.get("opgeslagen")]
            if not saved:
                continue
            archive.write(store_path, f"{store_path.parent.name}/objecten.json")
            for obj in saved:
                for key, value in obj["opgeslagen"].items():
                    if key in ("tijdstempel", "breedte", "hoogte"):
                        continue
                    path = folder / value
                    if path.exists():
                        archive.write(path, value, compress_type=zipfile.ZIP_STORED)
                if obj["id"] in wikitexts:
                    archive.writestr(f"wikitekst/{obj['id']}.txt", wikitexts[obj["id"]])
                count += 1
        if meta_path.exists():
            archive.write(meta_path, "bestand.json")
        archive.writestr("LEESMIJ.txt", readme(file))
    return buffer.getvalue(), count
