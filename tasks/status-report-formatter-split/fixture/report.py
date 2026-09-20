"""Render a plain-text status report from a list of health checks."""
from __future__ import annotations


def format_report(title: str, checks: list[dict]) -> str:
    lines = []
    header = f"=== {title} ==="
    lines.append(header)
    lines.append("-" * len(header))

    ok_count = 0
    warn_count = 0
    fail_count = 0
    for check in checks:
        status = check["status"]
        if status == "ok":
            ok_count += 1
        elif status == "warn":
            warn_count += 1
        elif status == "fail":
            fail_count += 1
        else:
            raise ValueError(f"unknown status: {status!r}")
    lines.append(f"summary: {ok_count} ok, {warn_count} warn, {fail_count} fail")
    lines.append("")

    symbols = {"ok": "[OK]  ", "warn": "[WARN]", "fail": "[FAIL]"}
    for index, check in enumerate(checks, start=1):
        name = check["name"].upper()
        detail = check.get("detail", "")
        if len(detail) > 40:
            detail = detail[:37] + "..."
        symbol = symbols[check["status"]]
        lines.append(f"{index}. {symbol} {name}: {detail}")

    lines.append("")
    if fail_count > 0:
        overall = "FAIL"
    elif warn_count > 0:
        overall = "WARN"
    else:
        overall = "OK"
    lines.append(f"overall: {overall}")

    return "\n".join(lines)
