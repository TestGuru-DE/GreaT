"""REQ-1300 Testintegritaet: Schutz der lokalen Produktiv-Datenbank.

Tests duerfen die lokale DB (z.B. ``great.db``) weder oeffnen noch veraendern.
Dieses Modul erfasst Fingerprints (SHA-256, Groesse, mtime_ns) aller bekannten
Speicherorte der lokalen DB inklusive WAL-/SHM-Sidecars. Es liest die Dateien nur
zum Hashen und schreibt nie.

Der Snapshot wird beim ersten Import erstellt. ``conftest.py`` importiert dieses
Modul vor jedem Datenbankzugriff.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIDECAR_SUFFIXES = ("", "-wal", "-shm")

Fingerprint = Tuple[str, int, int]


def guarded_paths() -> List[Path]:
    """Alle Orte, an denen eine reale lokale DB liegen kann (dedupliziert)."""
    candidates = [
        PROJECT_ROOT / "great.db",
        PROJECT_ROOT / "src" / "great.db",
        Path.cwd() / "great.db",
        Path.home() / ".great" / "great.db",
    ]
    unique: List[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def file_fingerprint(path: Path) -> Optional[Fingerprint]:
    """Liefert (sha256, size, mtime_ns) oder None, wenn die Datei fehlt."""
    if not path.is_file():
        return None
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return (digest.hexdigest(), stat.st_size, stat.st_mtime_ns)


def snapshot() -> Dict[str, Optional[Fingerprint]]:
    """Fingerprints aller geschuetzten Dateien, Schluessel = Pfad als String."""
    result: Dict[str, Optional[Fingerprint]] = {}
    for base in guarded_paths():
        for suffix in SIDECAR_SUFFIXES:
            target = base.with_name(base.name + suffix)
            result[str(target)] = file_fingerprint(target)
    return result


def diff(
    before: Dict[str, Optional[Fingerprint]],
    after: Dict[str, Optional[Fingerprint]],
) -> List[str]:
    """Liste der Pfade, deren Fingerprint sich geaendert hat (inkl. Anlegen/Loeschen)."""
    keys = sorted(set(before) | set(after))
    return [key for key in keys if before.get(key) != after.get(key)]


# Snapshot vor jeglichem Datenbankzugriff des Testlaufs.
START_SNAPSHOT: Dict[str, Optional[Fingerprint]] = snapshot()
