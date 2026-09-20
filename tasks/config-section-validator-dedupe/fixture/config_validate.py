"""Validate configuration sections loaded from a parsed dict (e.g. from JSON or TOML).

validate_config() is the single public entry point other modules call before
starting the service.
"""
from __future__ import annotations


def validate_server(config: dict) -> None:
    section = config.get("server")
    if not isinstance(section, dict):
        raise ValueError("server: missing or not a table")
    host = section.get("host")
    if not isinstance(host, str) or not host.strip():
        raise ValueError("server: host must be a non-empty string")
    port = section.get("port")
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise ValueError("server: port must be an integer in 1..65535")
    timeout = section.get("timeout", 30)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError("server: timeout must be a positive number")


def validate_worker(config: dict) -> None:
    section = config.get("worker")
    if not isinstance(section, dict):
        raise ValueError("worker: missing or not a table")
    host = section.get("host")
    if not isinstance(host, str) or not host.strip():
        raise ValueError("worker: host must be a non-empty string")
    port = section.get("port")
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise ValueError("worker: port must be an integer in 1..65535")
    timeout = section.get("timeout", 30)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError("worker: timeout must be a positive number")


def validate_config(config: dict) -> None:
    validate_server(config)
    validate_worker(config)
