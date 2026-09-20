# Agent Honesty Index

When a coding agent says "done", how often is that true?

A nightly public instrument: a fixed bank of realistic tasks, each with a hidden check the
agent never sees, run through Claude Code under several models. For every run we record
what the agent **claimed** and what the check **found**, and publish the silent-failure
rate — P(check fails | agent claimed success) — per model, over time, with confidence
intervals and the raw transcripts.

Design: `docs/superpowers/specs/2026-09-19-honesty-index-design.md`. Site: https://honesty.thomaspeng.ca.
Data: https://github.com/7P3ng/honesty-index-data.

What runs, all as cron on one box with no human in the loop: the nightly run at 02:00 UTC
(`harness/run_night.py`), the site build at 07:30, weekly task intake on Sunday, a weekly
factual post on Monday, and monthly retirement and digest on the 1st. See `ops/README.md`.

Run the tests: `uv sync && uv run pytest`.
