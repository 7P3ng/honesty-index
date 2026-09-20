"""Validate configuration sections loaded from a parsed dict (e.g. from JSON or TOML).

validate_config() is the single public entry point other modules call before
starting the service.
"""
from __future__ import annotations


def _validate_section(config: dict, name: str) -> None:
    section = config.get(name)
    if not isinstance(section, dict):
        raise ValueError(f"{name}: missing or not a table")
    host = section.get("host")
    if not isinstance(host, str) or not host.strip():
        raise ValueError(f"{name}: host must be a non-empty string")
    port = section.get("port")
    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise ValueError(f"{name}: port must be an integer in 1..65535")
    timeout = section.get("timeout", 30)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError(f"{name}: timeout must be a positive number")


def validate_config(config: dict) -> None:
    _validate_section(config, "server")
    _validate_section(config, "worker")
