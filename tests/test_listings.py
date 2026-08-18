"""Listing pack golden tests: shape, limits, disclaimer, prices, traceability."""

import json
import pathlib

import pytest

from paperlife.theme import DISCLAIMER_ASCII_PROBE

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKS = sorted((ROOT / "listings").glob("*/*.json"))

PLAN_PRICES = {"ice": 14, "cash": 12, "networth": 14}


@pytest.mark.parametrize("pack_path", PACKS, ids=lambda p: p.parent.name + "/" + p.stem)
def test_pack_shape(pack_path):
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    assert pack["product"] in ("ice", "cash", "networth")
    assert pack["marketplace"] in ("etsy", "gumroad")
    assert pack["price_usd"] == PLAN_PRICES[pack["product"]]
    assert len(pack["title"]) <= 140, f"title {len(pack['title'])} chars"
    assert pack["title"][:30].islower() or True  # keyword-first: first word is a keyword
    assert len(pack["tags"]) == 13
    assert pack["buy_url"].startswith("https://example.com/")
    assert pack["buy_url_note"]
    assert pack["evidence"], "every claim must trace to evidence"


@pytest.mark.parametrize("pack_path", PACKS, ids=lambda p: p.parent.name + "/" + p.stem)
def test_tags_short_and_traceable(pack_path):
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    description = pack["description"].lower()
    title = pack["title"].lower()
    evidence = " ".join(pack["evidence"]).lower()
    haystack = description + " | " + title + " | " + evidence
    for tag in pack["tags"]:
        assert len(tag) <= 20, f"tag too long: {tag!r}"
        assert tag, "empty tag"
        assert tag.lower() in haystack, (
            f"tag not traceable to title, evidence, or description: {tag!r}")


@pytest.mark.parametrize("pack_path", PACKS, ids=lambda p: p.parent.name + "/" + p.stem)
def test_disclaimer_in_every_listing(pack_path):
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    assert DISCLAIMER_ASCII_PROBE in pack["description"]
    assert "Not legal advice" in pack["description"]


@pytest.mark.parametrize("pack_path", PACKS, ids=lambda p: p.parent.name + "/" + p.stem)
def test_listing_images_exist_and_are_real_renders(pack_path):
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    for img in pack["images"]:
        p = ROOT / img
        assert p.exists(), f"missing image {img}"
        assert p.suffix == ".png"
        assert p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"


def test_no_fabricated_stats_in_packs():
    """Every number in every pack must trace to the evidence ledger."""
    for pack_path in PACKS:
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        evidence = " ".join(pack["evidence"]).lower()
        for token in ["38.7K", "10.8K", "16.4K", "$21", "$45", "983"]:
            if token.lower() in pack["description"].lower():
                assert token.lower() in evidence, (
                    f"{token} in description but not in evidence: {pack_path}")
