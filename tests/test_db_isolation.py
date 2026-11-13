"""REQ-1300 Testintegritaet: Tests duerfen die lokale Produktiv-DB nie oeffnen oder veraendern.

Entwickler-Bericht (Datensicherheit): Tests setzten das Schema der realen ``great.db``
zurueck. Diese Tests sichern die Isolation ab (siehe tests/conftest.py und tests/db_guard.py).
"""
import os
from pathlib import Path

import db_guard


def _engine_db_path() -> Path:
    from app.database import engine

    return Path(engine.url.database or "").resolve()


def test_engine_uses_temporary_database_file():
    """Die App-Engine zeigt exakt auf die von conftest bereitgestellte temporaere Test-DB."""
    db_path = _engine_db_path()
    expected = Path(os.environ["GREAT_TEST_DB_PATH"]).resolve()
    assert db_path == expected, f"Engine zeigt auf {db_path}, erwartet {expected}"


def test_engine_is_not_a_guarded_real_database():
    """Die Engine darf keinen der geschuetzten Speicherorte der realen DB verwenden."""
    db_path = _engine_db_path()
    assert db_path not in db_guard.guarded_paths(), f"Engine zeigt auf reale DB: {db_path}"


def test_real_database_unchanged_so_far():
    """Bis zu diesem Testzeitpunkt darf kein Test die reale great.db veraendert haben."""
    changes = db_guard.diff(db_guard.START_SNAPSHOT, db_guard.snapshot())
    assert changes == [], f"Reale DB durch Tests veraendert: {changes}"


def test_fingerprint_detects_content_change(tmp_path):
    """Der Fingerprint erkennt eine Aenderung und meldet fehlende Dateien als None."""
    probe = tmp_path / "probe.db"
    probe.write_bytes(b"alpha")
    before = db_guard.file_fingerprint(probe)
    probe.write_bytes(b"alpha-beta")
    assert db_guard.file_fingerprint(probe) != before
    assert db_guard.file_fingerprint(tmp_path / "absent.db") is None


def test_diff_reports_only_changed_entries():
    """diff() liefert genau die Pfade mit geaenderten Fingerprints."""
    before = {"a": None, "b": ("h", 1, 1)}
    after = {"a": ("h", 1, 1), "b": ("h", 1, 1)}
    assert db_guard.diff(before, after) == ["a"]
