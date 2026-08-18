"""Golden money-math tests — the allocator and the net-worth calculator.

The allocator contract: per-envelope amounts + leftover == income EXACTLY to
the cent, for any valid input; weights != 100% is a hard error.
"""

import pytest
from decimal import Decimal

from paperlife.money import (
    allocate, dollars_to_cents, fmt_cents, fmt_usd, net_worth,
    parse_dollars, parse_weight, validate_weights,
)

# 13 odd-weight categories that sum to exactly 100.00%
THIRTEEN_ODD = [
    "1.7", "2.3", "3.9", "4.1", "5.5", "6.7", "7.3", "8.2",
    "9.1", "10.4", "11.6", "13.9", "15.3",
]

GOLDEN_CASES = [
    # (income, weights) -> expected envelope list (cents), expected leftover
    ("100", ["50", "30", "20"], [5000, 3000, 2000], 0),
    ("500.17", ["27.5", "12.5", "7.5", "10", "15", "10", "7.5", "10"],
     [13754, 6252, 3751, 5001, 7502, 5001, 3751, 5001], 4),
    ("2000.00", ["33.33", "33.33", "33.34"], [66660, 66660, 66680], 0),
    ("2000.00", ["30", "30", "40"], [60000, 60000, 80000], 0),
    ("100", ["100"], [10000], 0),
    ("0.01", ["100"], [1], 0),
    ("500.17", THIRTEEN_ODD, None, None),  # shape verified below, math generic
]


def test_golden_allocations_exact_to_the_cent():
    for income, weights, expected_env, expected_left in GOLDEN_CASES:
        cents = dollars_to_cents(income)
        wts = [Decimal(w) for w in weights]
        envelopes, leftover = allocate(cents, wts)
        # The core golden invariant: sum + leftover == income, exactly.
        assert sum(envelopes) + leftover == cents, (income, weights)
        assert leftover >= 0
        assert all(e >= 0 for e in envelopes)
        # Every envelope amount is a whole number of cents (displayed with 2 dp).
        for e in envelopes:
            assert Decimal(e) / 100 == Decimal(fmt_cents(e))
        if expected_env is not None:
            assert envelopes == expected_env, income
            assert leftover == expected_left, income


def test_golden_thirteen_odd_weights_all_positive_floor():
    cents = dollars_to_cents("500.17")
    wts = [Decimal(w) for w in THIRTEEN_ODD]
    envelopes, leftover = allocate(cents, wts)
    assert len(envelopes) == 13
    assert sum(envelopes) + leftover == 50017
    assert 0 <= leftover < 13  # leftover is strictly less than one cent per category
    # floor property: each envelope <= exact share, share - envelope < 1 cent
    for e, w in zip(envelopes, wts):
        exact = Decimal(cents) * w / Decimal(100)
        assert e <= exact < e + 1


@pytest.mark.parametrize("weights", [
    ["50", "49"],          # 99%
    ["50", "50.01"],       # 100.01%
    ["10", "10", "10"],    # 30%
    ["100", "0.01"],       # 100.01%
])
def test_weights_not_exactly_100_are_hard_errors(weights):
    with pytest.raises(ValueError, match="must sum to exactly 100%"):
        allocate(10000, [Decimal(w) for w in weights])


def test_weights_finer_than_2dp_rejected_by_parse():
    # allocate() accepts any Decimals summing to exactly 100; the CLI gate is
    # parse_weight, which caps weights at 2 decimal places.
    with pytest.raises(ValueError):
        parse_weight("33.333")


@pytest.mark.parametrize("bad", ["0", "-5", "101"])
def test_weights_out_of_range_are_errors(bad):
    with pytest.raises(ValueError):
        parse_weight(bad)


@pytest.mark.parametrize("bad", ["", "abc", "1.999", "-1", "$"])
def test_income_parse_rejects_garbage(bad):
    with pytest.raises(ValueError):
        parse_dollars(bad)


def test_income_parse_accepts_currencies_and_commas():
    assert parse_dollars("$2,000.00") == Decimal("2000.00")
    assert parse_dollars(" 500.17 ") == Decimal("500.17")
    assert parse_dollars("100") == Decimal("100")
    assert parse_dollars("1,000") == Decimal("1000")


def test_negative_income_rejected():
    with pytest.raises(ValueError, match="must not be negative"):
        allocate(-1, [Decimal("100")])


def test_validate_weights_rejects_non_100():
    with pytest.raises(ValueError):
        validate_weights([Decimal("99.99")])


def test_net_worth_positive():
    assert net_worth(dollars_to_cents("1234567.89"), dollars_to_cents("234567.89")) == 100000000
    assert fmt_usd(net_worth(dollars_to_cents("1234567.89"), dollars_to_cents("234567.89"))) == "$1,000,000.00"


def test_net_worth_negative_rendered_honestly():
    worth = net_worth(dollars_to_cents("3500.00"), dollars_to_cents("6000.00"))
    assert worth == -250000
    assert fmt_usd(worth) == "-$2,500.00"
    assert fmt_usd(worth).startswith("-")  # never hidden


def test_net_worth_zero():
    assert net_worth(dollars_to_cents("12500.00"), dollars_to_cents("12500.00")) == 0
    assert fmt_usd(0) == "$0.00"


def test_fmt_uses_thousands_separators():
    assert fmt_usd(dollars_to_cents("999999.99")) == "$999,999.99"
    assert fmt_cents(123456789) == "1,234,567.89"
