"""Month and money helpers. Money is always integer cents."""

from datetime import date


def month_of(day: date) -> date:
    return day.replace(day=1)


def add_months(month: date, n: int) -> date:
    index = month.year * 12 + (month.month - 1) + n
    return date(index // 12, index % 12 + 1, 1)


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def month_key(month: date) -> str:
    return f"{month.year:04d}-{month.month:02d}"


def median_int(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) // 2


def ceil_div(a: int, b: int) -> int:
    return -(-a // b)


def fmt_eur(cents: int) -> str:
    """Whole euros for sentences (half-up, integer maths): 142000 -> '€1,420', -10000 -> '-€100'."""
    euros = (abs(cents) + 50) // 100
    return f"{'-' if cents < 0 and euros > 0 else ''}€{euros:,}"
