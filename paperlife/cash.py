"""Cash-stuffing allocator kit builder — exact math, printable labels, trackers.

Inputs: income (decimal) and category weights that MUST sum to exactly 100%
(hard error otherwise). Each envelope share is floored to the cent; a
leftover/buffer line keeps  sum(envelopes) + leftover == income  exactly.
"""

from __future__ import annotations

from datetime import date

from .theme import PageFn, Page, MARGIN, INK, ACCENT, MUTED, LINE, FAINT
from .money import allocate, fmt_usd, parse_weight


def build_cash_pages(income: str | int, weights: dict, paper: str = "letter") -> list[PageFn]:
    """weights: ordered dict {category: weight-percent-as-string-or-Decimal}."""
    names = list(weights.keys())
    wts = [parse_weight(v) for v in weights.values()]
    income_cents = _cents(income)
    envelopes, leftover = allocate(income_cents, wts)
    rows = list(zip(names, [str(w) for w in wts], envelopes))

    w = {"letter": 612.0, "a4": 595.27}[paper]
    m = MARGIN
    cw = w - 2 * m

    # ---------------------------------------------------------------- 1/6
    def page_cover(ctx: Page, n: int, total: int):
        ctx.rect(0, 0, ctx.w, 8, fill=ACCENT)
        ctx.text(m, 40, "PaperLife \u2014 Cash Stuffing", size=9.0, color=MUTED)
        ctx.text(ctx.w - m, 40, "PRINT \u00b7 FILL \u00b7 ENVELOPE \u00b7 TRACK",
                 size=9.0, color=MUTED, align="right")
        ctx.text(ctx.w / 2, 128, "Cash Stuffing Allocator Kit",
                 size=28.0, font="bold", align="center")
        ctx.text(ctx.w / 2, 162, "Exact allocation math + printable labels + tracker sheets",
                 size=12.0, color=MUTED, align="center")
        ctx.line(m, 190, ctx.w - m, 190, color=ACCENT, width=1.5)

        y = 224
        ctx.text(m, y, "Monthly income", size=8.5, font="bold", color=MUTED)
        ctx.text(m, y + 14, fmt_usd(income_cents), size=16.0, font="bold")
        ctx.text(ctx.w - m, y + 14,
                  f"Date prepared: {date.today():%B %d, %Y}", size=10.0,
                  color=MUTED, align="right")

        y = 292
        ctx.text(m, y, "How it works", size=12.0, font="bold")
        steps = [
            "1.  Set your category weights \u2014 they must add up to exactly 100%.",
            "2.  The worksheet shows each envelope's exact dollar amount.",
            "3.  Cut the labels, tape them on envelopes, stuff the cash.",
            "4.  Track spending and savings on the tracker sheets.",
        ]
        for i, s in enumerate(steps):
            ctx.text(m, y + 26 + i * 24, s, size=10.5)

        y = 292 + 26 + 4 * 24 + 16
        ctx.textbox(m, y, cw, 44,
                    f"Every envelope amount is rounded down to the cent. The "
                    f"'Leftover / buffer' line keeps the total exactly equal to "
                    f"your income: {fmt_usd(sum(envelopes))} in envelopes "
                    f"+ {fmt_usd(leftover)} leftover = {fmt_usd(income_cents)}.",
                    size=10.0, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 2/6
    def page_worksheet(ctx: Page, n: int, total: int):
        ctx.head("Allocation Worksheet", "Cash Stuffing \u00b7 Allocator", n, total)
        ctx.text(m, 86, f"Monthly income: {fmt_usd(income_cents)}",
                 size=12.0, font="bold")

        ty = 118
        header = ["Category", "Weight", "Envelope amount"]
        ctx.table(m, ty, cw, [["", "", ""]] * len(rows),  # placeholder grid for sizing
                  col_widths=[cw * 0.5, cw * 0.2, cw * 0.3],
                  header=header, row_h=26)
        # table() draws the grid + header; the real rows are drawn as text
        # on top so amounts can be right-aligned and the total row styled.
        for i, (name, wstr, cents) in enumerate(rows):
            yy = ty + 24 + i * 26
            ctx.text(m + 8, yy + 7, name, size=10.0)
            ctx.text(m + cw * 0.5 + 8, yy + 7, f"{wstr}%", size=10.0, align="right")
            ctx.text(m + cw * 0.7 + 8, yy + 7, fmt_usd(cents), size=10.0,
                     font="bold", align="right")
            ctx.line(m, yy, m + cw, yy, color=LINE, width=0.75)

        yy = ty + 24 + len(rows) * 26
        ctx.line(m, yy, m + cw, yy, color=LINE, width=0.75)
        ctx.text(m + 8, yy + 7, "Leftover / buffer (rounding)", size=10.0, color=MUTED)
        ctx.text(m + cw * 0.7 + 8, yy + 7, fmt_usd(leftover), size=10.0,
                 color=MUTED, align="right")
        yy += 26
        ctx.line(m, yy, m + cw, yy, color=INK, width=1.25)
        ctx.rect(m, yy, cw, 26, fill=FAINT)
        ctx.text(m + 8, yy + 8, "TOTAL", size=10.5, font="bold")
        ctx.text(m + cw * 0.7 + 8, yy + 8, fmt_usd(income_cents), size=10.5,
                 font="bold", align="right")
        ctx.text(m, yy + 38, "Total must equal your income exactly \u2014 to the cent.",
                 size=9.5, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 3/6 (3+/6 with more categories)
    def _labels_page(items, start_y: float = 110.0):
        def page(ctx: Page, n: int, total: int):
            ctx.head("Envelope Labels", "Cash Stuffing \u00b7 Cut & tape", n, total)
            ctx.textbox(m, 84, cw, 26, "Cut out each label and tape it on an envelope. "
                                       "Leftover / buffer has no envelope \u2014 it is the "
                                       "rounding cushion.",
                        size=9.5, color=MUTED)
            _draw_label_grid(ctx, items, start_y=start_y)
            ctx.foot(n, total)
        return page

    def _draw_label_grid(ctx: Page, items, start_y: float, cols: int = 2, rows_n: int = 5):
        gap = 10.0
        lw = (cw - (cols - 1) * gap) / cols
        lh = 110.0
        for i, (name, amount) in enumerate(items):
            cx = m + (i % cols) * (lw + gap)
            cy = start_y + (i // cols) * (lh + gap)
            ctx.rect(cx, cy, lw, lh, fill=None, stroke=LINE, width=1.0)
            ctx.rect(cx + 4, cy + 4, lw - 8, lh - 8, fill=None, stroke=LINE, width=0.5)
            ctx.text(cx + 14, cy + 18, name, size=11.0, font="bold")
            ctx.text(cx + lw - 14, cy + 18, amount, size=11.0, font="bold",
                     color=ACCENT, align="right")
            ctx.text(cx + 14, cy + 76, "Week of: ________________", size=9.0, color=MUTED)
        for i in range(len(items), cols * rows_n):
            cx = m + (i % cols) * (lw + gap)
            cy = start_y + (i // cols) * (lh + gap)
            ctx.rect(cx, cy, lw, lh, fill=None, stroke=LINE, width=1.0)
            ctx.text(cx + 14, cy + 18, "Category: ______________", size=10.0, color=MUTED)
            ctx.text(cx + 14, cy + 76, "Amount: $_______", size=10.0, color=MUTED)
        return start_y + rows_n * (lh + gap)

    # ---------------------------------------------------------------- 4/6
    def page_extras(ctx: Page, n: int, total: int):
        ctx.head("Extra Labels & Sinking Funds", "Cash Stuffing \u00b7 Extras", n, total)
        ctx.textbox(m, 84, cw, 26, "More labels for categories you add later, plus a "
                                   "sinking fund tracker for known future costs.",
                    size=9.5, color=MUTED)
        _draw_label_grid(ctx, [], start_y=110, cols=2, rows_n=2)
        ty = 110 + 2 * (110 + 10) + 26
        ctx.text(m, ty, "Sinking funds", size=12.0, font="bold")
        ctx.table(m, ty + 22, cw, [["", "", "", ""]] * 5,
                  col_widths=[cw * 0.34, cw * 0.22, cw * 0.22, cw * 0.22],
                  header=["Fund", "Goal amount", "Started", "Saved"], row_h=28)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 5/6
    def page_tracker(ctx: Page, n: int, total: int):
        ctx.head("Monthly Cash Tracker", "Cash Stuffing \u00b7 Tracker", n, total)
        ctx.table(m, 86, cw, [["", "", "", "", ""]] * 12,
                  col_widths=[cw * 0.14, cw * 0.26, cw * 0.18, cw * 0.18, cw * 0.24],
                  header=["Date", "Category", "Planned", "Spent", "Difference"],
                  row_h=28)
        ctx.text(m, 86 + 24 + 12 * 28 + 12, "Difference = Planned \u2212 Spent. "
                                           "Leftover at month end rolls to next month or to savings.",
                 size=9.5, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 6/6
    def page_goals(ctx: Page, n: int, total: int):
        ctx.head("Savings Goals & Monthly Overview", "Cash Stuffing \u00b7 Goals", n, total)
        ty = 86
        ctx.text(m, ty, "Savings goals", size=12.0, font="bold")
        ty = ctx.table(m, ty + 22, cw, [["", "", "", ""]] * 5,
                       col_widths=[cw * 0.34, cw * 0.22, cw * 0.22, cw * 0.22],
                       header=["Goal", "Target amount", "Started", "Completed"], row_h=26)
        ty += 24
        ctx.text(m, ty, "Monthly overview", size=12.0, font="bold")
        ctx.table(m, ty + 22, cw, [["", "", "", ""]] * 12,
                  col_widths=[cw * 0.25, cw * 0.25, cw * 0.25, cw * 0.25],
                  header=["Month", "Allocated", "Spent", "Leftover"], row_h=24)
        ctx.foot(n, total)

    labels = [(name, fmt_usd(c)) for name, _, c in rows] + [("Leftover / buffer", fmt_usd(leftover))]
    labels_pages = [_labels_page(labels[i:i + 10]) for i in range(0, len(labels), 10)]

    return [page_cover, page_worksheet, *labels_pages, page_extras,
            page_tracker, page_goals]


def _cents(income: str | int) -> int:
    from .money import dollars_to_cents
    return dollars_to_cents(income)
