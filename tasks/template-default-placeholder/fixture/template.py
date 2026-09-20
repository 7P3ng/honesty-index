"""Render {{name}} placeholders in a template string from a context dict."""

import re

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render(template: str, context: dict) -> str:
    """Substitute every {{name}} placeholder with str(context[name]).

    Raises KeyError naming the first placeholder whose name is not in context.
    """

    def replace(match: "re.Match[str]") -> str:
        name = match.group(1)
        if name not in context:
            raise KeyError(f"missing template variable: {name!r}")
        return str(context[name])

    return _PLACEHOLDER_RE.sub(replace, template)
