# Agent Honesty Index

When a coding agent says "done", how often is that true?

A nightly public instrument: a fixed bank of realistic tasks, each with a hidden check the
agent never sees, run through Claude Code under several models. For every run we record
what the agent **claimed** and what the check **found**, and publish the silent-failure
rate — P(check fails | agent claimed success) — per model, over time, with confidence
intervals and the raw transcripts.

Status: **design approved, not yet built.** Start with
`docs/superpowers/specs/2026-09-19-honesty-index-design.md`.

Run the tests: `uv sync && uv run pytest`.
