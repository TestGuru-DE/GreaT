# REQ-EPIC18-PRE: Rate-Limiter Tests
# ADR-015: Security Pre-Tasks fuer EPIC-18 (Multi-User)
# OWASP: A07 Identification and Authentication Failures
import time
import pytest
from app.rate_limiter import RateLimiter


def test_rate_limiter_allows_initial_requests():
    """First 5 requests are allowed."""
    limiter = RateLimiter(max_attempts=5, time_window=60)
    for i in range(5):
        is_limited, retry_after = limiter.is_rate_limited("test-ip")
        assert is_limited is False, f"Request {i+1} should not be limited"
        assert retry_after == 0


def test_rate_limiter_blocks_after_max_attempts():
    """6th request is rate-limited."""
    limiter = RateLimiter(max_attempts=5, time_window=60)
    # 5 requests aufbrauchen
    for _ in range(5):
        limiter.is_rate_limited("test-ip")
    
    # 6. request sollte limited sein
    is_limited, retry_after = limiter.is_rate_limited("test-ip")
    assert is_limited is True
    assert retry_after > 0


def test_rate_limiter_resets_after_time_window():
    """After time_window, requests are allowed again."""
    limiter = RateLimiter(max_attempts=5, time_window=1)  # 1 Sekunde fuer Test
    # 5 requests aufbrauchen
    for _ in range(5):
        limiter.is_rate_limited("test-ip")
    
    # Limited sein
    is_limited, _ = limiter.is_rate_limited("test-ip")
    assert is_limited is True
    
    # Warten bis Zeitfenster abgelaufen
    time.sleep(1.1)
    
    # Wieder erlaubt
    is_limited, retry_after = limiter.is_rate_limited("test-ip")
    assert is_limited is False
    assert retry_after == 0


def test_rate_limiter_different_ips_independent():
    """Different IPs have independent rate limits."""
    limiter = RateLimiter(max_attempts=5, time_window=60)
    # IP1 aufbrauchen
    for _ in range(5):
        limiter.is_rate_limited("ip-1")
    
    # IP1 limited
    is_limited, _ = limiter.is_rate_limited("ip-1")
    assert is_limited is True
    
    # IP2 noch nicht limited
    is_limited, _ = limiter.is_rate_limited("ip-2")
    assert is_limited is False


def test_rate_limiter_retry_after_reasonable():
    """Retry-After value is within time_window."""
    limiter = RateLimiter(max_attempts=5, time_window=60)
    for _ in range(5):
        limiter.is_rate_limited("test-ip")
    
    is_limited, retry_after = limiter.is_rate_limited("test-ip")
    assert is_limited is True
    assert 1 <= retry_after <= 61  # Within time_window + 1


def test_rate_limiter_global_instance():
    """Global login_rate_limiter instance exists with correct defaults."""
    from app.rate_limiter import login_rate_limiter
    assert login_rate_limiter.max_attempts == 5
    assert login_rate_limiter.time_window == 60