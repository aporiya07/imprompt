"""Small in-process TTL cache for pipeline artifacts (spec Phase 17).

Cost rule: the expensive vision analysis must not re-run for the same normalized
image within a session. Keys are stable hashes, values are typed artifacts.
"""
import time
from typing import Any


class TTLCache:
    def __init__(self, maxsize: int = 64, ttl_seconds: float = 1800.0):
        self._store: dict[str, tuple[float, Any]] = {}
        self._maxsize = maxsize
        self._ttl = ttl_seconds

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires, value = entry
        if expires < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.pop(key)
        elif len(self._store) >= self._maxsize:
            oldest = min(self._store, key=lambda k: self._store[k][0])
            self._store.pop(oldest)
        self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        self._store.clear()


# Analysis artifacts (VisualDNA + CreativeIntent + optional CollageAnalysis) keyed
# by normalized-image hash + vision model. DNA is mode-independent by design.
analysis_cache = TTLCache(maxsize=64, ttl_seconds=1800.0)
