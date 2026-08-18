# PaperLife

Printable money-life PDF kits, generated from your answers — not endless
blank forms. Three products, one shared renderer:

| Product | Price | Pages | What it does |
|---|---|---|---|
| **ICE Binder** | $14 | 8 | In-case-of-emergency binder: family info, contacts, medical, insurance, finances, digital accounts, wishes, document checklist. The generator asks **12 short questions**; the rest is labeled fill-in space. Generic — no state-specific sections. |
| **Cash-Stuffing Allocator Kit** | $12 | 6 | Income → per-envelope amounts **to the cent**, printable envelope labels, tracker sheets. Category weights **must sum to exactly 100%** or the generator refuses to run. |
| **Net-Worth Certificate** | $14 | 1 | Assets − liabilities = net worth, thousands separators, honest negatives, signature line, certificate border. |

Every PDF page carries a compliance footer. The PNG previews in `renders/`
are rendered from the **same page objects** as the PDFs — the listing
images are the product, never mockups or stock.

## Requirements

- Python 3.10+ (built and tested on 3.13)
- `pip install -r requirements.txt`  (reportlab; pillow for previews)
- Dev/tests: `pip install -r requirements-dev.txt` (pytest)

## Quick start

From the repo root:

```powershell
# ICE binder (8 pages, US Letter) — all 12 fields optional, blanks stay blank
python -m engine.paperlife --product ice --name "Alex Rivera" --blood-type "O+" --out renders/

# A4 instead
python -m engine.paperlife --product ice --name "Alex Rivera" --paper a4 --out renders/

# Cash allocator — weights MUST total exactly 100%
python -m engine.paperlife --product cash --income 500.17 `
    --weight "Housing=27.5" --weight "Food=12.5" --weight "Transportation=7.5" `
    --weight "Utilities=10" --weight "Savings=15" --weight "Fun=10" `
    --weight "Gifts=7.5" --weight "Emergency=10" --out renders/ --preview

# Net-worth certificate (negative values are shown honestly)
python -m engine.paperlife --product networth --name "Maya Chen" `
    --as-of 2026-08-16 --assets 1234567.89 --liabilities 234567.89 --out renders/

# Field values from a JSON file (any product):
python -m engine.paperlife --product ice --json my-fields.json --out renders/

# Interactive mode — prompts for the 12 ICE fields (or missing cash/networth fields)
python -m engine.paperlife --product ice
```

Or from inside `products/paperlife` (same commands, `python -m paperlife`):
`python -m paperlife --product cash --income 2000 --weight "A=60" --weight "B=40" --out out/`

## Windows one-click app (download bundle)

`dist/paperlife.exe` is a one-file Windows build (PyInstaller, ~22 MB) of the
same CLI, included in the customer download bundle for the ICE binder. Double-
click it and it asks the 12 short questions and prints `ice_binder_letter.pdf`
next to the app; all CLI flags work too
(`paperlife.exe --product cash --income 2000 --weight "A=60" --weight "B=40" --out out`).

Rebuild:

```powershell
python -m PyInstaller --onefile --name paperlife --paths . `
  --add-data "paperlife/fonts;paperlife/fonts" `
  --distpath dist --workpath build/pyinstaller --specpath build build/launcher.py
```

Exit codes: `0` success · `1` runtime error · `2` invalid input (bad weights,
non-decimal amounts, amounts finer than a cent).

## Regenerating the sample renders + landing images

```powershell
cd products/paperlife
python -m paperlife.render_samples
```

Deterministic: rewrites `renders/` (PDFs + PNG previews) and syncs
`landing/assets/img/`. The renders ARE the Etsy/Gumroad listing images.

## Tests

```powershell
cd products/paperlife
python -m pytest tests -q        # 96 tests
node landing/verify-render.mjs   # landing overflow check, 375/768/1280 (requires playwright)
```

Golden invariants covered: allocator sum + leftover == income **exactly**
across $100 / $500.17 / $2000.00 / 13 odd-weight categories; weights ≠ 100%
is a hard error; net-worth positive/negative/zero; PDF page counts (ICE ≥ 8,
cash ≥ 6, certificate = 1) for Letter and A4; the compliance disclaimer on
**every** PDF page (verified in the raw bytes); fail-closed text overflow
with a geometry audit of every drawn primitive; listing pack shape
(titles ≤ 140 chars, 13 tags ≤ 20 chars, traceable tags, prices); landing
structure (disclosure + privacy live and linked before buy links).

## Layout

```
paperlife/            # the Python package (builders + shared renderer)
  theme.py            # one layout model, PDF + PNG backends, footer
  money.py            # exact integer-cent math
  ice.py / cash.py / networth.py / freebie.py
  cli.py / pdfout.py / previews.py / samples.py / render_samples.py
build/                # PyInstaller entry (launcher.py) + build artifacts
dist/                 # paperlife.exe — the Windows one-click app (ships in the bundle)
listings/             # 3 Etsy + 3 Gumroad packs (JSON) — surf-studio submits
landing/              # the money page (privacy + disclosure live)
renders/              # sample PDFs + PNG previews (the listing images)
tests/                # pytest golden suite
```

## Compliance

- Every PDF page, every listing, and the landing footer carry:
  *"Organizational tools, not legal or financial documents. Not legal
  advice — verify requirements with your state or a licensed professional."*
- The ICE binder is **generic**: no state-specific legal content until
  state rule tables are verified (a gated future build, not this one).
- No fabricated stats anywhere: every figure on the landing page is dated
  and sourced to the wave evidence ledger (idea card v-20260815-13).
- Prices ($14 / $12 / $14) are the approved plan prices; no other figures
  are invented.

## License

MIT — see `LICENSE`. The bundled Vera Sans fonts carry the Bitstream Vera
license (`paperlife/fonts/bitstream-vera-license.txt`).
