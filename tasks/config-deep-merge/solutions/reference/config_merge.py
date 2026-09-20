"""Merge a user-supplied config dict onto a set of defaults."""


def merge_config(defaults: dict, overrides: dict) -> dict:
    """Return a new dict combining `defaults` with `overrides` applied on top.

    Nested dict values are merged recursively rather than replaced wholesale,
    so an override can change one nested key without dropping its siblings.
    """
    result = dict(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result
