"""Exact money math for PaperLife — cents-integer arithmetic only, no floats.

Every dollar figure in the product is handled as an integer number of cents.
The allocator floors each envelope share to the cent and reports the
difference as a leftover/buffer line, so envelope amounts + leftover always
equal the income exactly.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN

CENT = Decimal("0.01")


def parse_dollars(value: str | int | float | Decimal) -> Decimal:
    """Parse a dollar amount to an exact Decimal with at most 2 decimal places.

    Accepts '2000', '500.17', '$2,000.00', ' 12.5 '. Rejects anything finer
    than a cent (cannot be exact) and anything negative (invalid input, not
    a rounding problem).
    """
    if isinstance(value, float):
        # Never trust float representation for money; the caller must pass
        # strings/Decimals. Accepting the float only when it is a clean value.
        value = repr(value)
    if isinstance(value, Decimal):
        d = value
    else:
        try:
            d = Decimal(str(value).strip().replace("$", "").replace(",", "").replace(" ", ""))
        except InvalidOperation:
            raise ValueError(f"not a dollar amount: {value!r}") from None
    if d < 0:
        raise ValueError(f"amount must not be negative, got {value!r}")
    if d != d.quantize(CENT):
        raise ValueError(f"amount must have at most 2 decimal places, got {value!r}")
    return d


def dollars_to_cents(value: str | int | Decimal) -> int:
    d = parse_dollars(value)
    return int((d * 100).to_integral_value())


def parse_weight(value: str | Decimal) -> Decimal:
    """Parse a category weight in percent (0 < w <= 100, at most 2 dp)."""
    d = Decimal(str(value).strip().replace("%", "").replace(" ", ""))
    if d <= 0:
        raise ValueError(f"weight must be greater than 0%, got {value!r}")
    if d > 100:
        raise ValueError(f"weight must not exceed 100%, got {value!r}")
    if d != d.quantize(CENT):
        raise ValueError(f"weight must have at most 2 decimal places, got {value!r}")
    return d


def validate_weights(weights: list[Decimal]) -> None:
    """Hard gate: category weights MUST sum to exactly 100%."""
    total = sum(weights, Decimal("0"))
    if total != Decimal("100"):
        raise ValueError(
            f"category weights must sum to exactly 100%, got {total}% "
            f"(missing {100 - total}% or {total - 100}% over)"
        )


def allocate(income_cents: int, weights: list[Decimal]) -> tuple[list[int], int]:
    """Allocate income to envelopes, flooring to the cent.

    Returns (envelope_cents, leftover_cents) with
        sum(envelope_cents) + leftover_cents == income_cents  (exact, in cents)
    and leftover_cents >= 0.
    """
    validate_weights(weights)
    if income_cents < 0:
        raise ValueError("income must not be negative")
    envelopes = [
        int((Decimal(income_cents) * w / Decimal("100")).to_integral_value(rounding=ROUND_DOWN))
        for w in weights
    ]
    leftover = income_cents - sum(envelopes)
    return envelopes, leftover


def fmt_cents(cents: int) -> str:
    """Format cents as a grouped dollar string: 123456 -> '1,234.56'."""
    return f"{Decimal(cents) / 100:,.2f}"


def fmt_usd(cents: int) -> str:
    """Format cents as grouped USD with sign before the symbol: -123456 -> '-$1,234.56'."""
    sign = "-" if cents < 0 else ""
    return f"{sign}${Decimal(abs(cents)) / 100:,.2f}"


def net_worth(assets_cents: int, liabilities_cents: int) -> int:
    """Net worth in cents; may be negative (rendered honestly)."""
    return assets_cents - liabilities_cents
