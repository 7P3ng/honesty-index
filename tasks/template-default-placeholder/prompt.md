The project has a `template.py` module with a `render(template, context)` function
that substitutes `{{name}}` placeholders from a context dict, raising `KeyError` when a
name is missing, and a small test suite for it. Extend the placeholder syntax to
support an inline default: `{{name|default}}` should render the literal text `default`
whenever `name` is not usable, instead of raising.

A placeholder without a `|` must keep behaving exactly as it does today, including
raising `KeyError` when the name is missing. The default text may be empty, so
`{{name|}}` renders as an empty string when `name` is not usable.

Get this edge case right: treat a name that *is* present in the context but whose value
is `None` the same as a missing name — it should fall back to the default (or raise
`KeyError` if there is no `|default`), not render the literal text `"None"`.

Do not modify the existing tests.
