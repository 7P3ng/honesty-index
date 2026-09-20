"""Render {{name}} and {{name|default}} placeholders in a template from a context dict."""

import re

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)(?:\|([^{}]*))?\s*\}\}")


def render(template: str, context: dict) -> str:
    """Substitute {{name}} with str(context[name]), or {{name|default}} with `default`
    whenever `name` is missing from context.

    Raises KeyError naming the first placeholder whose name is unusable and has no
    inline default.
    """

    def replace(match: "re.Match[str]") -> str:
        name, default = match.group(1), match.group(2)
        if name not in context:
            if default is not None:
                return default
            raise KeyError(f"missing template variable: {name!r}")
        return str(context[name])

    return _PLACEHOLDER_RE.sub(replace, template)
