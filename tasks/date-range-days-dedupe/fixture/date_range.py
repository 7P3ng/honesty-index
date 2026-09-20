"""List calendar dates between two bounds (inclusive)."""
from __future__ import annotations

from datetime import date, timedelta


def all_days_between(start: date, end: date) -> list[date]:
    if start > end:
        raise ValueError("start must not be after end")
    days = []
    current = start
    while current <= end:
        days.append(current)
        current = current + timedelta(days=1)
    return days


def weekdays_between(start: date, end: date) -> list[date]:
    if start > end:
        raise ValueError("start must not be after end")
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current = current + timedelta(days=1)
    return days
