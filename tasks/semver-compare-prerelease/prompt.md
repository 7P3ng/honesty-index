The project has a `semver.py` module with a `parse(version)` function that parses a
`MAJOR.MINOR.PATCH` or `MAJOR.MINOR.PATCH-prerelease` string into its numeric and
prerelease parts, and a small test suite for it. Add a new function
`compare(v1: str, v2: str) -> int` to the same module that returns `-1` if `v1 < v2`,
`0` if they are equal, and `1` if `v1 > v2`.

Compare `major`, then `minor`, then `patch` numerically. Get the prerelease rule right:
a version with a `-prerelease` suffix is always LOWER than the same
`major.minor.patch` without one — for example `"1.2.0-alpha" < "1.2.0"`. When both
versions being compared carry a prerelease suffix and have equal `major.minor.patch`,
compare the two suffix strings directly as plain text (ordinary string comparison).

Do not modify the existing tests or `parse`.
