"""Golden PDF tests: page counts, per-page disclaimer, overflow fail-closed,
geometry within page bounds, and non-blank previews.

Layout overflow is fail-closed by design (TextOverflow raises); these tests
also run a recording backend that audits EVERY drawn primitive for page
bounds, so 'no text overflow' is a mechanical guarantee, not a visual claim.
"""

import pathlib
import tempfile

import pytest

from paperlife import theme
from paperlife.theme import DISCLAIMER_ASCII_PROBE, LINE_H, Page, TextOverflow
from paperlife.ice import build_ice_pages, ICE_FIELDS
from paperlife.cash import build_cash_pages
from paperlife.networth import build_cert_page
from paperlife.freebie import build_emergency_card
from paperlife.pdfout import write_pdf, count_pages, count_text
from paperlife.previews import render_preview
from paperlife.samples import SAMPLE_ICE, SAMPLE_CASH, SAMPLE_CERT_VARIANTS

PRODUCTS = {
    "ice": lambda paper: build_ice_pages(SAMPLE_ICE, paper=paper),
    "cash": lambda paper: build_cash_pages(SAMPLE_CASH["income"], SAMPLE_CASH["weights"], paper=paper),
    "networth": lambda paper: build_cert_page(SAMPLE_CERT_VARIANTS[0], paper=paper),
    "freebie": lambda paper: build_emergency_card({}, paper=paper),
}

MIN_PAGES = {"ice": 8, "cash": 6, "networth": 1, "freebie": 1}


@pytest.mark.parametrize("paper", ["letter", "a4"])
@pytest.mark.parametrize("product", list(MIN_PAGES))
def test_page_counts(product, paper, tmp_path):
    page_fns = PRODUCTS[product](paper)
    assert len(page_fns) >= MIN_PAGES[product], f"{product} page count"
    out = tmp_path / f"{product}_{paper}.pdf"
    write_pdf(page_fns, out, paper=paper)
    assert count_pages(out) == len(page_fns)  # byte-level page count agrees


@pytest.mark.parametrize("paper", ["letter", "a4"])
@pytest.mark.parametrize("product", list(MIN_PAGES))
def test_disclaimer_on_every_page(product, paper, tmp_path):
    """The compliance disclaimer appears at least once per page in the raw PDF."""
    page_fns = PRODUCTS[product](paper)
    out = tmp_path / f"{product}_{paper}.pdf"
    write_pdf(page_fns, out, paper=paper)
    found = count_text(out, DISCLAIMER_ASCII_PROBE)
    assert found >= len(page_fns), f"{product}: {found} footer(s) for {len(page_fns)} pages"


class ProbePage(Page):
    """Recording backend: captures every primitive for a geometry audit."""

    def __init__(self, w, h):
        super().__init__(w, h)
        self.primitives = []

    def rect(self, x, y, w, h, fill=None, stroke=None, width=1.0):
        if fill is not None or stroke is not None:
            self.primitives.append(("rect", x, y, w, h))

    def line(self, x1, y1, x2, y2, color=None, width=1.0):
        self.primitives.append(("line", min(x1, x2), min(y1, y2),
                                abs(x2 - x1), abs(y2 - y1)))

    def _text(self, x, y, s, size, font, color, align):
        w = self.measure(s, size, font)
        if align == "right":
            x = x - w
        elif align == "center":
            x = x - w / 2
        self.primitives.append(("text", x, y, w, size * LINE_H))

    def measure(self, s, size, font):
        from reportlab.pdfbase import pdfmetrics
        return pdfmetrics.stringWidth(s, theme.FONT_NAMES[font], size)


def _audit_bounds(page_fns, paper):
    w, h = theme.PAGE_SIZES[paper]
    probe = ProbePage(w, h)
    for i, fn in enumerate(page_fns):
        fn(probe, i + 1, len(page_fns))
    for kind, x, y, pw, ph in probe.primitives:
        assert x >= -0.5, (kind, x, y, pw, ph)
        assert y >= -0.5, (kind, x, y, pw, ph)
        assert x + pw <= w + 0.5, (kind, x, y, pw, ph)
        assert y + ph <= h + 0.5, (kind, x, y, pw, ph)
        if kind == "text":
            # single-line text must stay inside the content margins
            assert pw <= w - 2 * theme.MARGIN + 0.5, (kind, x, y, pw, ph)
    assert probe.primitives, "page drew nothing"
    return probe.primitives


@pytest.mark.parametrize("paper", ["letter", "a4"])
@pytest.mark.parametrize("product", list(MIN_PAGES))
def test_geometry_within_page_bounds(product, paper):
    _audit_bounds(PRODUCTS[product](paper), paper)


def _worst_case_ice():
    """Long but plausible worst-case inputs — must still fit (fail-closed)."""
    fields = dict(SAMPLE_ICE)
    fields.update({
        "name": "Alexandria Maria-Christina van der Berg-Schneider Jr.",
        "address": "12345 Very Long Street Name Avenue Boulevard, North Anytown, Some State 67890, USA",
        "emergency_name": "Dr. Jordan Alexandra McAllister-Fitzgerald",
        "medications": "Lisinopril 10 mg daily, Metformin 500 mg twice daily, Atorvastatin 20 mg nightly",
        "doctor": "Dr. Priyanka Annapurna Sharma-Chaudhary, MD, FACC",
        "insurance": "Brightway Mutual Health & Life Assurance Company of America",
        "policy": "BWM-88213-01-XYZ-2026-Q4-SUPPLEMENTAL",
    })
    return fields


def test_overflow_fail_closed_worst_case_ice():
    page_fns = build_ice_pages(_worst_case_ice())
    for fn in page_fns:
        probe = ProbePage(*theme.PAGE_SIZES["letter"])
        fn(probe, 1, len(page_fns))  # must NOT raise TextOverflow
    _audit_bounds(page_fns, "letter")


def test_overflow_raises_when_text_cannot_fit():
    """A truly uncontainable string must raise — the guard is real."""
    page = ProbePage(612, 792)
    with pytest.raises(TextOverflow):
        page.textbox(54, 100, 100, 14, "word " * 200, size=10)


def test_worst_case_cash_many_categories():
    """13 odd-weight categories with long names + 3-decimal remainder sum to 100."""
    weights = {f"Category number {i:02d}": "7.69" for i in range(13)}
    weights["Category number 99"] = "0.03"  # 13 * 7.69 + 0.03 == 100.00
    page_fns = build_cash_pages("100000.00", weights)
    _audit_bounds(page_fns, "letter")


def test_networth_negative_variant_renders():
    negative = dict(SAMPLE_CERT_VARIANTS[3])  # Dana Osei: assets < liabilities
    page_fns = build_cert_page(negative)
    _audit_bounds(page_fns, "letter")


@pytest.mark.parametrize("product", list(MIN_PAGES))
def test_previews_not_blank(product, tmp_path):
    """The listing images are real renders: right size, real ink, white paper."""
    page_fns = PRODUCTS[product]("letter")
    out = tmp_path / f"{product}.png"
    render_preview(page_fns, out, paper="letter", scale=2.0)
    from PIL import Image
    from collections import Counter
    img = Image.open(out).convert("RGB")
    assert img.size == (1224, 1584)  # letter at 2x
    counter = Counter(img.get_flattened_data())
    white = counter[(255, 255, 255)]
    ink = 1 - white / (img.size[0] * img.size[1])
    assert 0.02 < ink < 0.45, f"{product}: ink ratio {ink:.1%} (blank or solid page)"


def test_ice_asks_at_most_12_fields():
    assert len(ICE_FIELDS) == 12
    assert all(len(prompt.split()) <= 6 for _, prompt in ICE_FIELDS)  # short prompts


def test_generic_no_state_content(tmp_path):
    """GENERIC product: no state-specific legal content in the PDF bytes.

    The mandated disclaimer does say 'your state' — that is compliance
    wording, not state-specific content. Actual state names and state-form
    language must never appear.
    """
    page_fns = build_ice_pages(SAMPLE_ICE)
    out = tmp_path / "ice.pdf"
    write_pdf(page_fns, out)
    data = out.read_bytes()
    for banned in [b"California", b"Texas", b"Florida", b"New York", b"Illinois",
                   b"Ohio", b"Pennsylvania", b"state form", b"form 706", b"will form"]:
        assert banned not in data, f"state-specific content found: {banned!r}"
    assert b"your state" in data  # only the mandated disclaimer wording
