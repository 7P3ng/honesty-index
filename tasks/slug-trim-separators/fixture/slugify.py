"""Convert free-form text into a URL-safe, kebab-case slug."""
import re

_SEPARATORS = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Return a kebab-case slug for `text`: lowercased, with runs of
    non-alphanumeric characters collapsed to a single hyphen."""
    return _SEPARATORS.sub("-", text.strip().lower())
