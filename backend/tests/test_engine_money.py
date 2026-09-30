from datetime import date

from app.engine.money import add_months, ceil_div, fmt_eur, median_int, month_key, month_of, months_between


def test_month_of():
    assert month_of(date(2026, 9, 30)) == date(2026, 9, 1)


def test_add_months_crosses_years_both_ways():
    assert add_months(date(2026, 11, 1), 3) == date(2027, 2, 1)
    assert add_months(date(2026, 1, 1), -1) == date(2025, 12, 1)
    assert add_months(date(2026, 9, 1), -12) == date(2025, 9, 1)


def test_months_between():
    assert months_between(date(2026, 9, 1), date(2027, 12, 1)) == 15


def test_month_key():
    assert month_key(date(2026, 8, 1)) == "2026-08"


def test_median_int():
    assert median_int([30000, 40000, 35000]) == 35000
    assert median_int([30000, 34000, 35000, 35000, 38000, 40000]) == 35000
    assert median_int([84201, 98129]) == 91165
    assert median_int([]) == 0


def test_ceil_div():
    assert ceil_div(1_200_000, 45_000) == 27
    assert ceil_div(90_000, 45_000) == 2


def test_fmt_eur():
    assert fmt_eur(60_000) == "€600"
    assert fmt_eur(142_000) == "€1,420"
    assert fmt_eur(123_456) == "€1,235"
    assert fmt_eur(-10_000) == "-€100"


def test_fmt_eur_rounds_half_up_and_never_prints_negative_zero():
    assert fmt_eur(12_250) == "€123"
    assert fmt_eur(-40) == "€0"
    assert fmt_eur(-10_000) == "-€100"
