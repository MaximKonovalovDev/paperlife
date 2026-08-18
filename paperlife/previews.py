"""PNG preview rendering — the listing images.

Each preview is rendered by feeding the SAME page draw functions to the
Pillow backend, so a preview is a faithful raster of the PDF page, not a
mockup. The renders ARE the listing images.
"""

from __future__ import annotations

import pathlib
from typing import Sequence

from .theme import PageFn, PAGE_SIZES, PNGBackend


def render_preview(page_fns: Sequence[PageFn], path, paper: str = "letter",
                   scale: float = 2.0) -> None:
    """Render the first page of a product to a PNG. For single-page products
    this is the whole output; for multi-page products pass a slice (see
    render_samples)."""
    w, h = PAGE_SIZES[paper]
    backend = PNGBackend(scale)
    page = backend.page(w, h)
    page_fns[0](page, 1, len(page_fns))
    page.image.save(str(path))
