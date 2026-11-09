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
| RISK-T-008 | Konflikte bei gleichzeitiger Bearbeitung durch mehrere Nutzer (Multi-User, EPIC-18) | 3 | 4 | 12 | 🔴 | HYBRID-Ansatz (ADR-012): Optimistic Concurrency (REQ-4021) + Stale-Data-Warning (REQ-4022), keine volle Realtime-Kollaboration in Sprint 11–13 |

## Kategorie: Qualität

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-Q-001 | Coverage-Ziele (100%) können nicht eingehalten werden | 3 | 4 | 12 | 🔴 | pytest-cov sofort einrichten, Baseline messen |
| RISK-Q-002 | TDD nicht nachweisbar (keine Commit-Historie zeigt Test-First) | 3 | 3 | 9 | 🟡 | Branching-Strategie: Feature-Branches mit TDD-Commits |
| RISK-Q-003 | Fehlende Tests für Geschäftsregeln | 5 | 4 | 20 | 🔴 | Sofortmaßnahme in Phase 1 Sprint 1 |
| RISK-Q-004 | Mutation Testing Ziel (>=90%) nicht erreichbar ohne Basis-Tests | 3 | 3 | 9 | 🟡 | Erst Coverage 100%, dann Mutation Testing |
| RISK-Q-005 | Keine Systemtests (End-to-End) vorhanden | 4 | 3 | 12 | 🔴 | Playwright oder Selenium für E2E Tests |
| RISK-Q-006 | Verstoesse gegen die React-Hook-Regeln (B2, Fehler #300) und fehlende Fehlergrenze (B3) werden nicht automatisch erkannt, da ESLint nicht konfiguriert ist | 3 | 4 | 12 | 🔴 | Vorschlag: ESLint mit `react-hooks`-Regeln einfuehren. Teilweise gemindert: Error Boundary (B3) und Regressionstests in `TestCasePanel.test.tsx` (B2) vorhanden |

## Kategorie: Sicherheit

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-S-001 | Keine Authentifizierung – alle Endpunkte öffentlich | 5 | 4 | 20 | 🔴 | Für Team-Nutzung: OAuth2/JWT vorbereiten (SYSTEM_v1.0 §15) |
| RISK-S-002 | SQL-Injection via SQLAlchemy ORM (gering, da ORM parametrisiert) | 1 | 5 | 5 | 🟡 | ORM-Muster beibehalten, kein Raw-SQL |
| RISK-S-003 | Sensitive Daten in tanos.db nicht verschlüsselt | 2 | 3 | 6 | 🟡 | Dokumentieren: Testdaten sind nicht sensitiv, für Produktiv: Encryption at Rest |
| RISK-S-004 | OWASP Top 10 nicht systematisch geprüft | 3 | 4 | 12 | 🔴 | Security Review durch Security Architect Agent vor Release |
| RISK-S-005 | Keine Input-Validierung auf UI-Ebene (HTMX-Forms) | 3 | 3 | 9 | 🟡 | Pydantic-Validierung auf API-Ebene prüfen und erweitern |
| RISK-S-016 | Default-Admin mit festem Passwort `changeme123!` (src/app/bootstrap.py); kein Zwang zum Passwortwechsel nach dem ersten Login; Passwort steht im Quellcode des Repositories | 4 | 5 | 20 | 🔴 | Hinweis auf Login-Seite (Risikoakzeptanz), Pflicht-Passwortwechsel (REQ-4028), Ablehnung bekannter Defaults, Rate-Limit 10/min/IP. **Risikoakzeptanz durch Projektinhaber (Georg Hartel, 2026-11-03). Hinweis zeigt Standardpasswort auf Login-Seite. Score bleibt 20 (Risiko nicht beseitigt, nur gemildert).** |

## Kategorie: Betrieb

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| RISK-B-001 | Keine CI/CD Pipeline – manuelle Releases fehleranfällig | 4 | 4 | 16 | 🔴 | GitHub Actions Pipeline (Tests + Lint + Build) |
| RISK-B-002 | Kein Installationspaket für Nicht-Techniker (GREAT.exe fehlt) | 4 | 4 | 16 | 🔴 | PyInstaller build-exe.bat + GREAT.spec implementiert (REQ-5001, 2026-10-05); Smoke-Test im Build-Skript; finale QA-Pruefung ausstehend |
| RISK-B-003 | Start.bat ohne Fehlerbehandlung | 2 | 2 | 4 | 🟢 | Verbessern mit Fehler-Output |
| RISK-B-004 | Keine Logging-Infrastruktur | 3 | 3 | 9 | 🟡 | Python logging + log-Rotation einführen |
| RISK-B-005 | tanos.db ohne Backup-Strategie | 3 | 4 | 12 | 🔴 | Automatisches DB-Backup dokumentieren |

---

## Zusammenfassung Top-Risiken

| Rank | ID | Score | Beschreibung |
|---|---|---|---|
| 1 | RISK-S-001 | 20 | Keine Authentifizierung |
| 2 | RISK-S-016 | 20 | Default-Admin-Passwort (Risikoakzeptanz, gemildert) |
| 3 | RISK-T-001 | 20 | Monolithischer main.py |
| 4 | RISK-T-002 | 20 | Kein Migrations-Framework |
| 5 | RISK-F-002 | 20 | Geschäftsregeln fehlerhaft |
| 6 | RISK-Q-003 | 20 | Tests für Geschäftsregeln fehlen |
| 7 | RISK-F-003 | 16 | Grenzwertanalyse fehlt |
| 8 | RISK-B-001 | 16 | Keine CI/CD |
| 9 | RISK-B-002 | 16 | Kein Installationspaket |
| 10 | RISK-T-005 | 15 | Frontend-Technologie-Konflikt |
