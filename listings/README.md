# Listing packs — contract

Six packs: `etsy/{ice,cash,networth}.json` + `gumroad/{ice,cash,networth}.json`.

## Schema

| Field | Rule |
|---|---|
| `product` | `ice` \| `cash` \| `networth` |
| `marketplace` | `etsy` \| `gumroad` |
| `price_usd` | approved plan prices: ice $14, cash $12, networth $14 |
| `title` | keyword-first, <= 140 chars |
| `description` | contains the exact compliance disclaimer sentence |
| `tags` | exactly 13, each <= 20 chars, each traceable to `evidence` or the description |
| `images` | paths to committed renders (the renders ARE the listing images) |
| `buy_url` | PLACEHOLDER (`example.com`) — see below |
| `evidence` | source ledger entries with dates (traceability for every claim) |

## Handoff (surf-studio lane)

- **Nothing is posted from this repo.** `buy_url` values are placeholders;
  surf-studio replaces them with live listing URLs at submission time and
  must NOT ship any listing before `landing/pages/disclosure.html` and
  `landing/pages/privacy.html` are deployed (they are linked from the
  landing footer before any buy link).
- Etsy title limit is 140 chars and tag limit is 20 chars/13 tags — the
  packs already conform; the `tests/test_listings.py` enforces it.
- The sample renders in `renders/` are the listing images. Regenerate with
  `python -m paperlife.render_samples` (from `products/paperlife`).
