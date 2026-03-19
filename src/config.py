from dataclasses import dataclass, field


@dataclass
class AppConfig:
    """Application configuration."""

    app_name: str = "pr-review-test-backend"
    debug: bool = False
    log_level: str = "INFO"
    storage_backend: str = "memory"
    max_keys: int = 10_000


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    max_requests: int = 100
    window_seconds: float = 60.0
