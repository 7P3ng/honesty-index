# honesty-index — project instructions

Nightly public instrument measuring how often coding agents claim success when a hidden
check says they failed. Design: `docs/superpowers/specs/2026-09-19-honesty-index-design.md`
— read it before doing anything; it holds the approved architecture and the constraints.

## Rules that override defaults here

- **Zero human in the loop after launch.** Anything that needs Thomas to decide daily or
  weekly is a design bug. Agents pre-decide; he reads a monthly digest.
- **Never publish a number that could be a false accusation.** Every task passes the
  prove-fail gate (§3.3 of the spec) before it runs; ungradable claims are excluded and
  counted; no number is shown with n < 30; "offline" is a first-class state.
- **The website never calls Claude.** It is generated from files. Plan auth is used only
  by the nightly harness, only through the real `claude` binary, only as `tpeng`.
- **Plan auth only, $0 marginal cost.** No API keys for Claude. Other providers are a
  Thomas decision (spec §11), not something to add.
- **Sandbox every agent run** (bubblewrap; spec §2.1). Never run a task on the bare host.
- **eBay employment constraints apply** (memory `project_ebay_employment_constraints`):
  no finance, e-commerce, or marketplace content anywhere in tasks or site.
- **Coding style:** the global senior-engineer defaults (file headers, docstrings, full
  type hints, fail loudly, no swallowed errors, I/O separated from logic). Python 3.12.
- **Tests must be proven to fail first** on a real artifact before they count; parser
  guards for the `claude --output-format json` envelope are tested against a captured
  real envelope, re-captured on every Claude Code upgrade.
- **Crons:** `</dev/null` on every `claude -p`; dead-man alert via
  `sudo -n notify-general` on zero output; log to an existing directory.

## Layout (target — see spec §2)

`config/` rotation + budget · `harness/` nightly run, sandbox, claim grader, stats ·
`tasks/` task bank · `gate/` prove-fail gate · `site/` static generator → `build/` ·
`data/` runs.sqlite + nightly JSONL · `ops/` cron, digest, Caddy block · `tests/`.

## Deploy

Static `build/` served by Caddy at `honesty.thomaspeng.ca` (wildcard TLS already exists)
via a `personal` tenant block — see `~/roux/docs/vps/CONVENTIONS.md`.
