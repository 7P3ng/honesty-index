"""Loader for the compiler's config.json used by the build pipeline."""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config(path=CONFIG_PATH):
    with open(path) as f:
        return json.load(f)


def is_optimization_enabled(config, name):
    return bool(config.get("optimizations", {}).get(name, False))
