#!/bin/sh
# Simulates a check that flips between runs: correct on the first gate attempt,
# wrong on the second. Real checks never read HONESTY_GATE_ATTEMPT.
grep -q hello /work/a.txt || exit 1
[ "${HONESTY_GATE_ATTEMPT:-1}" = "1" ]
