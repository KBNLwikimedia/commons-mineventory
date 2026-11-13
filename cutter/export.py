"""Saving cut-outs and exporting (functional design 9.5 and 11).

- `cutout`: a transparent PNG of an object (the mask as alpha channel) and its
  black-and-white mask, from the original at full resolution.
- `crop_jpeg`: the rectangle as JPG (quality 95, the default for Commons).
- `file_zip`: everything saved for a file as one zip, with the wikitext of the
  Commons concept per cut-out.
- `table_csv`, `table_xlsx`: a list of rows (Changelog, Usage, Objects) as a file
  (wish Olaf). The Excel file is written with the standard library alone.

IIIF annotations follow later (backlog).
"""

import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

from . import __version__

JPEG_QUALITY = 95

DISCLAIMER = (
    "Dit is een experiment. Het is geen officiële dienst van de KB, nationale bibliotheek, "
    "of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend."
)


def encode(image, fmt, **options):
    """The bytes of a PIL image saved as `fmt` ("PNG", "JPEG") with these save options."""
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **options)
    return buffer.getvalue()


def _png(image):
    return encode(image, "PNG", optimize=True)


def rect(box, scale):
    """(x0, y0, x1, y1) of a box in native page pixels, scaled by `scale`; at least one pixel."""
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
    crop = page_image.crop(rect(box, scale)).convert("RGBA")
    alpha = Image.fromarray(raster * 255, "L").resize(crop.size, Image.BILINEAR)
    crop.putalpha(alpha)
    mask = alpha.point(lambda value: 255 if value >= 128 else 0)
    return _png(crop), _png(mask)


def crop_jpeg(page_image, box, scale, quality=JPEG_QUALITY):
    """JPEG of a rectangle of the page (native pixels, scaled by `scale`)."""
    return encode(page_image.crop(rect(box, scale)).convert("RGB"), "JPEG", quality=quality)


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
        f"Gemaakt met Commons Mineventory {__version__} op {datetime.now(timezone.utc).isoformat(timespec='seconds')}.",
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


# -- Tables -------------------------------------------------------------------------------

_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
_ILLEGAL_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
_EXCEL_CELL_MAX = 32767
_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _csv_cell(value):
    """Text as text: a title or AI text that starts like a formula must not run in a spreadsheet."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) and value.startswith(_FORMULA_START):
        return "'" + value
    return value


def table_csv(rows, columns):
    """UTF-8 with a byte order mark, so Excel reads the accents correctly."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(columns)
    writer.writerows([_csv_cell(row.get(column)) for column in columns] for row in rows)
    return ("\ufeff" + out.getvalue()).encode("utf-8")


def _column_name(index):
    name = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        name = chr(65 + rest) + name
    return name


def _xlsx_cell(reference, value, style=0):
    """Text as an inline string, so nothing in a cell can become a formula."""
    if value is None or value == "":
        return ""
    style_attribute = f' s="{style}"' if style else ""
    if isinstance(value, bool):
        return f'<c r="{reference}"{style_attribute} t="b"><v>{int(value)}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{reference}"{style_attribute}><v>{value}</v></c>'
    text = escape(_ILLEGAL_XML.sub("", str(value))[:_EXCEL_CELL_MAX])
    return f'<c r="{reference}"{style_attribute} t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>'


def table_xlsx(rows, columns):
    """One sheet: a bold header that stays in view, and the rows."""
    lines = [
        '<row r="1">' + "".join(_xlsx_cell(f"{_column_name(c)}1", name, style=1) for c, name in enumerate(columns)) + "</row>"
    ]
    for r, row in enumerate(rows, start=2):
        lines.append(f'<row r="{r}">' + "".join(_xlsx_cell(f"{_column_name(c)}{r}", row.get(name)) for c, name in enumerate(columns)) + "</row>")
    sheet = (
        f'{_XML}<worksheet xmlns="{_MAIN_NS}"><sheetViews><sheetView tabSelected="1" workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<sheetData>{"".join(lines)}</sheetData></worksheet>'
    )
    parts = {
        "[Content_Types].xml": (
            f'{_XML}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            f'{_XML}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{_REL_NS}/officeDocument" Target="xl/workbook.xml"/></Relationships>'
        ),
        "xl/workbook.xml": (
            f'{_XML}<workbook xmlns="{_MAIN_NS}" xmlns:r="{_REL_NS}"><bookViews><workbookView/></bookViews>'
            '<sheets><sheet name="Export" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            f'{_XML}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{_REL_NS}/worksheet" Target="worksheets/sheet1.xml"/>'
            f'<Relationship Id="rId2" Type="{_REL_NS}/styles" Target="styles.xml"/></Relationships>'
        ),
        "xl/styles.xml": (
            f'{_XML}<styleSheet xmlns="{_MAIN_NS}">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
            "</styleSheet>"
        ),
        "xl/worksheets/sheet1.xml": sheet,
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content.encode("utf-8"))
    return buffer.getvalue()
