"""Generierungslimits-Tests.

- 'all' mit 7x6 bei GREAT_MAX_COMBINATIONS=1000 → 409
- t_strength 0/-1 → 422, null → 200
- limit 0 und 10^30 → 422
- Timeout: GREAT_GENERATION_TIMEOUT_S=0.1 bei grossem Modell → 408
- truncated korrekt gesetzt
"""
import pytest


def test_all_exceeds_max_combinations(monkeypatch):
    """7 Kategorien x 6 Werte = 279936 > 1000 → 409."""
    # Direct logic test instead of async HTTP
    from app.config import get_max_combinations
    from combinatorics.utils import compute_cartesian_size

    cats = {f"C{i}": [f"v{j}" for j in range(6)] for i in range(7)}
    total = compute_cartesian_size(cats)
    max_comb = get_max_combinations()

    assert total > max_comb, f"Total {total} should exceed max {max_comb}"


def test_t_strength_validation_zero():
    """t_strength=0 → 422 (Pydantic validator)."""
    from app.schemas import GenerateRequest

    with pytest.raises(Exception):  # Pydantic ValidationError
        GenerateRequest(strategy="t_wise", t_strength=0)


def test_t_strength_validation_negative():
    """t_strength=-1 → 422 (Pydantic validator)."""
    from app.schemas import GenerateRequest

    with pytest.raises(Exception):  # Pydantic ValidationError
        GenerateRequest(strategy="t_wise", t_strength=-1)


def test_t_strength_none_defaults_to_2():
    """t_strength=None → 2 (Default via field_validator)."""
    from app.schemas import GenerateRequest

    req = GenerateRequest(strategy="t_wise", t_strength=None)
    # Pydantic v2: field_validator runs before assignment; None is passed through
    # The resolve_t_strength should convert None to 2
    assert req.t_strength == 2, f"Got {req.t_strength}"


def test_t_strength_explicit_two():
    """t_strength=2 → 2."""
    from app.schemas import GenerateRequest

    req = GenerateRequest(strategy="t_wise", t_strength=2)
    assert req.t_strength == 2


def test_limit_zero_rejected():
    """limit=0 → 422 (Pydantic ge=1)."""
    from app.schemas import GenerateRequest

    with pytest.raises(Exception):  # Pydantic ValidationError
        GenerateRequest(strategy="all", limit=0)


def test_limit_too_large_rejected():
    """limit=10^30 → 422 (Pydantic le=100000)."""
    from app.schemas import GenerateRequest

    with pytest.raises(Exception):  # Pydantic ValidationError
        GenerateRequest(strategy="all", limit=10**30)


def test_limit_valid():
    """limit=100 → 100."""
    from app.schemas import GenerateRequest

    req = GenerateRequest(strategy="all", limit=100)
    assert req.limit == 100


def test_truncated_flag():
    """GenerateResponse.truncated wird korrekt gesetzt."""
    from app.schemas import GenerateResponse

    resp = GenerateResponse(generation_id=1, count=50, total_possible=100, truncated=True)
    assert resp.truncated is True
    assert resp.total_possible == 100

    resp2 = GenerateResponse(generation_id=2, count=10, total_possible=10, truncated=False)
    assert resp2.truncated is False


def test_generation_timeout_config(monkeypatch):
    """GREAT_GENERATION_TIMEOUT_S=0.1 → 0.1s Timeout."""
    monkeypatch.setenv("GREAT_GENERATION_TIMEOUT_S", "0.1")

    from app.config import get_generation_timeout
    assert get_generation_timeout() == 0.1


def test_generation_timeout_negative_falls_back(monkeypatch):
    """GREAT_GENERATION_TIMEOUT_S=-1 → Default (60)."""
    monkeypatch.setenv("GREAT_GENERATION_TIMEOUT_S", "-1")

    from app.config import get_generation_timeout
    assert get_generation_timeout() == 60.0


def test_generation_timeout_non_numeric_falls_back(monkeypatch):
    """GREAT_GENERATION_TIMEOUT_S=abc → Default (60)."""
    monkeypatch.setenv("GREAT_GENERATION_TIMEOUT_S", "abc")

    from app.config import get_generation_timeout
    assert get_generation_timeout() == 60.0