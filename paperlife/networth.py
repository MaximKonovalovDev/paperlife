"""Net-worth certificate builder — one page, honest math.

assets - liabilities = net worth, rendered with thousands separators and an
unmistakable negative sign when the number is negative (never hidden).
"""

from __future__ import annotations

from datetime import date

from .theme import PageFn, Page, MARGIN, INK, ACCENT, MUTED, LINE, BAD
from .money import dollars_to_cents, net_worth, fmt_usd


def build_cert_page(fields: dict, paper: str = "letter") -> list[PageFn]:
    """fields: name (optional), as_of (YYYY-MM-DD, optional), assets, liabilities."""
    assets_cents = dollars_to_cents(fields["assets"])
    liabilities_cents = dollars_to_cents(fields["liabilities"])
    worth = net_worth(assets_cents, liabilities_cents)

    name = str(fields.get("name") or "").strip() or "\u2014 \u2014 \u2014 \u2014 \u2014 \u2014"
    as_of_raw = str(fields.get("as_of") or "").strip()
    if as_of_raw:
        as_of = date.fromisoformat(as_of_raw).strftime("%B %d, %Y")
    else:
        as_of = "\u2014 \u2014 \u2014 \u2014 \u2014 \u2014 \u2014"

    w = {"letter": 612.0, "a4": 595.27}[paper]

    def page(ctx: Page, n: int, total: int):
        # certificate border: outer double frame + accent inner rule
        ctx.rect(24, 24, ctx.w - 48, ctx.h - 88, fill=None, stroke=INK, width=2.0)
        ctx.rect(30, 30, ctx.w - 60, ctx.h - 100, fill=None, stroke=INK, width=0.75)
        ctx.rect(36, 36, ctx.w - 72, ctx.h - 112, fill=None, stroke=ACCENT, width=1.0)

        cx = ctx.w / 2
        ctx.text(cx, 86, "P A P E R L I F E", size=10.0, font="bold", color=ACCENT,
                 align="center")
        ctx.text(cx, 108, "CERTIFICATE", size=21.0, font="bold", align="center")
        ctx.text(cx, 134, "OF NET WORTH", size=15.0, color=MUTED, align="center")
        ctx.line(cx - 90, 152, cx + 90, 152, color=ACCENT, width=1.0)

        ctx.text(cx, 196, "This certifies that", size=11.0, color=MUTED, align="center")
        ctx.text(cx, 222, name, size=19.0, font="bold", align="center")
        ctx.text(cx, 248, f"as of {as_of}", size=11.0, color=MUTED, align="center")

        # money rows with dotted leaders
        y = 306
        row_w = 320.0
        x1 = cx - row_w / 2
        x2 = cx + row_w / 2

        def money_row(label, cents, ypos, bold=False, color=INK):
            ctx.text(x1, ypos, label, size=11.5, font=("bold" if bold else "normal"),
                     color=color)
            ctx.dotted(x1 + 90, x2 - 120, ypos + 3, color=LINE)
            ctx.text(x2, ypos, fmt_usd(cents), size=11.5,
                     font=("bold" if bold else "normal"), color=color, align="right")

        money_row("Assets", assets_cents, y)
        money_row("Liabilities", liabilities_cents, y + 30)
        ctx.line(x1, y + 52, x2, y + 52, color=INK, width=1.0)
        money_row("Net Worth", worth, y + 66, bold=True,
                  color=BAD if worth < 0 else ACCENT)
        if worth < 0:
            ctx.text(cx, y + 92, "Net worth is negative \u2014 shown honestly, not hidden.",
                     size=9.5, color=BAD, align="center")
        else:
            ctx.text(cx, y + 92, "Signed and dated on the line below.",
                     size=9.5, color=MUTED, align="center")

        # signature line
        sy = ctx.h - 190
        ctx.line(x1, sy, x2 - 60, sy, color=INK, width=1.0)
        ctx.text(x1, sy + 8, "Signature", size=10.0, color=MUTED)
        ctx.line(x2 - 40, sy, x2, sy, color=INK, width=1.0)
        ctx.text(x2 - 20, sy + 8, "Date", size=10.0, color=MUTED)

        ctx.text(cx, sy + 44, "A record of personal net worth on the date shown.",
                 size=9.0, color=MUTED, align="center")
        ctx.foot(n, total)

    return [page]
