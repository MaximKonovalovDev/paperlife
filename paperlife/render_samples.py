"""Regenerate every committed render + landing image, deterministically.

    python -m paperlife.render_samples

Writes:
    renders/ice/ice_binder_letter.pdf  (+ 8 PNG previews + 1 A4 cover preview)
    renders/cash/cash_kit_letter.pdf   (+ 6 PNG previews + 1 A4 cover preview)
    renders/networth/*.pdf             (6 certificate variants + PNG previews)
    renders/freebie/emergency_contact_card.pdf  (+ PNG)
    landing/assets/img/*.png           (synced copies for the landing page)
"""

from __future__ import annotations

import pathlib
import shutil

from .ice import build_ice_pages
from .cash import build_cash_pages
from .networth import build_cert_page
from .freebie import build_emergency_card
from .pdfout import write_pdf
from .previews import render_preview
from .samples import (SAMPLE_ICE, SAMPLE_CASH, SAMPLE_CERT_VARIANTS, SAMPLE_FREEBEE)

ROOT = pathlib.Path(__file__).resolve().parent.parent
RENDERS = ROOT / "renders"
LANDING_IMG = ROOT / "landing" / "assets" / "img"

ICE_PAGE_NAMES = [
    "ice_01_cover", "ice_02_contacts", "ice_03_medical", "ice_04_insurance",
    "ice_05_finances", "ice_06_digital", "ice_07_wishes", "ice_08_checklist",
]
CASH_PAGE_NAMES = [
    "cash_01_cover", "cash_02_worksheet", "cash_03_labels",
    "cash_04_extras", "cash_05_tracker", "cash_06_goals",
]


def _render_all_pages(page_fns, out_dir, stem, page_names, paper="letter"):
    """Write one PDF plus one PNG per page (named page_names)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{stem}_{paper}.pdf"
    write_pdf(page_fns, pdf_path, paper=paper, title=f"PaperLife {stem}")
    png_dir = out_dir / "png"
    png_dir.mkdir(parents=True, exist_ok=True)
    assert len(page_names) == len(page_fns)
    for i, fn in enumerate(page_fns):
        png = png_dir / f"{page_names[i]}_{paper}.png"
        render_preview([fn], png, paper=paper, scale=2.0)
    return pdf_path


def main() -> None:
    # ICE binder: full 8-page PDF (letter) + one A4 cover preview for the pack.
    ice_pages = build_ice_pages(SAMPLE_ICE)
    _render_all_pages(ice_pages, RENDERS / "ice", "ice_binder", ICE_PAGE_NAMES)
    (RENDERS / "ice" / "png" / "ice_cover_a4.png").parent.mkdir(parents=True, exist_ok=True)
    render_preview([ice_pages[0]], RENDERS / "ice" / "png" / "ice_cover_a4.png",
                   paper="a4", scale=2.0)
    write_pdf(ice_pages, RENDERS / "ice" / "ice_binder_a4.pdf", paper="a4",
              title="PaperLife ICE Binder (A4)")

    # Cash kit: full 6-page PDF + A4 cover preview.
    cash_pages = build_cash_pages(SAMPLE_CASH["income"], SAMPLE_CASH["weights"])
    _render_all_pages(cash_pages, RENDERS / "cash", "cash_kit", CASH_PAGE_NAMES)
    render_preview([cash_pages[0]], RENDERS / "cash" / "png" / "cash_cover_a4.png",
                   paper="a4", scale=2.0)
    write_pdf(cash_pages, RENDERS / "cash" / "cash_kit_a4.pdf", paper="a4",
              title="PaperLife Cash Stuffing Kit (A4)")

    # Net worth: six certificate variants (positive, positive, zero, negative,
    # A4, odd-cents) — each its own single-page PDF + preview.
    cert_dir = RENDERS / "networth"
    cert_dir.mkdir(parents=True, exist_ok=True)
    (cert_dir / "png").mkdir(parents=True, exist_ok=True)
    papers = ["letter", "letter", "letter", "letter", "a4", "letter"]
    for i, (variant, paper) in enumerate(zip(SAMPLE_CERT_VARIANTS, papers)):
        stem = f"cert_{i + 1:02d}_{paper}"
        cert_pages = build_cert_page(variant, paper=paper)
        write_pdf(cert_pages, cert_dir / f"{stem}.pdf", paper=paper,
                  title="PaperLife Certificate of Net Worth")
        render_preview(cert_pages, cert_dir / "png" / f"{stem}.png", paper=paper, scale=2.0)

    # Freebie card (landing wedge payload).
    free_dir = RENDERS / "freebie"
    free_dir.mkdir(parents=True, exist_ok=True)
    (free_dir / "png").mkdir(parents=True, exist_ok=True)
    card_pages = build_emergency_card(SAMPLE_FREEBEE)
    write_pdf(card_pages, free_dir / "emergency_contact_card.pdf",
              title="PaperLife Emergency Contact Card")
    render_preview(card_pages, free_dir / "png" / "emergency_contact_card.png", scale=2.0)

    # Sync previews into the landing page images (single source of truth).
    LANDING_IMG.mkdir(parents=True, exist_ok=True)
    wanted = {
        "ice": [f"{name}_letter.png" for name in ICE_PAGE_NAMES] + ["ice_cover_a4.png"],
        "cash": [f"{name}_letter.png" for name in CASH_PAGE_NAMES] + ["cash_cover_a4.png"],
        "networth": [f"cert_{i:02d}_{p}.png" for i, p in
                     enumerate(["letter", "letter", "letter", "letter", "a4", "letter"], start=1)],
        "freebie": ["emergency_contact_card.png"],
    }
    for product, names in wanted.items():
        for name in names:
            src = RENDERS / product / "png" / name
            dst = LANDING_IMG / name
            shutil.copy2(src, dst)

    print(f"renders -> {RENDERS}")
    print(f"landing images -> {LANDING_IMG}")


if __name__ == "__main__":
    main()
