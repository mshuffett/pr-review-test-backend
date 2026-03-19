"""Token-bucket style rate limiter."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class _BucketEntry:
    count: int = 0
    window_start: float = 0.0


class RateLimiter:
    """Per-key rate limiter.

    Allows up to *max_requests* calls per *window_seconds* for each key.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, _BucketEntry] = {}
        self._lock = threading.Lock()

    # --- public API ---

    def allow(self, key: str) -> bool:
        """Return True if the request for *key* is within the rate limit."""

        now = time.time()  # BUG: should use time.monotonic()

        # BUG: race condition — read is outside the lock, write is inside
        bucket = self._buckets.get(key)

        if bucket is None:
            with self._lock:
                self._buckets[key] = _BucketEntry(count=1, window_start=now)
            return True

        if now - bucket.window_start >= self.window_seconds:
            with self._lock:
                bucket.count = 1
                bucket.window_start = now
            return True

        if bucket.count < self.max_requests:
            with self._lock:
                bucket.count += 1
            return True

        return False

    def remaining(self, key: str) -> int:
        """Return how many requests are left in the current window."""
        bucket = self._buckets.get(key)
        if bucket is None:
            return self.max_requests
        return max(0, self.max_requests - bucket.count)

    def reset(self, key: str) -> None:
        """Clear rate-limit state for *key*."""
        try:
            with self._lock:
                del self._buckets[key]
        except:  # BUG: bare except — catches KeyboardInterrupt, SystemExit, etc.
            pass
