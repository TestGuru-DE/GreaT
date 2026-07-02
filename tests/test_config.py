"""REQ-4007: GREAT_PORT Konfiguration.

Tests für die Umgebungsvariablen-basierte Portkonfiguration.
"""
import os
import sys
import pytest


def test_default_port():
    """Default GREAT_PORT ist 8000."""
    # Entferne GREAT_PORT aus Umgebung
    os.environ.pop("GREAT_PORT", None)
    
    # Entlade config-Modul falls bereits geladen
    if "app.config" in sys.modules:
        del sys.modules["app.config"]
    
    # Importiere neu
    from app.config import GREAT_PORT
    assert GREAT_PORT == 8000, f"Expected GREAT_PORT=8000, got {GREAT_PORT}"


def test_custom_port():
    """GREAT_PORT kann via Env-Variable gesetzt werden."""
    # Setze GREAT_PORT
    os.environ["GREAT_PORT"] = "9000"
    
    # Entlade config-Modul
    if "app.config" in sys.modules:
        del sys.modules["app.config"]
    
    # Importiere neu
    from app.config import GREAT_PORT
    assert GREAT_PORT == 9000, f"Expected GREAT_PORT=9000, got {GREAT_PORT}"
    
    # Cleanup
    os.environ.pop("GREAT_PORT", None)
    if "app.config" in sys.modules:
        del sys.modules["app.config"]


def test_custom_port_string_parsing():
    """GREAT_PORT wird korrekt als Integer geparst."""
    os.environ["GREAT_PORT"] = "3000"
    
    if "app.config" in sys.modules:
        del sys.modules["app.config"]
    
    from app.config import GREAT_PORT
    assert isinstance(GREAT_PORT, int), "GREAT_PORT must be int"
    assert GREAT_PORT == 3000
    
    os.environ.pop("GREAT_PORT", None)
    if "app.config" in sys.modules:
        del sys.modules["app.config"]


def test_default_host():
    """Default GREAT_HOST ist 0.0.0.0."""
    os.environ.pop("GREAT_HOST", None)
    
    if "app.config" in sys.modules:
        del sys.modules["app.config"]
    
    from app.config import GREAT_HOST
    assert GREAT_HOST == "0.0.0.0", f"Expected GREAT_HOST=0.0.0.0, got {GREAT_HOST}"


def test_env_example_exists():
    """.env.example muss im Repository existieren."""
    assert os.path.exists(".env.example"), ".env.example file not found"
    
    # Prüfe Inhalt
    with open(".env.example", "r") as f:
        content = f.read()
        assert "GREAT_PORT" in content, ".env.example must mention GREAT_PORT"
        assert "GREAT_HOST" in content, ".env.example must mention GREAT_HOST"


def test_env_not_committed():
    """.env sollte nicht im Repository sein (nur .env.example)."""
    assert not os.path.exists(".env"), ".env must not be committed (use .env.example instead)"
