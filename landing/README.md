# PaperLife landing page

Static, mobile-first, zero-dependency page for the three PaperLife kits.

## Layout

```
landing/
├── index.html          # one job: proof → kits → free-card wedge
├── pages/
│   ├── privacy.html    # LIVE before any money link (non-negotiable)
│   └── disclosure.html # same gate — linked in header + footer
├── assets/
│   ├── css/style.css
│   ├── js/capture.js   # wedge form (endpoint = deploy seam, see forms/)
│   └── img/            # REAL renders of the generated PDFs (no stock)
├── forms/README.md     # capture contract + wiring status
└── verify-render.mjs   # playwright overflow check (375/768/1280)
```

## Rules this page obeys

- **One CTA per card** — each kit card has exactly one buy link; the hero has
  one CTA (the free card).
- **Claims sourced** — every market figure carries its source + date
  (`data-source` attribute). Nothing invented.
- **Images are renders** — `assets/img/*.png` are the actual generator
  outputs (synced by `python -m paperlife.render_samples`).
- **Disclosure + privacy are live and linked before any buy link** — both
  pages ship with this landing and are linked from the header nav and footer.

## Buy links

`href` values in the kit cards are **placeholders** (`example.com`). The
live Etsy/Gumroad URLs are assigned by surf-studio at listing submission;
`data-pack` on each buy link names the listing pack
(`listings/etsy/<product>.json`). Nothing is posted from this repo.

## Verify renders (no overflow)

```powershell
npm install                # installs playwright (dev dependency)
npx playwright install chromium   # once, downloads the browser
npm run verify-render
```

Loads the page at 375 / 768 / 1280 px and fails if `scrollWidth` exceeds the
viewport — the same check the studio pipeline runs before deploy.
