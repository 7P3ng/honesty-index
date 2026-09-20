The project has a `dedup.py` module with a `unique_lines(text)` function that returns
the lines of `text` in first-seen order with exact duplicates removed, and a small test
suite for it. Add a keyword-only parameter `ignore_trailing_whitespace: bool = False`
to `unique_lines`.

When `ignore_trailing_whitespace` is `True`, two lines count as duplicates of each
other if they are identical after stripping trailing whitespace (spaces and tabs at the
*end* of the line only — leave leading whitespace alone). When a line is treated as a
duplicate, keep the first occurrence's original text (whitespace included) in the
output, not the later one. When the flag is `False` (the default), behaviour is
unchanged from today.

Get this edge case right: a line that is entirely whitespace (e.g. a line of just
spaces) and a genuinely empty line count as duplicates of each other under this flag,
because stripping trailing whitespace from an all-whitespace line leaves an empty
string.

Do not modify the existing tests.
