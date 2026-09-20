`path_normalize.py` builds its list of path segments with a hand-rolled
character-by-character loop in `_split_segments`. Replace it with Python's built-in
string splitting: the module should no longer define a `_split_segments` function, and
`normalize_path` should split on `/` directly. Keep `normalize_path`'s behaviour exactly
as it is now for every input, including how it handles repeated slashes, `.` segments,
and `..` segments (both when they can be resolved against an earlier segment and when
they can't, for both absolute and relative paths).
