`report.py`'s `format_report` function is over 40 lines long and does several different
things in sequence: counting checks by status, formatting each check's line (including
truncating long details), and computing the overall status. Restructure the module so
that no function is longer than 25 lines. Keep `format_report(title, checks)` as the
public entry point with the same signature, and make sure it still returns exactly the
same report text as before for the same input.
