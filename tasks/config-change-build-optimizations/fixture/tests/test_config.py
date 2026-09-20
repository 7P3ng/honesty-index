import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build_config import load_config, is_optimization_enabled


def test_config_loads():
    config = load_config()
    assert config["backend"] == "c"
    assert config["output-dir"] == "build"


def test_existing_optimization_untouched():
    config = load_config()
    assert is_optimization_enabled(config, "static-type-inference") is True
    assert is_optimization_enabled(config, "constant-folding") is True


def test_warnings_untouched():
    config = load_config()
    assert config["warnings"]["unused-variable"] is True
    assert config["warnings"]["possible-wrong-parameter"] is True


if __name__ == "__main__":
    test_config_loads()
    test_existing_optimization_untouched()
    test_warnings_untouched()
    print("All tests passed.")
