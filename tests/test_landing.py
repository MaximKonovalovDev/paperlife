"""Landing page structural tests: disclosure/privacy live and linked BEFORE
any buy link, disclaimer in footer, wedge form present, claims sourced."""

import pathlib
import re

from paperlife.theme import DISCLAIMER_ASCII_PROBE

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANDING = ROOT / "landing"


def test_landing_exists_and_is_single_page():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    assert "<html" in html
    assert html.count("<main") == 1  # one page, one job


def test_privacy_and_disclosure_live_before_buy_links():
    for page in ("privacy.html", "disclosure.html"):
        assert (LANDING / "pages" / page).exists(), f"{page} missing"
        content = (LANDING / "pages" / page).read_text(encoding="utf-8")
        assert DISCLAIMER_ASCII_PROBE in content, f"{page} must carry the disclaimer"
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    assert "pages/privacy.html" in html
    assert "pages/disclosure.html" in html
    # buy links exist only as documented placeholders
    assert html.count('href="https://example.com/') == 3  # exactly the 3 kits
    assert 'data-pack="listings/' in html


def test_disclaimer_in_landing_footer():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    footer = html.split("<footer")[1]
    assert DISCLAIMER_ASCII_PROBE in footer


def test_wedge_form_captures_email():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    assert 'name="email"' in html and 'type="email"' in html
    assert "emergency-contact-card" in html
    js = (LANDING / "assets" / "js" / "capture.js").read_text(encoding="utf-8")
    assert "FORM_ENDPOINT" in js
    assert "forms/submit" in js  # documented deploy seam (relative stub, mailto fallback)
    assert "https://example.com" not in js  # the form never POSTs to a placeholder domain


def test_claims_sourced_no_fabricated_stats():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    # every stat carries data-source with the wave date
    assert 'data-source="marketplace pass 3, Etsy market pages"' in html
    assert "2026-08-15" in html
    assert "idea card v-20260815-13" in html
    # no fake testimonials
    assert "testimonial" not in html.lower()
    assert "★★★★★" not in html


def test_one_cta_per_card():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    cards = html.split('<article class="card">')[1:]
    assert len(cards) == 3
    for card in cards:
        assert card.count('<a class="cta"') == 1, "card must have exactly one CTA"


def test_card_prices_match_plan():
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    assert "$14 <span>one-time</span>" in html  # ice
    assert "$12 <span>one-time</span>" in html  # cash
    assert "$14 <span>one-time</span>" in html  # networth


def test_landing_images_are_real_render_pngs():
    for img in ["ice_01_cover_letter.png", "cash_02_worksheet_letter.png",
                "cert_01_letter.png", "emergency_contact_card.png"]:
        p = LANDING / "assets" / "img" / img
        assert p.exists(), f"missing {img}"
        assert p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
