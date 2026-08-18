# Wedge form — capture contract

The free-card form on the landing page POSTs JSON to `FORM_ENDPOINT`
(defined in `assets/js/capture.js`).

## Contract

```
POST {FORM_ENDPOINT}
Content-Type: application/json

{ "email": "you@example.com", "product": "emergency-contact-card", "company": "" }
```

- `email` — the subscriber (validated client-side).
- `product` — always `emergency-contact-card` (future wedges reuse the seam).
- `company` — honeypot; a non-empty value means a bot. Drop the submission.

## Status

**BLOCKED / deploy seam (surf-studio lane):** `FORM_ENDPOINT` is the
relative stub `forms/submit` (it 404s until a backend exists — the form
never posts to a placeholder domain). The freebie PDF payload lives
at `renders/freebie/emergency_contact_card.pdf` — the endpoint response
should deliver that file (download link or attachment) to the address.

Wiring options, in studio order: the studio capture service (if built),
a form service that accepts JSON POSTs, or a small serverless endpoint
owned by surf-studio. Until wired, the form is honest (GigDeduct pattern):
it tries the endpoint, and on any failure falls back to the visitor's mail
client via `mailto:` (MAILTO in `assets/js/capture.js`) with a visible
"capture not wired yet" message. It never pretends the email was captured.

Privacy wording for the endpoint: see `landing/pages/privacy.html`
(email collected only to send the card and optional updates; no resale).
