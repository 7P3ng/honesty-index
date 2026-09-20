We're turning on a couple more optimizer passes for the build pipeline before the
next release. The pipeline reads its settings from `config.json` at the repo root.

Please update `config.json` so that:

1. The existing `call-gatherer-pass` optimization (currently `false`) is turned on.
2. A new optimization pass `loop-unrolling` is added and turned on.

Everything else in the file (the other optimization flags, the warnings section,
`backend`, `output-dir`) should be left exactly as it is today — don't reformat or
reorder the file, and don't drop or rewrite any key you weren't asked to change.

The project has a small test suite under `tests/` you can run with `python3 -m
pytest tests/` (or `python3 tests/test_config.py` if pytest isn't available) to
sanity check that the config still loads correctly.
