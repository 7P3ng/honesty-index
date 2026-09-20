"""Render a plain-text status report from a list of health checks."""
from __future__ import annotations

_SYMBOLS = {"ok": "[OK]  ", "warn": "[WARN]", "fail": "[FAIL]"}


def _count_statuses(checks: list[dict]) -> dict[str, int]:
    counts = {"ok": 0, "warn": 0, "fail": 0}
    for check in checks:
        status = check["status"]
        if status not in counts:
            raise ValueError(f"unknown status: {status!r}")
        counts[status] += 1
    return counts


def _format_check_line(index: int, check: dict) -> str:
    name = check["name"].upper()
    detail = check.get("detail", "")
    if len(detail) > 40:
        detail = detail[:37] + "..."
    symbol = _SYMBOLS[check["status"]]
    return f"{index}. {symbol} {name}: {detail}"


def _overall_status(counts: dict[str, int]) -> str:
    if counts["fail"] > 0:
        return "FAIL"
    if counts["warn"] > 0:
        return "WARN"
    return "OK"


def format_report(title: str, checks: list[dict]) -> str:
    header = f"=== {title} ==="
    counts = _count_statuses(checks)
    lines = [
        header,
        "-" * len(header),
        f"summary: {counts['ok']} ok, {counts['warn']} warn, {counts['fail']} fail",
        "",
    ]
    lines.extend(_format_check_line(i, c) for i, c in enumerate(checks, start=1))
    lines.append("")
    lines.append(f"overall: {_overall_status(counts)}")
    return "\n".join(lines)
