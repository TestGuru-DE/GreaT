# Risk Log – G.R.E.A.T.
Version: 1.0
Phase: 0 – Bestandsaufnahme
Erstellt: 2026-06-10
Erstellt von: Program Manager Agent

---

## Bewertungsschema

**Wahrscheinlichkeit:** 1 (gering) – 5 (sehr hoch)
**Impact:** 1 (gering) – 5 (kritisch)
**Risikoscore:** Wahrscheinlichkeit × Impact

| Score | Ampel |
|---|---|
| 1–4 | 🟢 Niedrig |
| 5–9 | 🟡 Mittel |
| 10–25 | 🔴 Hoch |

---

## Kategorie: Fachlich

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-F-001 | Kombinatorik-Algorithmen liefern inkorrekte Testfälle | 3 | 5 | 15 | 🔴 | TDD + mathematische Verifikation (alle Paare prüfen) |
| RISK-F-002 | Geschäftsregeln werden beim Generieren nicht korrekt angewendet | 4 | 5 | 20 | 🔴 | Regeltypen vollständig implementieren, testen |
| RISK-F-003 | Fehlende Grenzwertanalyse macht Kern-Feature unvollständig | 4 | 4 | 16 | 🔴 | Grenzwertmodul priorisieren in Phase 1 |
| RISK-F-004 | Inkonsistenz zwischen Ist-Implementierung und Requirements | 3 | 4 | 12 | 🔴 | requirements_v1.1.md als Single Source of Truth |
| RISK-F-005 | ISTQB-Terminologie nicht konsistent umgesetzt | 2 | 3 | 6 | 🟡 | Glossar aus ISTQB-Standard referenzieren |

## Kategorie: Technisch

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-T-001 | Monolithischer main.py wird unwartbar | 5 | 4 | 20 | 🔴 | Sofort in Router-Module aufteilen (DEBT-001) |
| RISK-T-002 | Kein Migrations-Framework führt zu Datenverlust/Fehler bei Updates | 4 | 5 | 20 | 🔴 | Alembic einführen (DEBT-002) |
| RISK-T-003 | Abhängigkeitskonflikte durch unpinned requirements.txt | 3 | 3 | 9 | 🟡 | Versionspinning + requirements-lock.txt |
| RISK-T-004 | Zwei parallele Backends (src/app + src/backend) erzeugen Verwirrung | 4 | 3 | 12 | 🔴 | src/backend/ archivieren |
| RISK-T-005 | Frontend-Technologie (HTMX) nicht auf Zielarchitektur (React) ausgerichtet | 5 | 3 | 15 | 🔴 | ADR-001 verfassen: Python beibehalten vs. .NET |
| RISK-T-006 | SQLite für Multi-User-Betrieb ungeeignet | 2 | 4 | 8 | 🟡 | PostgreSQL-Migration in Roadmap vorbereiten |
| RISK-T-007 | Keine Fehlerbehandlung in API (keine 4xx/5xx) | 4 | 3 | 12 | 🔴 | Exception Handler für FastAPI einführen |

## Kategorie: Qualität

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-Q-001 | Coverage-Ziele (100%) können nicht eingehalten werden | 3 | 4 | 12 | 🔴 | pytest-cov sofort einrichten, Baseline messen |
| RISK-Q-002 | TDD nicht nachweisbar (keine Commit-Historie zeigt Test-First) | 3 | 3 | 9 | 🟡 | Branching-Strategie: Feature-Branches mit TDD-Commits |
| RISK-Q-003 | Fehlende Tests für Geschäftsregeln | 5 | 4 | 20 | 🔴 | Sofortmaßnahme in Phase 1 Sprint 1 |
| RISK-Q-004 | Mutation Testing Ziel (>=90%) nicht erreichbar ohne Basis-Tests | 3 | 3 | 9 | 🟡 | Erst Coverage 100%, dann Mutation Testing |
| RISK-Q-005 | Keine Systemtests (End-to-End) vorhanden | 4 | 3 | 12 | 🔴 | Playwright oder Selenium für E2E Tests |

## Kategorie: Sicherheit

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-S-001 | Keine Authentifizierung – alle Endpunkte öffentlich | 5 | 4 | 20 | 🔴 | Für Team-Nutzung: OAuth2/JWT vorbereiten (SYSTEM_v1.0 §15) |
| RISK-S-002 | SQL-Injection via SQLAlchemy ORM (gering, da ORM parametrisiert) | 1 | 5 | 5 | 🟡 | ORM-Muster beibehalten, kein Raw-SQL |
| RISK-S-003 | Sensitive Daten in tanos.db nicht verschlüsselt | 2 | 3 | 6 | 🟡 | Dokumentieren: Testdaten sind nicht sensitiv, für Produktiv: Encryption at Rest |
| RISK-S-004 | OWASP Top 10 nicht systematisch geprüft | 3 | 4 | 12 | 🔴 | Security Review durch Security Architect Agent vor Release |
| RISK-S-005 | Keine Input-Validierung auf UI-Ebene (HTMX-Forms) | 3 | 3 | 9 | 🟡 | Pydantic-Validierung auf API-Ebene prüfen und erweitern |

## Kategorie: Betrieb

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-B-001 | Keine CI/CD Pipeline – manuelle Releases fehleranfällig | 4 | 4 | 16 | 🔴 | GitHub Actions Pipeline (Tests + Lint + Build) |
| RISK-B-002 | Kein Installationspaket für Nicht-Techniker (GREAT.exe fehlt) | 4 | 4 | 16 | 🔴 | PyInstaller oder NSIS Installer erstellen |
| RISK-B-003 | Start.bat ohne Fehlerbehandlung | 2 | 2 | 4 | 🟢 | Verbessern mit Fehler-Output |
| RISK-B-004 | Keine Logging-Infrastruktur | 3 | 3 | 9 | 🟡 | Python logging + log-Rotation einführen |
| RISK-B-005 | tanos.db ohne Backup-Strategie | 3 | 4 | 12 | 🔴 | Automatisches DB-Backup dokumentieren |

---

## Zusammenfassung Top-Risiken

| Rank | ID | Score | Beschreibung |
|---|---|---|---|
| 1 | RISK-S-001 | 20 | Keine Authentifizierung |
| 2 | RISK-T-001 | 20 | Monolithischer main.py |
| 3 | RISK-T-002 | 20 | Kein Migrations-Framework |
| 4 | RISK-F-002 | 20 | Geschäftsregeln fehlerhaft |
| 5 | RISK-Q-003 | 20 | Tests für Geschäftsregeln fehlen |
| 6 | RISK-F-003 | 16 | Grenzwertanalyse fehlt |
| 7 | RISK-B-001 | 16 | Keine CI/CD |
| 8 | RISK-B-002 | 16 | Kein Installationspaket |
| 9 | RISK-T-005 | 15 | Frontend-Technologie-Konflikt |
| 10 | RISK-F-001 | 15 | Kombinatorik-Korrektheit |
