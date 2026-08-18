"""ICE / end-of-life binder builder — 8 pages, one page per thing.

The generator asks at most 12 short fields (ICE_FIELDS below); everything
else on the pages is labeled blank fill-in space. The content is GENERIC:
no state-specific sections, no legal forms — the disclaimer covers that
boundary on every page.
"""

from __future__ import annotations

from datetime import date

from .theme import PageFn, Page, MARGIN, INK, ACCENT, MUTED, LINE

# Exactly 12 short fields — the interactive generator asks no more than these.
ICE_FIELDS: list[tuple[str, str]] = [
    ("name", "Full name"),
    ("phone", "Phone number"),
    ("address", "Home address"),
    ("emergency_name", "Primary emergency contact (name)"),
    ("emergency_phone", "Primary emergency contact (phone)"),
    ("blood_type", "Blood type"),
    ("allergies", "Allergies"),
    ("medications", "Current medications"),
    ("doctor", "Primary doctor"),
    ("doctor_phone", "Doctor's phone number"),
    ("insurance", "Insurance company"),
    ("policy", "Policy number"),
]

PAGE_TITLES = [
    "Cover & Family Information",
    "Emergency Contacts",
    "Medical Information",
    "Insurance & Policies",
    "Finances",
    "Digital Accounts",
    "Final Wishes",
    "Document Checklist",
]

_BLANK = "\u2014"  # em dash placeholder for empty values


def _v(fields: dict, key: str) -> str:
    value = str(fields.get(key, "") or "").strip()
    return value if value else _BLANK


def _blank_lines(ctx: Page, x: float, y: float, n: int, gap: float = 22.0,
                 width: float | None = None):
    """Draw n blank fill-in lines starting at (x, y)."""
    w = width if width is not None else ctx.w - 2 * MARGIN - x + MARGIN
    for i in range(n):
        yy = y + i * gap + 6
        ctx.line(x, yy, x + w, yy, color=LINE, width=0.75)
    return y + n * gap


def _field_block(ctx: Page, x: float, y: float, label: str, value: str,
                 value_size: float = 11.0, lines_under: int = 0):
    """A labeled value (or blank) with optional extra blank lines under it."""
    ctx.text(x, y, label, size=8.5, font="bold", color=MUTED)
    ctx.text(x, y + 14, value if value else _BLANK, size=value_size)
    y2 = y + 34
    if lines_under:
        y2 = _blank_lines(ctx, x, y2, lines_under)
    return y2


def build_ice_pages(fields: dict, paper: str = "letter") -> list[PageFn]:
    w = {"letter": 612.0, "a4": 595.27}[paper]
    m = MARGIN
    cw = w - 2 * m

    # ---------------------------------------------------------------- 1/8
    def page_cover(ctx: Page, n: int, total: int):
        ctx.rect(0, 0, ctx.w, 8, fill=ACCENT)
        ctx.text(m, 40, "PaperLife \u2014 ICE Binder", size=9.0, color=MUTED)
        ctx.text(ctx.w - m, 40, "PRINT, FILL, KEEP WHERE SOMEONE CAN FIND IT",
                 size=9.0, color=MUTED, align="right")
        ctx.text(ctx.w / 2, 128, "In Case of Emergency",
                 size=30.0, font="bold", align="center")
        ctx.text(ctx.w / 2, 160, "Family & household information binder",
                 size=12.5, color=MUTED, align="center")
        ctx.line(m, 186, ctx.w - m, 186, color=ACCENT, width=1.5)

        y = 216
        ctx.text(m, y, "Prepared for", size=8.5, font="bold", color=MUTED)
        ctx.text(m, y + 14, _v(fields, "name"), size=13.0)
        raw_date = fields.get("date_prepared") or date.today()
        if isinstance(raw_date, str):
            try:
                prepared = date.fromisoformat(raw_date)
            except ValueError:
                prepared = date.today()
        else:
            prepared = raw_date
        ctx.text(m + 220, y + 14, f"Date: {prepared:%B %d, %Y}",
                 size=10.0, color=MUTED)
        y2 = _field_block(ctx, m, y + 44, "PHONE", _v(fields, "phone"))
        y2 = _field_block(ctx, m, y2 + 6, "ADDRESS", _v(fields, "address"))

        ty = y2 + 18
        ctx.text(m, ty, "Household members", size=12.0, font="bold")
        ctx.table(m, ty + 22, cw,
                  [["", "", "", ""]] * 5,
                  col_widths=[cw * 0.28, cw * 0.22, cw * 0.25, cw * 0.25],
                  header=["Name", "Relationship", "Phone", "Notes"], row_h=28)
        ctx.text(m, ctx.h - 64, "Tell your family where this binder lives "
                                "\u2014 keep it somewhere easy to reach.",
                 size=9.5, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 2/8
    def page_contacts(ctx: Page, n: int, total: int):
        ctx.head("Emergency Contacts", PAGE_TITLES[1], n, total)
        ctx.textbox(m, 86, cw, 26, "Everyone a loved one might call: partner, parents, "
                                   "siblings, close friends, doctors, work contacts.",
                    size=9.5, color=MUTED)
        rows = [["", "", "", ""]] * 9
        if fields.get("emergency_name"):
            rows[0] = [str(fields["emergency_name"]), "Primary contact",
                       str(fields.get("emergency_phone") or ""), ""]
        ctx.table(m, 112, cw, rows,
                  col_widths=[cw * 0.30, cw * 0.22, cw * 0.24, cw * 0.24],
                  header=["Contact", "Relationship", "Phone", "Notes"], row_h=32)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 3/8
    def page_medical(ctx: Page, n: int, total: int):
        ctx.head("Medical Information", PAGE_TITLES[2], n, total)
        y = 86
        y = _field_block(ctx, m, y, "BLOOD TYPE", _v(fields, "blood_type"))
        y = _field_block(ctx, m, y + 2, "ALLERGIES", _v(fields, "allergies"))
        y = _field_block(ctx, m, y + 2, "CURRENT MEDICATIONS", _v(fields, "medications"),
                         lines_under=3)
        y = _field_block(ctx, m, y + 4, "MEDICAL CONDITIONS", _BLANK, lines_under=3)
        y = _field_block(ctx, m, y + 4, "PRIMARY DOCTOR", _v(fields, "doctor"))
        y = _field_block(ctx, m, y + 2, "DOCTOR'S PHONE", _v(fields, "doctor_phone"))
        y = _field_block(ctx, m, y + 2, "PREFERRED HOSPITAL", _BLANK)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 4/8
    def page_insurance(ctx: Page, n: int, total: int):
        ctx.head("Insurance & Policies", PAGE_TITLES[3], n, total)
        y = 86
        y = _field_block(ctx, m, y, "INSURANCE COMPANY", _v(fields, "insurance"))
        y = _field_block(ctx, m, y + 2, "POLICY NUMBER", _v(fields, "policy"))
        ty = y + 10
        ctx.text(m, ty, "Policies & memberships", size=12.0, font="bold")
        ctx.table(m, ty + 22, cw, [["", "", "", ""]] * 7,
                  col_widths=[cw * 0.24, cw * 0.28, cw * 0.24, cw * 0.24],
                  header=["Policy type", "Company", "Policy number", "Phone"], row_h=30)
        ctx.text(m, ty + 22 + 8 * 30 + 12, "Auto, home, life, dental, roadside "
                                          "\u2014 list anything the family might need to claim.",
                 size=9.5, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 5/8
    def page_finances(ctx: Page, n: int, total: int):
        ctx.head("Finances", PAGE_TITLES[4], n, total)
        ctx.textbox(m, 86, cw, 26, "Enough detail for a family member to find the "
                                   "accounts \u2014 you do not need full account numbers here.",
                    size=9.5, color=MUTED)
        ctx.table(m, 112, cw, [["", "", "", "", ""]] * 8,
                  col_widths=[cw * 0.22, cw * 0.20, cw * 0.24, cw * 0.18, cw * 0.16],
                  header=["Institution", "Account type", "Account details", "Phone", "Notes"],
                  row_h=32)
        ctx.text(m, 112 + 24 + 8 * 32 + 12, "Include: bank, credit union, credit cards, "
                                           "loans, utilities, subscriptions.",
                 size=9.5, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 6/8
    def page_digital(ctx: Page, n: int, total: int):
        ctx.head("Digital Accounts", PAGE_TITLES[5], n, total)
        ctx.table(m, 86, cw, [["", "", "", ""]] * 8,
                  col_widths=[cw * 0.26, cw * 0.30, cw * 0.24, cw * 0.20],
                  header=["Service", "Username / email", "Recovery contact", "Password kept"],
                  row_h=32)
        ctx.textbox(m, 86 + 24 + 8 * 32 + 12, cw, 26,
                    "Do NOT write passwords on these pages if other people see "
                    "this binder. Note where passwords live: password manager, "
                    "safe, trusted family member.",
                    size=9.5, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 7/8
    def page_wishes(ctx: Page, n: int, total: int):
        ctx.head("Final Wishes", PAGE_TITLES[6], n, total)
        ctx.text(m, 86, "Written in your own words \u2014 the people who love you will "
                        "be grateful for the clarity.",
                 size=9.5, color=MUTED)
        y = 116
        for label, lines in [
            ("FUNERAL OR MEMORIAL PREFERENCES", 3),
            ("PEOPLE TO NOTIFY", 3),
            ("ORGANIZATIONS / CAUSES", 2),
            ("PERSONAL MESSAGES", 3),
            ("ANYTHING ELSE", 2),
        ]:
            ctx.text(m, y, label, size=8.5, font="bold", color=MUTED)
            y = _blank_lines(ctx, m, y + 12, lines, gap=24)
            y += 16
        ctx.textbox(m, y + 4, cw, 40,
                    "For legally binding documents \u2014 wills, powers of attorney, "
                    "advance directives \u2014 consult a licensed professional in your "
                    "state. This binder is organizational only.",
                    size=9.5, color=MUTED)
        ctx.foot(n, total)

    # ---------------------------------------------------------------- 8/8
    def page_checklist(ctx: Page, n: int, total: int):
        ctx.head("Document Checklist", PAGE_TITLES[7], n, total)
        docs = ["Birth certificate", "Passport", "Driver's license / ID",
                "Marriage certificate", "Will", "Power of attorney",
                "Insurance policies", "Property deed / lease", "Vehicle title",
                "Tax returns (last 3 years)"]
        rows = [[d, "", ""] for d in docs] + [["", "", ""]] * 4
        ctx.table(m, 86, cw, rows,
                  col_widths=[cw * 0.42, cw * 0.28, cw * 0.30],
                  header=["Document", "Location", "Notes"], row_h=30)
        ctx.foot(n, total)

    return [page_cover, page_contacts, page_medical, page_insurance,
            page_finances, page_digital, page_wishes, page_checklist]
