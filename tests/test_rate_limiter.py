"""Tests for the RateLimiter class."""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest

from src.rate_limiter import RateLimiter


@pytest.fixture
def limiter() -> RateLimiter:
    """A limiter allowing 3 requests per 1-second window."""
    return RateLimiter(max_requests=3, window_seconds=1.0)


# --- basic allow/deny ---


def test_allows_requests_within_limit(limiter: RateLimiter) -> None:
    """Requests up to max_requests should all be allowed."""
    assert limiter.allow("key") is True
    assert limiter.allow("key") is True
    assert limiter.allow("key") is True


def test_denies_request_over_limit(limiter: RateLimiter) -> None:
    """The request exceeding max_requests should be denied."""
    for _ in range(3):
        limiter.allow("key")
    assert limiter.allow("key") is False


def test_different_keys_independent(limiter: RateLimiter) -> None:
    """Rate limits are tracked per-key."""
    for _ in range(3):
        limiter.allow("a")
    assert limiter.allow("a") is False
    # "b" should still be allowed
    assert limiter.allow("b") is True


# --- window reset ---


def test_window_resets_after_expiry(limiter: RateLimiter) -> None:
    """After window_seconds elapse, the counter should reset."""
    for _ in range(3):
        limiter.allow("key")
    assert limiter.allow("key") is False

    # Advance monotonic clock past the window
    with patch("src.rate_limiter.time.monotonic", return_value=time.monotonic() + 2.0):
        assert limiter.allow("key") is True


# --- remaining ---


def test_remaining_full_when_no_requests(limiter: RateLimiter) -> None:
    """Remaining should equal max_requests for an unseen key."""
    assert limiter.remaining("key") == 3


def test_remaining_decreases(limiter: RateLimiter) -> None:
    """Each allowed request decreases remaining by 1."""
    limiter.allow("key")
    assert limiter.remaining("key") == 2
    limiter.allow("key")
    assert limiter.remaining("key") == 1
    limiter.allow("key")
    assert limiter.remaining("key") == 0


def test_remaining_never_negative(limiter: RateLimiter) -> None:
    """Remaining should never go below 0."""
    for _ in range(5):
        limiter.allow("key")
    assert limiter.remaining("key") == 0


# --- reset ---


def test_reset_clears_key(limiter: RateLimiter) -> None:
    """After reset, the key should be allowed again."""
    for _ in range(3):
        limiter.allow("key")
    assert limiter.allow("key") is False

    limiter.reset("key")
    assert limiter.allow("key") is True
    assert limiter.remaining("key") == 2


def test_reset_nonexistent_key_no_error(limiter: RateLimiter) -> None:
    """Resetting a key that doesn't exist should not raise."""
    limiter.reset("nonexistent")  # should not raise


# --- edge cases ---


def test_zero_max_requests() -> None:
    """A limiter with max_requests=0 should deny everything."""
    limiter = RateLimiter(max_requests=0, window_seconds=1.0)
    assert limiter.allow("key") is False


def test_single_request_limit() -> None:
    """A limiter with max_requests=1 should allow exactly one request."""
    limiter = RateLimiter(max_requests=1, window_seconds=1.0)
    assert limiter.allow("key") is True
    assert limiter.allow("key") is False


# --- thread safety ---


def test_concurrent_access_does_not_exceed_limit() -> None:
    """Under concurrent access, total allowed requests should not exceed max_requests."""
    limiter = RateLimiter(max_requests=100, window_seconds=60.0)
    allowed_count = 0
    lock = threading.Lock()
    barrier = threading.Barrier(20)

    def worker() -> None:
        nonlocal allowed_count
        barrier.wait()  # synchronize all threads to start at once
        for _ in range(10):
            if limiter.allow("shared"):
                with lock:
                    allowed_count += 1

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 20 threads * 10 attempts = 200 attempts, but limit is 100
    assert allowed_count == 100


# --- uses monotonic clock ---


def test_uses_monotonic_clock() -> None:
    """Verify the limiter uses time.monotonic, not time.time."""
    with patch("src.rate_limiter.time.monotonic") as mock_mono:
        mock_mono.return_value = 1000.0
        limiter = RateLimiter(max_requests=1, window_seconds=1.0)
        assert limiter.allow("key") is True
        assert limiter.allow("key") is False

        # Advance monotonic clock
        mock_mono.return_value = 1002.0
        assert limiter.allow("key") is True

        mock_mono.assert_called()
