# G.R.E.A.T. Release Notes - Phase 2 Abschluss / Phase 3 Start

**Datum:** 2026-11-09
**Branch:** `fix/export-routing-e2e-test` → `main`

---

## Was ist neu?

### Entscheidungstabelle (Decision Table) - Vollstaendig implementiert

**REQ-5000/5002/5003/5004/5005:** Vollstaendige Ursache-Wirkung-Entscheidungstabelle

- **Kategorie-Typen:** Kategorien koennen als "Normal", "Ergebnis", "Ursache" oder "Wirkung" angelegt werden
- **Visuelle Kennzeichnung:** Badges im Kategorienbaum (U=Ursache, W=Wirkung, E=Ergebnis)
- **Typ-Aenderung:** Kontextmenue zum Nachtraeglichen Aendern des Kategorie-Typs
- **Regelgenerierung:** Button "Regeln generieren" in neuem "Entscheidungstabelle"-Tab
- **Constraint-Dialog:** Regeln/Constraints fuer die Entscheidungstabelle definieren (E/O/I/R/M)
- **Optimierung:** Collapsing (Zusammenfassen redundanter Regeln) und Validierung (Checksum, Widersprueche, Luecken)
- **Priorisierung:** REQ-5021 - Wirkungen priorisieren mit Override-Modus
- **Text/Binar-Modus:** Wirkungen als Textwerte oder Binar (X/-)

### Authentifizierung & Multi-User

- **Login-Seite:** Neue Login-Oberflaeche mit First-Start-Erkennung
- **Passwort-aendern:** Geschuetzte Passwort-aenderungs-Seite
- **User-Management:** Admin kann Benutzer verwalten (REQ-4006)
- **JWT-Auth:** Token-basierte Authentifizierung mit Refresh-Tokens
- **Rollen:** Admin/Editor/Viewer-Rollen mit Zugriffskontrolle
- **Passwort-Policy:** Mindestanforderungen fuer Passwoerter
- **Rate Limiting:** Schutz vor Brute-Force-Angriffen

### Projekt-Freigabe (Sharing)

- **Projekt-Freigabe:** Projekte mit anderen Benutzern teilen (REQ-4006)
- **Mitglieder-Verwaltung:** Mitglieder hinzufügen/entfernen mit Rollen
- **Sichtbarkeit:** Nicht-Admins sehen nur ihre eigenen Projekte

### UX & Frontend

- **StaleDataWarning:** Warnung bei veralteten Daten nach parallelen Aenderungen
- **Conflict-Handling:** Echtzeit-Konflikterkennung bei Projekt-Umbenennung (Overwrite-Pfad)
- **ErrorBoundary:** Globaler Fehler-Handler fuer React-Komponenten
- **ProtectedRoute:** Geschuetzte Routen mit Auth-Prüfung
- **Theme-System:** Verbessertes Theme-System (Dark Mode, Steampunk, Rainbow, Heavy Metal)
- **Keyboard-Navigation:** Pfeiltasten-Navigation im Kategorienbaum (REQ-3054)
- **Undo/Redo:** Rueckgaengig/Wiederholen fuer Kategorie-Aenderungen (REQ-3053)

### Backend & API

- **Neue API-Endpunkte:**
  - `/api/decision-table/generate` - Entscheidungstabelle generieren
  - `/api/decision-table/categories/{project_id}` - Ursachen/Wirkungen laden
  - `/api/decision-table/constraints` - Constraint CRUD
  - `/api/decision-table/collapse` - Regeln zusammenfassen
  - `/api/decision-table/validate` - Validierung (Checksum, Widersprueche, Luecken)
  - `/api/decision-table/graph/{project_id}` - Cause-Effect-Graph-Daten
  - `/api/auth/login`, `/api/auth/logout`, `/api/auth/refresh` - Auth-Endpunkte
  - `/api/users` - User-Management
  - `/api/projects/{id}/members` - Projekt-Freigabe

- **Datenbank-Migration:** Neue Tabellen fuer Benutzer, Tokens, Projekt-Mitgliedschaften, Constraints
- **CORS-Whitelist:** Konfigurierbare CORS-Einstellungen
- **Docs-Auth-Middleware:** Geschuetzte API-Dokumentation
- **Concurrency-Lock:** Schutz vor parallelen Schreibkonflikten

### DevOps & Konfiguration

- **Start.bat / Start.sh:** Verbesserte Startskripte mit Port-Konfiguration
- **Port-Einstellung:** Konfigurierbarer Server-Port in den Einstellungen
- **Max-Testcases-Einstellung:** Konfigurierbares Limit fuer Testfall-Generierung
- **Backup-API:** Datenbank-Backup/Restore-Endpunkte

---

## Architektur-Aenderungen

- **Models-Package:** `src/app/models/` (Package) ersetzt `src/app/models.py` (archiviert)
- **Clean Architecture:** Trennung von Routers, Services, Models, Schemas
- **Middleware:** Neue Middleware-Schicht fuer Auth und CORS
- **Combinatorics:** Refactored Each-Choice und Linear-Expansion-Module

---

## Bugs behoben

- **BVA-Dialog:** Grenzwertanalyse wieder verfuegbar auf Port 8000
- **Theme-Contrast:** Farbanpassungen fuer bessere Lesbarkeit
- **Export-Routing:** Routing-Probleme beim Export behoben
- **Category-Delete:** FK-Cleanup bei Projekt-Loeschung (decision_table_constraints, project_memberships)
- **Password-Change:** Default-Admin-Passwort muss nach erstem Login geaendert werden

---

## Entfernt / Archiviert

- `src/app/models.py` → `archive/2026-11-08/models.py` (durch models/ Package ersetzt)
- Legacy DataClassDialog → durch DataNodeApplyDialog ersetzt
- "Tanos" Export-Name → zurueck zu "Great"

---

## Test-Status

- **Backend:** 812 Tests bestanden, 0 fehlgeschlagen
- **Frontend:** 66 Test-Dateien, 473 Tests bestanden, 2 skipped
- **Build:** Frontend-Build erfolgreich (tsc + vite build)

---

## Offene Punkte / Naechste Schritte

- **Phase 3:** React-First / HTMX-Abloesung geplant
- **Epic 18/20:** Weitere Entscheidungstabelle-Features (Sprint-Planning vorhanden)
- **Dokumentation:** Installationsanleitung und Benutzerdokumentation aktualisieren

---

## Dateien im Commit

**Produktionscode:** ~44 geaenderte Dateien (Backend + Frontend + Docs)
**Neue Dateien:** ~30 neue Produktionsdateien (Decision Table, Auth, Sharing, etc.)
**Exkludiert:** Testdateien, Datenbank, Agent-Konfiguration