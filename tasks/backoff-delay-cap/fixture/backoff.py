"""Exponential backoff delay calculator for retrying failed operations."""


def backoff_delay(attempt: int, base: float = 1.0, factor: float = 2.0, max_delay: float = 30.0) -> float:
    """Return the delay in seconds before retry number `attempt` (1-indexed).

    Delay grows exponentially from `base` by `factor` each attempt, capped at
    `max_delay`.
    """
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    return base * (factor ** (attempt - 1))


def total_backoff_time(attempts: int, base: float = 1.0, factor: float = 2.0, max_delay: float = 30.0) -> float:
    """Return the sum of backoff_delay(1..attempts) — the total time spent
    waiting across a full retry sequence."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    total = 0.0
    for attempt in range(1, attempts + 1):
        total += base * (factor ** (attempt - 1))
    return total
