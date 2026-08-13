# G.R.E.A.T.

**Georg Radikal Einfacher Automatisierter TestcaseDesigner**  
**Version 1.0.0** – Initial Public Release (2026-07-01)

Open-Source-Tool fuer strukturiertes Testfall-Design nach ISTQB-Methodik.  
Unterstuetzt Aequivalenzklassen, Grenzwertanalyse, Pairwise und weitere Kombinatorik-Strategien.

---

## Schnellstart

### Installation

Vollstaendige Anleitung: [INSTALLATION.md](INSTALLATION.md)

Kurzfassung (Windows):
```cmd
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
```

### System starten

Vollstaendige Anleitung: [QUICKSTART.md](QUICKSTART.md)

**Für Anwender (ein Befehl):**
- **Windows:** Doppelklick auf `Start.bat`
- **Linux/Raspberry Pi:** `chmod +x Start.sh && ./Start.sh`

Öffne dann: **http://localhost:8000**

**Für Entwickler (mit Hot-Reload):**
- **Windows:** Doppelklick auf `Start-Dev.bat`
  - Backend: http://localhost:8000
  - Frontend Dev: http://localhost:5173 (Vite Hot-Reload)

**Manuell (ohne Batch/Shell-Skripte):**
```cmd
set PYTHONPATH=src
python -m uvicorn src.app.main:app --reload --port 8000
```

---

## Features

| Feature | Beschreibung |
|---|---|
| Projektmanagement | Projekte anlegen, oeffnen, loeschen |
| Kategorien & Werte | Baumstruktur mit Drag & Drop Sortierung |
| Kombinatorik-Strategien | Each Choice, Lineare Expansion, All Combinations, Pairwise, Risikobasiert |
| Grenzwertanalyse (BVA) | Automatische Grenzwert-Testfaelle fuer numerische Felder |
| System-Datenklassen | Vordefinierte Kataloge typischer Äquivalenzklassen für 7 Datentypen (String, Zahl, Datum, E-Mail, ...) |
| Regelwerk | Wenn-Dann-Abhaengigkeiten zwischen Kategorien |
| Export | JSON, Excel (.xlsx), CSV |
| Tastenkuerzel | STRG+N, DEL, Doppelklick, Rechtsklick-Kontextmenue |
| React-Frontend | Moderne zweispaltige Ansicht (Kategorienbaum + Testfalltabelle) |
| REST-API | Vollstaendige API mit Swagger-Dokumentation |

---

## Multi-User Betrieb (NEU in 1.0.0)

G.R.E.A.T. unterstützt **Multi-User-Scenarios** ab Release 1.0.0:

### SQLite (Standard, bis ~10 gleichzeitige Nutzer)

Funktioniert out-of-the-box mit folgenden Optimierungen:
- **WAL-Mode** (Write-Ahead Logging): Verhindert "database is locked" Fehler bei gleichzeitigen Zugriffen
- **Connection-Pool**: Effizientes Ressourcen-Management
- Datei-basiert → einfaches Backup und Deployment

```cmd
# Keine weitere Konfiguration nötig
python -m uvicorn src.app.main:app --port 8000
```

### PostgreSQL (für größere Teams, 100+ gleichzeitige Nutzer)

Für produktive Multi-User-Installationen mit vielen gleichzeitigen Nutzern:

```cmd
# 1. PostgreSQL installieren (z.B. via postgres.org oder Docker)
# 2. Datenbank anlegen:
#    CREATE DATABASE great_db;

# 3. .env anlegen mit PostgreSQL-Connection:
#    DATABASE_URL=postgresql://great_user:password@localhost:5432/great_db

# 4. Abhängigkeiten installieren:
pip install psycopg2-binary

# 5. Migrationen ausführen (falls vorhanden):
python -m alembic upgrade head

# 6. System starten
python -m uvicorn src.app.main:app --port 8000
```

### Optimistic Locking (Concurrent Edit Prevention)

Alle kritischen Tabellen haben `updated_at`-Timestamps für optimistisches Sperren:

| Tabelle | updated_at | Funktion |
|---|---|---|
| Projects | ✓ | Konflikt-Erkennung bei gleichzeitiger Bearbeitung |
| Categories | ✓ | Struktur-Änderungen koordinieren |
| Values | ✓ | Wert-Änderungen versionieren |
| Generations | ✓ | Test-Lauf-Generationen konsistent halten |

**Detaillierte Anleitung:** [INSTALLATION.md](INSTALLATION.md#multi-user-betrieb)

---

## Technologie

| Schicht | Technologie |
|---|---|
| Backend | Python 3.10+, FastAPI, SQLAlchemy, SQLite + PostgreSQL (optional) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand |
| Tests | pytest, pytest-cov, Vitest |
| Lizenz | AGPL-3.0 (Dual-Licensing) |

---

## Dokumentation

| Datei | Inhalt |
|---|---|
| [INSTALLATION.md](INSTALLATION.md) | Schritt-fuer-Schritt Installationsanleitung |
| [QUICKSTART.md](QUICKSTART.md) | System starten, erste Schritte, Tastenkuerzel |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | Release-Informationen v1.0.0 und Roadmap |
| [CHANGELOG.md](CHANGELOG.md) | Versionshistorie |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Tests ausfuehren und Coverage messen |
| [documentation/](documentation/) | Architektur, Entscheidungen, Risiken |

---

## Tests ausfuehren

```cmd
set PYTHONPATH=src
python -m pytest tests/ --ignore=tests/e2e -q
```

Mit Coverage:
```cmd
python -m pytest tests/ --ignore=tests/e2e --cov=src --cov-report=term-missing
```

---

## Lizenz

G.R.E.A.T. steht unter der **AGPL-3.0** mit differenziertem Nutzungsmodell:

### Kostenlose Nutzung (unter AGPL-3.0)

Der Einsatz von G.R.E.A.T. als Werkzeug für den Testfall-Entwurf ist **kostenlos** – auch in kommerziellen Umgebungen:

- ✅ Softwarehersteller, die eigene Produkte testen
- ✅ Interne QA-Teams
- ✅ Private, wissenschaftliche, akademische Nutzung
- ✅ Nicht-kommerzielle Open-Source-Projekte

### Genehmigungspflichtige Nutzung

Wer mit G.R.E.A.T. selbst **Geld verdient**, benötigt vorherige Genehmigung und schließt eine Umsatzbeteiligungs-Vereinbarung:

- ❌ Consultants, die Testfälle als bezahlte Dienstleistung erstellen
- ❌ Tool-Anbieter, die G.R.E.A.T. in kommerzielle Produkte integrieren
- ❌ SaaS-Anbieter, die G.R.E.A.T. gegen Bezahlung hosten

**Details:** siehe [NOTICE.md](NOTICE.md) und [LICENSE](LICENSE)

**Haftung:** Nutzung auf eigene Gefahr, keinerlei Haftung durch den Autor.