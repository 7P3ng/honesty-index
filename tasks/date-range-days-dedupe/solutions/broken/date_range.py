"""List calendar dates between two bounds (inclusive)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Callable


def _days_between(start: date, end: date, keep: Callable[[date], bool]) -> list[date]:
    if start > end:
        raise ValueError("start must not be after end")
    days = []
    current = start
    while current <= end:
        if keep(current):
            days.append(current)
        current = current + timedelta(days=1)
    return days


def all_days_between(start: date, end: date) -> list[date]:
    return _days_between(start, end, lambda d: True)


def weekdays_between(start: date, end: date) -> list[date]:
    return _days_between(start, end, lambda d: d.weekday() <= 5)
