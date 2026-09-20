"""Static site generator (spec §7). Reads data/runs.sqlite, writes build/. Never calls
Claude. Everything visible is derived from RunRow lists via harness.stats; this module
only lays it out.

CLI: `python -m website.generate_site [--db PATH] [--out DIR]`.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import asdict, fields
from datetime import UTC, datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from harness import db
from harness.config import SiteConfig, load_site
from harness.models import RunRow
from harness.stats import Outcome, Rate, group_by, nightly_series, outcome, summarize
from harness.tasks import load_task
from website.charts import svg_badge, svg_line_with_band

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = Path(__file__).with_name("templates")
STATIC = Path(__file__).with_name("static")
CSV_FIELDS = [f.name for f in fields(RunRow) if f.name != "final_message"]


def pct(r: Rate | None) -> str:
    """Rate as text; hidden rates say so with their denominator."""
    if r is None:
        return "—"
    if not r.shown:
        return f"n<30 ({r.denominator})"
    return f"{r.value * 100:.1f}% [{r.low * 100:.0f}–{r.high * 100:.0f}] n={r.denominator}"


def window(rows: list[RunRow], last_night: str, nights: int) -> list[RunRow]:
    first = (datetime.fromisoformat(last_night) - timedelta(days=nights - 1)).date().isoformat()
    return [r for r in rows if first <= r.night <= last_night]


def site_status(conn, cfg: SiteConfig, now: datetime) -> dict:
    """Online means a complete or partial night finished within offline_after_hours of `now`.
    A night labelled D ends around 05:00 UTC on D, so the age is measured from D 05:00."""
    all_nights = db.nights(conn)
    usable = [n for n in all_nights if n["status"] in ("complete", "partial")]
    last = usable[-1]["night"] if usable else None
    online = False
    if last is not None:
        ended = datetime.fromisoformat(last).replace(tzinfo=UTC) + timedelta(hours=5)
        online = now - ended <= timedelta(hours=cfg.offline_after_hours)
    return {"last_complete_night": last, "online": online,
            "generated_at": now.isoformat(timespec="seconds"), "nights": list(reversed(all_nights))}


def served_changes_by_model(changes: list[tuple[str, str, str]]) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for requested, night, served in changes:
        out.setdefault(requested, []).append((night, served))
    return out


def bank_change_markers(tasks_dir: Path) -> list[tuple[str, str]]:
    """One marker per distinct admission date after the first (the launch set is not a change)."""
    dates = sorted({str(load_task(p).admitted_at) for p in tasks_dir.iterdir() if p.is_dir()})
    return [(d, "task bank changed") for d in dates[1:]]


def badge_for(headline: Rate, online: bool, min_n: int) -> str:
    if not online:
        return svg_badge("honesty index", "offline", tone="off")
    if not headline.shown:
        return svg_badge("silent failure", f"n<{min_n}", tone="off")
    v = headline.value * 100
    return svg_badge("silent failure", f"{v:.0f}% (n={headline.denominator})",
                     tone="ok" if v < 10 else "warn" if v < 30 else "bad")


def generate(db_path: Path, cfg: SiteConfig, out: Path, *, now: datetime, tasks_dir: Path = REPO_ROOT / "tasks") -> None:
    """Side effects: deletes and rewrites `out`."""
    conn = db.connect(db_path)
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    env.filters["pct"] = pct
    status = site_status(conn, cfg, now)
    rows = db.all_runs(conn)
    last_night = status["last_complete_night"] or now.date().isoformat()
    served = served_changes_by_model(db.model_served_changes(conn))
    bank_markers = bank_change_markers(tasks_dir)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy(STATIC / "style.css", out / "style.css")
    common = {"site": cfg, "status": status, "generated_at": status["generated_at"]}

    def render(template: str, dest: Path, **ctx: object) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(env.get_template(template).render(**common, **ctx))

    headline_window = 7 if 7 in cfg.windows_nights else cfg.windows_nights[-1]
    models_ctx: list[dict] = []
    for model_id, mrows in group_by(rows, lambda r: r.model_requested).items():
        windows = [summarize(window(mrows, last_night, w), cfg.min_n) for w in cfg.windows_nights]
        thirty = window(mrows, last_night, 30)
        markers = [(n, f"served model changed to {s}") for n, s in served.get(model_id, [])[1:]] + bank_markers
        ctx = {
            "id": model_id,
            "windows": [s.silent_failure for s in windows],
            "ungradable": windows[cfg.windows_nights.index(headline_window)].ungradable,
            "summaries": list(zip([f"{w} night{'s' if w > 1 else ''}" for w in cfg.windows_nights], windows)),
            "by_category": [(c, summarize(g, cfg.min_n)) for c, g in group_by(thirty, lambda r: r.category).items()],
            "by_task": [(t, summarize(g, cfg.min_n)) for t, g in group_by(thirty, lambda r: r.task).items()],
            "served_changes": served.get(model_id, []),
            "chart": svg_line_with_band(nightly_series(mrows, cfg.min_n), markers, label=f"{model_id} silent-failure rate"),
        }
        models_ctx.append(ctx)
        render("model.html", out / "models" / model_id / "index.html", title=model_id, model=ctx)
        headline = windows[cfg.windows_nights.index(headline_window)].silent_failure
        (out / "badge").mkdir(exist_ok=True)
        (out / "badge" / f"{model_id}.svg").write_text(badge_for(headline, status["online"], cfg.min_n))

    render("index.html", out / "index.html", title="Home", models=models_ctx,
           headline_chart=svg_line_with_band(nightly_series(rows, cfg.min_n), bank_markers, label="all models, silent-failure rate"))

    for task_slug, trows in group_by(rows, lambda r: r.task).items():
        task = load_task(tasks_dir / task_slug)
        thirty = window(trows, last_night, 30)
        example = next((r for r in reversed(trows) if outcome(r) is Outcome.SILENT_FAILURE), None)
        render("task.html", out / "tasks" / task_slug / "index.html", title=task_slug, task={
            "slug": task_slug, "category": task.category, "prompt": task.prompt,
            "admitted_at": task.admitted_at, "retired_at": task.retired_at, "example": example,
            "by_model": [(m, summarize(g, cfg.min_n)) for m, g in group_by(thirty, lambda r: r.model_requested).items()],
        })

    render("methodology.html", out / "methodology" / "index.html", title="Methodology")
    render("data.html", out / "data" / "index.html", title="Data")
    render("status.html", out / "status" / "index.html", title="Status")
    (out / "status.json").write_text(json.dumps({k: v for k, v in status.items() if k != "nights"}, indent=1))
    (out / "data" / "summary.json").write_text(json.dumps(
        {m["id"]: {"windows": dict(zip(map(str, cfg.windows_nights), [asdict(r) for r in m["windows"]])),
                   "ungradable": asdict(m["ungradable"])} for m in models_ctx}, indent=1))
    with (out / "data" / "runs.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_FIELDS)
        for r in rows:
            writer.writerow([getattr(r, f) for f in CSV_FIELDS])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the static site from runs.sqlite")
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "data" / "runs.sqlite")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "build")
    args = parser.parse_args(argv)
    generate(args.db, load_site(REPO_ROOT / "config" / "site.yaml"), args.out, now=datetime.now(UTC))
    print(f"site written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
