"""Shared PaperLife renderer: one layout model, two output backends.

A product builder returns a list of *page draw functions*. Each draw function
receives a `Page` (backend context) plus its 1-based page number and the total
page count, and draws using the primitives below.

Two backends consume the same draw functions:

* PDFBackend  -> reportlab canvas (uncompressed content streams, so tests can
                 verify text presence per page in the raw bytes)
* PNGBackend  -> Pillow image (the committed listing images are rendered from
                 the SAME page objects as the PDFs — the renders are the
                 product, never mockups)

Both backends use the same vendored Vera Sans TrueType files, so glyph
metrics are identical and the previews are faithful.

All coordinates are in points with a top-left origin (HTML-like).
"""

from __future__ import annotations

import pathlib
from typing import Callable, Sequence

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = pathlib.Path(__file__).parent / "fonts"
FONT_REGULAR = str(FONT_DIR / "Vera.ttf")
FONT_BOLD = str(FONT_DIR / "VeraBd.ttf")
FONT_LICENSE = FONT_DIR / "bitstream-vera-license.txt"

# Required compliance wording — every PDF page, every listing, landing footer.
DISCLAIMER = (
    "Organizational tools, not legal or financial documents. "
    "Not legal advice \u2014 verify requirements with your state "
    "or a licensed professional."
)
# ASCII prefix of the disclaimer, used for raw-byte text verification in tests.
DISCLAIMER_ASCII_PROBE = "Organizational tools, not legal or financial documents."

BRAND = "PaperLife"

PAGE_SIZES = {"letter": (612.0, 792.0), "a4": (595.27, 841.89)}
MARGIN = 54.0
LINE_H = 1.32  # line height as a multiple of font size

# Palette (RGB 0-255).
INK = (27, 42, 65)          # deep navy
ACCENT = (23, 114, 109)     # teal
MUTED = (99, 108, 122)
LINE = (205, 212, 222)
FAINT = (238, 242, 247)     # header row fill
BAD = (146, 43, 33)         # honest negative figures


class TextOverflow(Exception):
    """Raised when a text box does not fit its bounds — fail-closed overflow guard."""


def _register_fonts() -> None:
    for name, path in (("PaperLifeVera", FONT_REGULAR), ("PaperLifeVeraBd", FONT_BOLD)):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
        except Exception:  # already registered
            pass


_register_fonts()
FONT_NAMES = {"normal": "PaperLifeVera", "bold": "PaperLifeVeraBd"}


def wrap_lines(measure: Callable[[str], float], text: str, width: float) -> list[str]:
    """Greedy word wrap against a backend measure function."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if measure(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


class Page:
    """A single page context — all coordinates are top-left, in points."""

    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h

    # --- primitives: implemented by subclasses --------------------------
    def rect(self, x, y, w, h, fill=None, stroke=None, width=1.0):  # pragma: no cover
        raise NotImplementedError

    def line(self, x1, y1, x2, y2, color=LINE, width=1.0):  # pragma: no cover
        raise NotImplementedError

    def _text(self, x, y, s, size, font, color, align):  # pragma: no cover
        raise NotImplementedError

    def measure(self, s, size, font) -> float:  # pragma: no cover
        raise NotImplementedError

    # --- shared layout helpers ------------------------------------------
    def text(self, x, y, s, size=10.0, font="normal", color=INK, align="left"):
        """Draw a single line; y is the top of the line box."""
        self._text(x, y, s, size, font, color, align)

    def textbox(self, x, y, w, h, s, size=10.0, font="normal", color=INK,
                align="left", lh=LINE_H):
        """Draw wrapped text inside a box; raise TextOverflow if it does not fit."""
        if not s.strip():
            return
        measure = lambda t: self.measure(t, size, font)
        lines = wrap_lines(measure, s, w)
        line_h = size * lh
        if len(lines) * line_h > h + 0.5:
            raise TextOverflow(
                f"text does not fit box ({len(lines)} lines x {line_h:.1f}pt > {h:.1f}pt): {s[:60]}..."
            )
        for i, ln in enumerate(lines):
            self.text(x, y + i * line_h, ln, size=size, font=font, color=color, align=align)

    def table(self, x, y, w, rows, col_widths=None, header=None,
              row_h=26.0, header_h=24.0, size=9.5, hsize=9.5,
              header_fill=FAINT, pad=6.0):
        """Grid table with optional header; cells wrap and fail closed on overflow.

        ``rows`` is a list of lists of strings. Column widths default to equal.
        """
        n_cols = len(rows[0]) if rows else (len(header) if header else 1)
        if col_widths is None:
            col_widths = [w / n_cols] * n_cols
        assert len(col_widths) == n_cols
        top = y
        cursor = y

        def draw_row(cells, heights, fill, cell_size, bold=False):
            row_bottom = cursor + heights
            for i, cell in enumerate(cells):
                cx = x + sum(col_widths[:i])
                cw = col_widths[i]
                if fill is not None:
                    self.rect(cx, cursor, cw, heights, fill=fill)
                if cell:
                    # box height = row height minus padding, so wrapped cells
                    # still fit; overflow past the row still raises TextOverflow.
                    self.textbox(cx + pad, cursor + 2, cw - 2 * pad, heights - 4,
                                 str(cell), size=cell_size,
                                 font=("bold" if bold else "normal"))
                self.rect(cx, cursor, cw, heights, fill=None, stroke=LINE, width=0.75)
            self.line(x, cursor, x + w, cursor, color=LINE, width=0.75)
            return heights

        if header:
            draw_row(header, header_h, fill=header_fill, cell_size=hsize, bold=True)
        for cells in rows:
            draw_row(list(cells), row_h, fill=None, cell_size=size)
        self.line(x, cursor, x + w, cursor, color=LINE, width=0.75)
        return cursor

    def dotted(self, x1, x2, y, color=MUTED):
        """Dotted leader line for certificate rows."""
        dot_w = self.measure(".", 10.0, "normal") or 3.0
        step = dot_w * 2.2
        t = x1
        while t < x2 - dot_w:
            self._text(t, y - 1.0, ".", 10.0, "normal", color, "left")
            t += step

    # --- shared furniture -------------------------------------------------
    def head(self, title: str, label: str, page_no: int, total: int):
        """Standard content-page header (title left, page label right).

        NOTE: callers draw the footer themselves (foot) so it appears exactly
        once per page.
        """
        self.rect(0, 0, self.w, 6, fill=ACCENT)
        self.text(MARGIN, 40, title, size=15.0, font="bold")
        self.text(self.w - MARGIN, 40, label, size=9.0, color=MUTED, align="right")
        self.line(MARGIN, 62, self.w - MARGIN, 62, color=LINE, width=0.75)

    def foot(self, page_no: int, total: int):
        """Mandatory footer: brand + page number + compliance disclaimer."""
        y = self.h - 46.0
        self.line(MARGIN, y, self.w - MARGIN, y, color=LINE, width=0.75)
        self.text(MARGIN, y + 8, f"{BRAND} \u2014 organizational printables",
                  size=7.5, color=MUTED)
        self.text(self.w - MARGIN, y + 8, f"Page {page_no} of {total}",
                  size=7.5, color=MUTED, align="right")
        self.textbox(MARGIN, y + 18, self.w - 2 * MARGIN, 26, DISCLAIMER,
                     size=7.0, color=MUTED)


class PDFPage(Page):
    def __init__(self, c: rl_canvas.Canvas, w: float, h: float):
        super().__init__(w, h)
        self._c = c

    def _flip(self, y, hh=0.0):
        return self.h - y - hh

    def rect(self, x, y, w, h, fill=None, stroke=None, width=1.0):
        c = self._c
        if fill is not None:
            c.setFillColorRGB(*(v / 255 for v in fill))
            c.rect(x, self._flip(y, h), w, h, stroke=0, fill=1)
        if stroke is not None:
            c.setStrokeColorRGB(*(v / 255 for v in stroke))
            c.setLineWidth(width)
            c.rect(x, self._flip(y, h), w, h, stroke=1, fill=0)

    def line(self, x1, y1, x2, y2, color=LINE, width=1.0):
        self._c.setStrokeColorRGB(*(v / 255 for v in color))
        self._c.setLineWidth(width)
        self._c.line(x1, self._flip(y1), x2, self._flip(y2))

    def _text(self, x, y, s, size, font, color, align):
        c = self._c
        c.setFont(FONT_NAMES[font], size)
        c.setFillColorRGB(*(v / 255 for v in color))
        if align == "right":
            x = x - self.measure(s, size, font)
        elif align == "center":
            x = x - self.measure(s, size, font) / 2
        c.drawString(x, self._flip(y) - size * 0.80, s)

    def measure(self, s, size, font):
        return pdfmetrics.stringWidth(s, FONT_NAMES[font], size)


class PDFBackend:
    def __init__(self, path, paper="letter", title=None):
        w, h = PAGE_SIZES[paper]
        self._c = rl_canvas.Canvas(str(path), pagesize=(w, h), pageCompression=0)
        if title:
            self._c.setTitle(title)
        self.w, self.h = w, h
        self._pages = 0

    def page(self) -> Page:
        if self._pages > 0:
            self._c.showPage()  # every page context is a real PDF page
        self._pages += 1
        return PDFPage(self._c, self.w, self.h)

    def finish(self):
        self._c.save()


class PNGPage(Page):
    def __init__(self, img: Image.Image, scale: float):
        super().__init__(img.width / scale, img.height / scale)
        self._img = img
        self.image = img
        self._d = ImageDraw.Draw(img)
        self._s = scale
        self._fonts = {
            "normal": ImageFont.truetype(FONT_REGULAR, 10),
            "bold": ImageFont.truetype(FONT_BOLD, 10),
        }

    def _font(self, size, font):
        key = (font, int(size * self._s))
        if key not in self._fonts:
            path = FONT_BOLD if font == "bold" else FONT_REGULAR
            self._fonts[key] = ImageFont.truetype(path, int(size * self._s))
        return self._fonts[key]

    def rect(self, x, y, w, h, fill=None, stroke=None, width=1.0):
        s = self._s
        box = (x * s, y * s, (x + w) * s, (y + h) * s)
        if fill is not None:
            self._d.rectangle(box, fill=fill)
        if stroke is not None:
            self._d.rectangle(box, outline=stroke, width=max(1, round(width * s)))

    def line(self, x1, y1, x2, y2, color=LINE, width=1.0):
        s = self._s
        self._d.line((x1 * s, y1 * s, x2 * s, y2 * s), fill=color,
                     width=max(1, round(width * s)))

    def _text(self, x, y, s, size, font, color, align):
        f = self._font(size, font)
        sc = self._s
        if align == "right":
            x = x - self.measure(s, size, font)
        elif align == "center":
            x = x - self.measure(s, size, font) / 2
        self._d.text((x * sc, y * sc), s, font=f, fill=color)

    def measure(self, s, size, font):
        return self._d.textlength(s, font=self._font(size, font)) / self._s


class PNGBackend:
    def __init__(self, scale: float = 2.0):
        self._scale = scale

    def page(self, w, h) -> Page:
        img = Image.new("RGB", (int(w * self._scale), int(h * self._scale)),
                        color=(255, 255, 255))
        return PNGPage(img, self._scale)


PageFn = Callable[[Page, int, int], None]
