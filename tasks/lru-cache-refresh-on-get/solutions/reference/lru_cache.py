"""A fixed-capacity least-recently-used cache."""
from collections import OrderedDict


class LRUCache:
    """Cache that evicts the least-recently-used entry once it is full."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._store: OrderedDict = OrderedDict()

    def get(self, key):
        """Return the value for `key`, refreshing its recency, or None if absent."""
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key, value) -> None:
        """Insert or update `key`, evicting the least-recently-used entry if
        the cache is over capacity afterward."""
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self._capacity:
            self._store.popitem(last=False)
