"""
src/app/system_dataclasses.py
REQ-2005: Vorinstallierte System-Datenklassen.
Werden beim App-Start automatisch in die Datenbank geseeded.
Loeschgeschuetzt (is_system=True).
"""
from __future__ import annotations

# Jede Klasse hat: name (deutsch, beschreibend), value_type, description, values
SYSTEM_DATACLASS_CATALOG: list[dict] = [
    {
        "name": "Text – Grenzwerte & Sonderzeichen",
        "value_type": "freetext",
        "description": "Typische Texteingaben die Systeme zum Absturz bringen oder Fehler provozieren",
        "values": [
            "",
            " ",
            "a",
            "a" * 255,
            "a" * 256,
            "<script>alert(1)</script>",
            "' OR '1'='1",
            "null",
            "undefined",
            "0",
            "true",
            "Ä ö ü ß € 中文 😀",
        ],
    },
    {
        "name": "Zahlen – Grenzwerte & Sonderwerte",
        "value_type": "freetext",
        "description": "Numerische Grenzwerte: Null, Extremwerte, Gleitkomma, Sonderwerte",
        "values": [
            "0", "-1", "1",
            "-2147483648", "2147483647", "2147483648", "-2147483649",
            "0.1", "-0.1", "0.0000001",
            "999999999999",
            "NaN", "Infinity", "-Infinity",
        ],
    },
    {
        "name": "Datum – Grenzwerte",
        "value_type": "freetext",
        "description": "Datumswerte an den Grenzen: Schaltjahr, ungültige Daten, alte Formate",
        "values": [
            "2000-01-01", "1900-01-01", "9999-12-31",
            "2024-02-29",   # gültiger Schaltjahrtag
            "2023-02-29",   # ungültig (kein Schaltjahr)
            "2024-01-32",   # Tag zu groß
            "2024-13-01",   # Monat zu groß
            "01/01/2024",   # US-Format
            "01.01.2024",   # deutsches Format
            "2024-00-00",   # Nulldatum
            "",
        ],
    },
    {
        "name": "E-Mail – Gültige Beispiele",
        "value_type": "freetext",
        "description": "Valide E-Mail-Adressen für positive Tests",
        "values": [
            "a@b.c",
            "test@example.com",
            "test+filter@example.com",
            "user.name@sub.domain.org",
            "123@numbers.de",
        ],
    },
    {
        "name": "E-Mail – Ungültige Beispiele",
        "value_type": "freetext",
        "description": "Invalide E-Mail-Adressen für negative Tests",
        "values": [
            "",
            "test@",
            "@example.com",
            "test@.com",
            "test@example",
            "test @example.com",
            "test@@example.com",
            "kein-at-zeichen",
        ],
    },
    {
        "name": "Wahrheitswerte – Alle Varianten",
        "value_type": "freetext",
        "description": "Alle üblichen Schreibweisen von Boolean-Werten inkl. Randfälle",
        "values": [
            "true", "false",
            "True", "False",
            "TRUE", "FALSE",
            "1", "0",
            "yes", "no",
            "ja", "nein",
            "", "null",
        ],
    },
    {
        "name": "URLs – Grenzwerte",
        "value_type": "freetext",
        "description": "URL-Eingaben für Sicherheits- und Validierungstests",
        "values": [
            "",
            "http://example.com",
            "https://example.com",
            "javascript:alert(1)",
            "http://",
            "http://localhost",
            "http://127.0.0.1",
            "ftp://files.example.com",
        ],
    },
    {
        "name": "Passwörter – Schwache Beispiele",
        "value_type": "freetext",
        "description": "Häufige schwache Passwörter und Randfälle für Passwortfeld-Tests",
        "values": [
            "",
            "a",
            "12345678",
            "password",
            "Password1!",
            "' OR '1'='1",
            "<script>",
            "123456",
            "qwerty",
        ],
    },
]


def seed_system_dataclasses(db) -> int:
    """
    Legt System-Datenklassen an falls noch nicht vorhanden.
    Gibt Anzahl neu angelegter Klassen zurueck.
    """
    from . import models

    created = 0
    for entry in SYSTEM_DATACLASS_CATALOG:
        existing = db.query(models.DataClass).filter(models.DataClass.name == entry["name"]).first()
        if existing:
            # Sicherstellen dass is_system gesetzt ist
            if not existing.is_system:
                existing.is_system = True
                db.flush()
            continue
        dc = models.DataClass(
            name=entry["name"],
            value_type=entry["value_type"],
            description=entry["description"],
            is_system=True,
        )
        db.add(dc)
        db.flush()
        for val_str in entry["values"]:
            db.add(models.DataClassValue(dataclass_id=dc.id, value=val_str))
        created += 1
    db.commit()
    return created