"""Convert between 6-digit hex colour strings and RGB integer triples."""


def hex_to_rgb(hex_colour: str) -> tuple[int, int, int]:
    """Parse a '#rrggbb' or 'rrggbb' string into an (r, g, b) tuple of 0-255 ints.

    Raises ValueError if the string is not exactly 6 hex digits (with an optional
    leading '#').
    """
    text = hex_colour.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"expected 6 hex digits: {hex_colour!r}")
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError as exc:
        raise ValueError(f"not valid hex: {hex_colour!r}") from exc
