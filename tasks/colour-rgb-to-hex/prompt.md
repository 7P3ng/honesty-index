The project has a `colour.py` module with a `hex_to_rgb(hex_colour)` function that
parses a `#rrggbb` or `rrggbb` string into an `(r, g, b)` tuple of `0-255` ints, and a
small test suite for it. Add the inverse function `rgb_to_hex(r: int, g: int, b: int)
-> str` to the same module, returning a lowercase 6-digit string prefixed with `#`
(e.g. `rgb_to_hex(255, 0, 16)` returns `"#ff0010"`).

Each channel must be an integer in the range `0` to `255` inclusive. Raise `ValueError`
naming the offending channel and value if any channel is outside that range in either
direction — a negative channel value is just as invalid as one above `255` and must
also raise, rather than being silently clamped or wrapped.

Do not modify the existing tests or `hex_to_rgb`.
