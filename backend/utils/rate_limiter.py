"""Simple in-memory sliding-window rate limiter (30 req/min by default).

Sufficient for a single-instance PHC deployment; swap for Redis when
scaling horizontally.
"""
import threading
import time
from collections import defaultdict, deque

_buckets = defaultdict(deque)
_lock = threading.Lock()


def check_rate_limit(key, limit, window_seconds=60):
    """Return True if `key` is under `limit` within the window (records the hit)."""
    now = time.time()
    with _lock:
        bucket = _buckets[key]
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True
