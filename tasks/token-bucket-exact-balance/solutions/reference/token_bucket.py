"""Token-bucket rate limiter with an injectable clock for deterministic tests."""


class TokenBucket:
    """Allows up to `capacity` tokens, refilling at `rate` tokens per second.

    `clock` is a zero-argument callable returning the current time in seconds;
    tests pass a fake one so behavior does not depend on wall-clock time.
    """

    def __init__(self, capacity: float, rate: float, clock) -> None:
        if capacity <= 0 or rate <= 0:
            raise ValueError("capacity and rate must be > 0")
        self._capacity = capacity
        self._rate = rate
        self._clock = clock
        self._tokens = capacity
        self._last_check = clock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._last_check
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_check = now

    def allow(self, cost: float = 1) -> bool:
        """Return True and deduct `cost` tokens if enough are available."""
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False

    def allow_many(self, costs: list) -> list:
        """Apply `allow` to each cost in `costs`, in order, returning the results."""
        results = []
        for cost in costs:
            self._refill()
            if self._tokens >= cost:
                self._tokens -= cost
                results.append(True)
            else:
                results.append(False)
        return results
