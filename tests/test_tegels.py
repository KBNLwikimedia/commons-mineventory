"""Cut-outs from very large originals, read in pieces with libvips (cutter/tegels.py, FO 5.4)."""

import io

import numpy as np
import pytest
from conftest import ALBUM
from PIL import Image

from cutter import export, tegels
from cutter.commons import CommonsClient
from cutter.detectie.dienst import DetectionService
from cutter.detectie.dummy import DummyDetector
from cutter.verbruik import Verbruik

pytestmark = pytest.mark.skipif(not tegels.available(), reason="pyvips (libvips) is not installed")


def picture(mode="RGB", size=(300, 200)):
    data = np.zeros((size[1], size[0], len(mode)), dtype=np.uint8)
    data[:, :, 0] = np.arange(size[0]) % 256  # a gradient, so a wrong offset shows
    if len(mode) > 1:
        data[:, :, 1] = (np.arange(size[1]) % 256)[:, None]
    return Image.fromarray(data if len(mode) > 1 else data[:, :, 0], mode)


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "TIFF"])
def test_crop_matches_pillow(tmp_path, fmt):
    original = picture()
    path = tmp_path / f"x.{fmt.lower()}"
    original.save(path, format=fmt, **({"quality": 100} if fmt == "JPEG" else {}))
    tiled = tegels.TiledImage(path)
    assert (tiled.width, tiled.height) == (300, 200)
    piece = tiled.crop((50, 40, 170, 120))
    expected = Image.open(path).convert("RGB").crop((50, 40, 170, 120))
    assert piece.size == (120, 80) and piece.mode == "RGB"
    assert np.abs(np.asarray(piece, dtype=int) - np.asarray(expected, dtype=int)).max() <= 2


def test_crop_from_bytes_greyscale_alpha_and_16_bit(tmp_path):
    grey = io.BytesIO()
    picture("L").save(grey, format="PNG")
    assert tegels.TiledImage(grey.getvalue()).crop((0, 0, 10, 10)).mode == "RGB"
    rgba = io.BytesIO()
    picture("RGBA").save(rgba, format="PNG")
    assert tegels.TiledImage(rgba.getvalue()).crop((0, 0, 10, 10)).mode == "RGBA"
    deep = tmp_path / "deep.tif"
    Image.fromarray(np.arange(200 * 300, dtype=np.uint16).reshape(200, 300)).save(deep)
    piece = tegels.TiledImage(deep).crop((0, 0, 20, 20))
    assert piece.mode == "RGB" and piece.size == (20, 20)


def test_crop_is_clamped_to_the_image(tmp_path):
    path = tmp_path / "x.png"
    picture().save(path)
    assert tegels.TiledImage(path).crop((280, 190, 400, 400)).size == (20, 10)


def test_large_file_is_cut_out_in_pieces_at_full_resolution(fetcher, tmp_path):
    # A limit of 0.01 megapixel makes the album a "large" file.
    client = CommonsClient(fetcher, cache_dir=tmp_path / "cache", max_megapixels=0.01)
    album = client.load_file(ALBUM)
    assert album["tegels"] and album["uitsnijden_mogelijk"]
    image = client.original_image(album, 1)
    assert isinstance(image, tegels.TiledImage)
    service = DetectionService(DummyDetector(), client, tmp_path / "cache", tmp_path / "uitvoer", Verbruik(tmp_path / "verbruik", 500))
    rect = service.rectangle(album, 1, {"x": 100, "y": 100, "w": 400, "h": 300})["object"]
    service.save_objects(album, 1, [rect["id"]])
    saved = {o["id"]: o for o in service.page_objects(album, 1)}[rect["id"]]["opgeslagen"]
    jpg = Image.open(tmp_path / "uitvoer" / album["mid"] / saved["jpg"])
    scale = image.width / album["breedte"]
    assert jpg.size == (round(400 * scale), round(300 * scale))
    # The same pixels as when the whole original is decoded with Pillow.
    whole = Image.open(io.BytesIO(client._original_bytes(album))).convert("RGB")
    expected = Image.open(io.BytesIO(export.crop_jpeg(whole, rect["box"], scale)))
    assert np.abs(np.asarray(jpg, dtype=int) - np.asarray(expected, dtype=int)).mean() < 2
    # Previews come from the pieces too.
    assert service.cutout_jpeg(album, 1, rect["id"], width=None)[:2] == b"\xff\xd8"
