## Automated PR Review

![](https://img.shields.io/badge/issues-4%20found%20%E2%86%92%204%20fixed-success?style=flat-square) ![](https://img.shields.io/badge/coverage-0%25%20%E2%86%92%20100%25-blue?style=flat-square) ![](https://img.shields.io/badge/tests-17%20added-blue?style=flat-square) ![](https://img.shields.io/badge/screenshots-0%20(no%20UI)-lightgrey?style=flat-square)

> [!CAUTION]
> **4 bugs fixed in `src/rate_limiter.py`** -- 2 critical, 1 high, 1 medium.
>
> **1. Race condition in `allow()` (critical)** -- bucket lookup happened outside the lock while mutations happened inside it. Two concurrent threads could both see `bucket is None` and create duplicate entries, or both read a stale `count` and exceed the limit.
> ```diff
> -        bucket = self._buckets.get(key)
> -
> -        if bucket is None:
> -            with self._lock:
> -                self._buckets[key] = _BucketEntry(count=1, window_start=now)
> -            return True
> +        with self._lock:
> +            bucket = self._buckets.get(key)
> +
> +            if bucket is None:
> +                bucket = _BucketEntry(count=0, window_start=now)
> +                self._buckets[key] = bucket
> ```
> [`rate_limiter.py#L35`](https://github.com/mshuffett/pr-review-test-backend/blob/3a9bc54bcb38fd5770168572a1212f3f0f0ac49c/src/rate_limiter.py#L35)
>
> **2. `time.time()` used instead of `time.monotonic()` (critical)** -- `time.time()` can jump backward during NTP sync or DST changes, breaking window expiry calculations. Monotonic clock is the correct choice for elapsed-time measurement.
> ```diff
> -        now = time.time()  # BUG: should use time.monotonic()
> +        now = time.monotonic()
> ```
> [`rate_limiter.py#L33`](https://github.com/mshuffett/pr-review-test-backend/blob/3a9bc54bcb38fd5770168572a1212f3f0f0ac49c/src/rate_limiter.py#L33)
>
> **3. Bare `except:` in `reset()` (high)** -- catches `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`, masking fatal errors. Fixed to catch only `KeyError`.
> ```diff
> -        except:  # BUG: bare except
> +        except KeyError:
> ```
> [`rate_limiter.py#L64`](https://github.com/mshuffett/pr-review-test-backend/blob/3a9bc54bcb38fd5770168572a1212f3f0f0ac49c/src/rate_limiter.py#L64)
>
> **4. First request always allowed regardless of `max_requests` (high)** -- when `max_requests=0`, the first request for a new key created a bucket with `count=1` and returned `True` without checking the limit. The window-reset path had the same issue. Fixed by initializing `count=0` and always checking `count < max_requests` before allowing.
> ```diff
> -            if bucket is None:
> -                self._buckets[key] = _BucketEntry(count=1, window_start=now)
> -                return True
> -            if now - bucket.window_start >= self.window_seconds:
> -                bucket.count = 1
> -                bucket.window_start = now
> -                return True
> +            if bucket is None:
> +                bucket = _BucketEntry(count=0, window_start=now)
> +                self._buckets[key] = bucket
> +            elif now - bucket.window_start >= self.window_seconds:
> +                bucket.count = 0
> +                bucket.window_start = now
> +            if bucket.count < self.max_requests:
> +                bucket.count += 1
> +                return True
> ```
> [`rate_limiter.py#L38-L49`](https://github.com/mshuffett/pr-review-test-backend/blob/3a9bc54bcb38fd5770168572a1212f3f0f0ac49c/src/rate_limiter.py#L38-L49)

<details>
<summary><strong>All issues (1 more)</strong></summary>

| Sev | Issue | Fix | Link |
|:---:|-------|-----|:----:|
| :yellow_circle: | Unused `field` import from `dataclasses` | Removed import | [`rate_limiter.py#L7`](https://github.com/mshuffett/pr-review-test-backend/blob/3a9bc54bcb38fd5770168572a1212f3f0f0ac49c/src/rate_limiter.py#L7) |

</details>

<details>
<summary><strong>Tests (17 added, all passing)</strong></summary>

| Suite | Count | Coverage | Link |
|-------|:-----:|:--------:|:----:|
| `test_rate_limiter.py` | 13 | 100% of `rate_limiter.py` | [`tests/test_rate_limiter.py`](https://github.com/mshuffett/pr-review-test-backend/blob/3a9bc54bcb38fd5770168572a1212f3f0f0ac49c/tests/test_rate_limiter.py) |
| `test_config.py` | 4 | 100% of `config.py` | [`tests/test_config.py`](https://github.com/mshuffett/pr-review-test-backend/blob/3a9bc54bcb38fd5770168572a1212f3f0f0ac49c/tests/test_config.py) |

**Test output:**
```
24 passed in 0.03s

Name                  Stmts   Miss  Cover
-----------------------------------------
src/__init__.py           0      0   100%
src/config.py            12      0   100%
src/rate_limiter.py      40      0   100%
src/storage.py           24      0   100%
-----------------------------------------
TOTAL                    76      0   100%
```

**Key tests:**
- Basic allow/deny within limits
- Per-key independence
- Window expiry and reset
- `remaining()` accuracy
- `reset()` clears state; resetting nonexistent key is safe
- Edge case: `max_requests=0` denies all
- Edge case: `max_requests=1` allows exactly one
- Thread safety: 20 concurrent threads cannot exceed the limit
- Verifies `time.monotonic()` is used (not `time.time()`)
- `RateLimitConfig` defaults and custom values

</details>

**No UI changes detected** -- all changed files (`src/rate_limiter.py`, `src/config.py`) are pure Python backend code. E2E/UI testing and GIF recording correctly skipped.
