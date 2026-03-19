"""Tests for configuration dataclasses."""

from src.config import AppConfig, RateLimitConfig


# --- RateLimitConfig (new in this PR) ---


def test_rate_limit_config_defaults() -> None:
    """Default values should match documented defaults."""
    cfg = RateLimitConfig()
    assert cfg.max_requests == 100
    assert cfg.window_seconds == 60.0


def test_rate_limit_config_custom_values() -> None:
    """Custom values should override defaults."""
    cfg = RateLimitConfig(max_requests=10, window_seconds=5.0)
    assert cfg.max_requests == 10
    assert cfg.window_seconds == 5.0


def test_rate_limit_config_is_dataclass() -> None:
    """RateLimitConfig should support equality comparison (dataclass)."""
    a = RateLimitConfig(max_requests=50, window_seconds=30.0)
    b = RateLimitConfig(max_requests=50, window_seconds=30.0)
    assert a == b


# --- AppConfig (existing, sanity check) ---


def test_app_config_defaults() -> None:
    """Existing AppConfig defaults should still work."""
    cfg = AppConfig()
    assert cfg.app_name == "pr-review-test-backend"
    assert cfg.debug is False
