"""Inline SVG charts for the static site. No scripts, no external assets.

Colours are CSS classes so light/dark is the stylesheet's job. One series per chart,
band = Wilson interval, gaps left as gaps, change markers as dashed verticals.
"""
from __future__ import annotations

from harness.stats import Rate


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg_line_with_band(series: list[tuple[str, Rate]], markers: list[tuple[str, str]], *, width: int = 720,
                       height: int = 260, label: str = "silent-failure rate over time") -> str:
    """series: (night, rate) in night order; rates with shown=False leave a gap. markers: (night, label)."""
    pad_l, pad_r, pad_t, pad_b = 44, 12, 12, 28
    inner_w, inner_h = width - pad_l - pad_r, height - pad_t - pad_b
    nights = [n for n, _ in series]
    if not nights:
        return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="no data" class="chart">'
                f'<text class="axis" x="{width / 2}" y="{height / 2}" text-anchor="middle">no data yet</text></svg>')
    x_of = {n: pad_l + (i * inner_w / max(1, len(nights) - 1)) for i, n in enumerate(nights)}

    def y_of(v: float) -> float:
        return pad_t + inner_h * (1 - v)

    segments: list[list[tuple[str, Rate]]] = [[]]
    for n, r in series:
        if r.shown:
            segments[-1].append((n, r))
        elif segments[-1]:
            segments.append([])
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_esc(label)}" class="chart">']
    for frac in (0, 0.25, 0.5, 0.75, 1):
        y = y_of(frac)
        parts.append(f'<line class="grid" x1="{pad_l}" x2="{width - pad_r}" y1="{y:.1f}" y2="{y:.1f}"/>')
        parts.append(f'<text class="axis" x="{pad_l - 6}" y="{y + 4:.1f}" text-anchor="end">{int(frac * 100)}%</text>')
    for seg in segments:
        if not seg:
            continue
        upper = " ".join(f"{x_of[n]:.1f},{y_of(r.high):.1f}" for n, r in seg)
        lower = " ".join(f"{x_of[n]:.1f},{y_of(r.low):.1f}" for n, r in reversed(seg))
        parts.append(f'<polygon class="band" points="{upper} {lower}"/>')
        line = " ".join(f"{x_of[n]:.1f},{y_of(r.value):.1f}" for n, r in seg)
        parts.append(f'<polyline class="line" fill="none" points="{line}"/>')
        for n, r in seg:
            parts.append(f'<circle class="dot" cx="{x_of[n]:.1f}" cy="{y_of(r.value):.1f}" r="2.5">'
                         f'<title>{_esc(n)}: {r.value * 100:.1f}% (n={r.denominator})</title></circle>')
    for n, text in markers:
        if n in x_of:
            parts.append(f'<line class="marker" x1="{x_of[n]:.1f}" x2="{x_of[n]:.1f}" y1="{pad_t}" y2="{pad_t + inner_h}">'
                         f'<title>{_esc(text)}</title></line>')
    step = max(1, len(nights) // 6)
    for i, n in enumerate(nights):
        if i % step == 0 or i == len(nights) - 1:
            parts.append(f'<text class="axis" x="{x_of[n]:.1f}" y="{height - 8}" text-anchor="middle">{_esc(n[5:])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_badge(label: str, value: str, *, tone: str) -> str:
    """Shields-style flat badge. tone: 'ok' | 'warn' | 'bad' | 'off'."""
    colours = {"ok": "#2e7d32", "warn": "#b26a00", "bad": "#c62828", "off": "#6b6b6b"}
    lw, vw = 7 * len(label) + 12, 7 * len(value) + 12
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{lw + vw}" height="20" role="img" '
        f'aria-label="{_esc(label)}: {_esc(value)}">'
        f'<rect width="{lw}" height="20" fill="#555"/><rect x="{lw}" width="{vw}" height="20" fill="{colours[tone]}"/>'
        f'<g fill="#fff" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11" text-anchor="middle">'
        f'<text x="{lw / 2}" y="14">{_esc(label)}</text><text x="{lw + vw / 2}" y="14">{_esc(value)}</text></g></svg>'
    )
