"""PDF output + byte-level verification helpers.

Content streams are written UNCOMPRESSED (pageCompression=0) so tests can
verify that the compliance disclaimer appears on every page by scanning the
raw bytes — an honest check that does not need a PDF text extractor.
"""

from __future__ import annotations

import pathlib
from typing import Sequence

from .theme import PageFn, PAGE_SIZES, PDFBackend


def write_pdf(page_fns: Sequence[PageFn], path, paper: str = "letter",
              title: str | None = None) -> int:
    """Render pages to a PDF file; returns the page count written."""
    backend = PDFBackend(path, paper=paper, title=title)
    for i, fn in enumerate(page_fns):
        fn(backend.page(), i + 1, len(page_fns))
    backend.finish()
    return len(page_fns)


def count_pages(path) -> int:
    """Page count by scanning the raw PDF structure (no extra dependencies)."""
    data = pathlib.Path(path).read_bytes()
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


def count_text(path, probe: str) -> int:
    """Count occurrences of an ASCII probe in the raw PDF bytes.

    Valid because content streams are uncompressed and standard fonts embed
    ASCII verbatim (non-ASCII is octal-escaped, so probe only ASCII prefixes).
    """
    return pathlib.Path(path).read_bytes().count(probe.encode("ascii"))
