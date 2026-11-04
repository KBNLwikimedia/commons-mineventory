"""Cut-outs from very large originals, in pieces (functional design 5.4).

Above MAX_MEGAPIXELS the original is not decoded as a whole (a 300-megapixel
scan is about 900 MB in memory). Detection runs on the reduced image, as for
every file; for a cut-out at full resolution only the needed piece is read,
with libvips (pyvips): it decodes the file sequentially up to the piece and
keeps only that piece. JPEG, PNG and (multi-page) TIFF all work this way.

`TiledImage` behaves like the few parts of a Pillow image that the app uses
on an original: `width`, `height`, `crop(box)` and `convert()`. Without pyvips
installed, `available()` is False and the app refuses such files, as before.
"""

from pathlib import Path

from PIL import Image

try:  # libvips is a system library; without it large originals stay unsupported
    import pyvips
except (ImportError, OSError):
    pyvips = None


def available():
    return pyvips is not None


class TiledImage:
    """A large original on disk (or in memory), read one piece at a time."""

    def __init__(self, source, page=0):
        if pyvips is None:
            raise RuntimeError("pyvips (libvips) is not installed.")
        self.source = source  # a path, or the bytes of the file
        self.page = page
        header = self._open()
        self.width = header.width
        self.height = header.height

    def _open(self, access="sequential"):
        options = {"access": access}
        if self.page:
            options["page"] = self.page
        if isinstance(self.source, (str, Path)):
            return pyvips.Image.new_from_file(str(self.source), **options)
        return pyvips.Image.new_from_buffer(self.source, "", **options)

    def convert(self, _mode=None):
        """Converting happens per piece, in crop(); the whole image is never converted."""
        return self

    def crop(self, box):
        """The piece (left, top, right, bottom) as a Pillow image in RGB or RGBA,
        8 bits per channel. Only this piece is kept in memory."""
        left, top, right, bottom = (int(round(v)) for v in box)
        left, top = max(0, min(left, self.width - 1)), max(0, min(top, self.height - 1))
        right, bottom = max(left + 1, min(right, self.width)), max(top + 1, min(bottom, self.height))
        piece = self._open().crop(left, top, right - left, bottom - top)
        # 16-bit scans, CMYK and greyscale: to 8-bit sRGB, keeping an alpha channel.
        if piece.interpretation not in ("srgb", "b-w") or piece.format != "uchar":
            piece = piece.colourspace("srgb")
        if piece.format != "uchar":
            piece = piece.cast("uchar")
        if piece.bands in (1, 2):  # greyscale (with alpha): to RGB(A)
            piece = piece.colourspace("srgb")
        mode = {3: "RGB", 4: "RGBA"}.get(piece.bands)
        if mode is None:
            piece = piece.extract_band(0, n=3)
            mode = "RGB"
        return Image.frombytes(mode, (piece.width, piece.height), piece.write_to_memory())
