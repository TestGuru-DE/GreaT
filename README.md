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

**Einfachste Methode:** Doppelklick auf `Start.bat`

**Oder manuell:**
```cmd
set PYTHONPATH=src
python -m uvicorn src.app.main:app --reload --port 8000
```

Browser oeffnen: **http://localhost:8000**

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

## Technologie

| Schicht | Technologie |
|---|---|
| Backend | Python 3.10+, FastAPI, SQLAlchemy, SQLite |
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