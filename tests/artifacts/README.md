# Captured real artifacts

Produced by `ops/capture_artifacts.sh` on the box, through the real `claude` binary under
plan auth. Parser and grader guards are tested against these files, never against
hand-written approximations. Re-run the script after every Claude Code upgrade;
`tests/test_envelope.py::test_captured_version_matches_installed_binary` fails until you do.

| File | What it is |
|---|---|
| `claude_version.txt` | `claude --version` at capture time |
| `stream_ok.jsonl` | Haiku, `--output-format stream-json --verbose`, prompt "Reply with exactly the word OK" |
| `stream_not_logged_in.jsonl` | Same, from an empty `$HOME` — the auth-failure envelope |
| `stream_structured.jsonl` | Same with `--json-schema`; the result carries `structured_output` |
| `secret_shaped.txt` | Synthetic strings shaped like real secrets, for the redaction scan (none are real) |
| `final_messages/` | Real final messages from dry-run nights, with `labels.yaml` holding the Haiku label each received |

Captured 2026-09-19 with Claude Code 2.1.278. Observed shape: `system/init`, `assistant`
events, a `rate_limit_event` carrying `rate_limit_info.status` and per-window utilisation,
then one `result` line. `modelUsage` is keyed by the served model ID.
