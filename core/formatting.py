"""Indian number and currency formatting helpers."""
from __future__ import annotations


def indian_grouping(value: float) -> str:
    """Format an integer with Indian digit grouping, e.g. 12345678 -> '1,23,45,678'."""
    number = int(round(value))
    digits = str(abs(number))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return f"-{digits}" if number < 0 else digits


def format_inr(value: float, compact: bool = True) -> str:
    """Format rupees as ₹ Cr / ₹ L when compact, else with full Indian grouping."""
    if not compact:
        return f"₹{indian_grouping(value)}"
    magnitude = abs(value)
    sign = "-" if value < 0 else ""
    if magnitude >= 1e7:
        return f"{sign}₹{magnitude / 1e7:,.2f} Cr"
    if magnitude >= 1e5:
        return f"{sign}₹{magnitude / 1e5:,.2f} L"
    return f"{sign}₹{indian_grouping(magnitude)}"


def format_quantity(value: float, unit: str) -> str:
    """Human-friendly quantity: steel above a tonne is shown in MT."""
    if unit == "kg" and value >= 1000:
        return f"{value / 1000:,.2f} MT"
    return f"{indian_grouping(value)} {unit}"
