# Changelog

Alle wesentlichen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

## [Unreleased]

### 🔒 Sicherheit
- **Scopes von API-Tokens gelten fuer alle Endpunkte (A-03):** Bisher nur bei `generate` geprueft. Zuordnung fuer `/api/*`: Modell-Datei lesen/schreiben `models:read`/`models:write`, Testfall-Exporte `export`, Generierung und Lueckenschluss `generate`, sonst lesend `projects:read` und aendernd `projects:write`. Fehlender Scope: 403 mit `X-Error-Code: insufficient_scope`.
- **Rate-Limit nicht mehr ueber den Token-Praefix missbrauchbar (A-07):** Gezaehlt wird je Token erst nach erfolgreicher Pruefung. Fehlgeschlagene Token-Pruefungen sind je Client-IP begrenzt (20/Minute) und werden vor der aufwendigen Hash-Pruefung abgewiesen.
- **Constraints nur mit Kategorien und Werten des eigenen Projekts (K-05):** Fremde oder unbekannte IDs liefern 422 `constraint_reference_invalid`; `/constraints/validate` meldet sie als Fehler.

### 🐛 Bugfixes
- **Angemeldet bleiben nach eigenem Passwortwechsel (B-06):** Die aendernde Sitzung erhaelt neue Tokens; alle anderen Sitzungen des Nutzers enden weiterhin.
- **Kein Abmelden mehr beim Neuladen nach 15 Minuten (B-43):** Auch Aufrufe unter `/auth` (z. B. `/auth/me` beim Seitenstart) erneuern ein abgelaufenes Access-Token per Refresh. Scheitert der Refresh, wird die Anfrage nicht endlos wiederholt.
- **Verstaendliche Fehlermeldungen beim Passwortwechsel (N-01):** Statt "Request failed with status code 400" erscheinen uebersetzte Meldungen, auch fuer zu verbreitete Passwoerter und zu wenig verschiedene Zeichen. Die Login-Seite zeigt ebenfalls die Meldung des Servers.
- **Gherkin-Export gueltig (A-05):** Deutsches Schluesselwort `Funktionalität`; Schritte verwenden Platzhalter (`<Spalte>`) statt der Werte des ersten Testfalls; Tabellenzellen werden nach Gherkin-Regeln maskiert und nicht mehr in Anfuehrungszeichen gesetzt; kein Fehler 500 bei Generierungen ohne Testfaelle.
- **Robot-Export lauffaehig (A-06):** `Test Template` in `*** Settings ***`, eingerueckte `[Arguments]`; Werte werden exakt uebergeben (Variablen, `#`, `=`, mehrfache Leerzeichen, leere Werte als `${EMPTY}`). Die immer fehlschlagende Pruefung gegen "Expected Result" entfaellt.
- **Exporte folgen der Generierung (A-10):** Spalten sind die Kategorien der jeweiligen Generierung; geloeschte Kategorien bleiben erhalten, spaeter angelegte erscheinen nicht.
- **Testmanagement-CSV importierbar (A-11):** Erste Zeile ist der Spaltenkopf (keine Kommentarzeile); Titel/Summary beginnen mit der TC-ID. Azure DevOps: Spalte `ID` leer (neue Testfaelle statt Ueberschreiben vorhandener Work Items), Komma als Trennzeichen, State `Design`.
- **Namen und Reihenfolge (A-12):** Eindeutige Bezeichner bei kollidierenden Kategorienamen (z. B. `a b`/`a-b`), Umlaute bleiben in Gherkin und Robot erhalten, Testfaelle in natuerlicher Reihenfolge (TC_1, TC_2, …, TC_10).
- **Grenzwertanalyse ohne Serverfehler (C-04):** Monatsenden ueber Dezember, Kalendergrenzen 0001/9999, gemischte Zeitzonen, `extras` als Liste, `NaN`, sehr grosse Zahlen und Datumsangaben an `/bva/ranges` liefern Werte bzw. 400 mit Meldung statt 500.
- **Mehrere Bereiche gemeinsam (C-05):** Datum, Uhrzeit, Datum+Uhrzeit und Stringlaenge werden wie Zahlen ueber alle Bereiche berechnet: gueltig/ungueltig je Bereich, keine doppelten Werte mit widerspruechlicher Einstufung, Ueberschneidung und Min > Max werden gemeldet (auch im Dialog). Uhrzeiten mit Min > Max gelten als Bereich ueber Mitternacht.
- **Zusatzwerte nur im Bereich (C-07):** 29.02. im Nicht-Schaltjahr und ungueltiges Datum (31. eines 30-Tage-Monats) entstehen nur, wenn der Monat im Bereich liegt; die Jahreszahl bleibt unveraendert.
- **Datum, Uhrzeit, Zeitzone (C-08 bis C-10):** Monatsenden inkl. Startmonat; im Format TT.MM.JJJJ chronologisch sortiert; nur gueltige Uhrzeiten (00:00 minus 1 Minute = 23:59, kein `-00:01`), `24:00:00` beim Format mit Sekunden, Sekundenschritte immer mit Sekunden. Neue Option Zeitzone (ISO-8601-Offset) fuer Datum+Uhrzeit.
- **Stringlaenge (C-11, C-12):** Keine negative Laenge bei Min 0; Werte durchlaufen den Zeichenvorrat (z. B. Umlaute bei „inkl. Umlaute“), Unicode enthaelt Emoji und Zeichen ausserhalb der BMP; fuehrende und abschliessende Leerzeichen gehen nicht mehr verloren.
- **Nicht angewendete Constraints werden gemeldet (R-05):** Ungueltige oder nicht auswertbare Constraints erscheinen als Hinweis in der Generierung (API `warnings` und Oberflaeche), statt nur im Log.
- **Abdeckung korrekt und schnell (K-04, K-06, K-08):** "Moeglich" heisst jetzt: es gibt einen vollstaendigen gueltigen Testfall mit diesem Tupel (auch ueber verkettete Constraints und Abhaengigkeitsregeln unmoegliche Tupel zaehlen nicht mit). 3-wise-Groessenpruefung ueber die echte Tripelanzahl; `/coverage/missing?t=3` liefert bei Ueberschreitung 422 statt 500. Ergebnis wird in der Generierung gespeichert und bei jeder Aenderung an Kategorien, Werten, Regeln oder Constraints neu berechnet (auch nach Neustart verfuegbar). Laden und Zaehlen ohne N+1-Abfragen.
- **Warnungen zu unerreichbaren Werten (K-06, K-07, REQ-6001 AK-8):** Beim Speichern eines Constraints wird jeder Wert genannt, der in keinem gueltigen Testfall mehr vorkommen kann. Die Generierung meldet "in keinem Testfall erreichbar" nur noch fuer tatsaechlich unerreichbare Werte.
- **Risikobasierte Strategie regelbewusst (K-07):** `risk_based` erzeugt nur regelkonforme Testfaelle und deckt jeden erreichbaren Wert ab, statt regelwidrige Faelle nachtraeglich zu verwerfen.
- **Seeds und Lueckenschluss ergaenzen gezielt (K-10 bis K-12):** Nur noch fehlende, erreichbare Tupel der gewaehlten Staerke werden ergaenzt (keine volle Neugenerierung); `t_wise` nutzt `t_strength`; unbekannte Strategien liefern 422. Der Bericht nennt die durch Regeln unmoeglichen Tupel. `limit` kuerzt keine Seeds (Hinweis statt stiller Kuerzung); Seeds mit unbekannten Werten werden nicht uebernommen.
- **Oberflaeche eingebunden (K-09):** Generierungsuebersicht mit Spalte "2-wise %", Abdeckungsmatrix mit Heatmap und Aktion "Luecken schliessen"; Projektansicht mit Reiter "Seeds" (Seed-Saetze anlegen, bearbeiten, CSV-Import) und Auswahl eines Seed-Satzes bei der Generierung.
- **Geloeschte Werte wirken nicht mehr still in Constraints weiter (K-02, REQ-6001 AK-10):** Loeschen einer referenzierten Kategorie bzw. eines referenzierten Werts liefert zuerst 409 `constraint_reference` mit den betroffenen Constraints; die Oberflaeche fragt nach. Nach Bestaetigung (`force=true`) werden die Constraints als ungueltig markiert, in der Liste angezeigt und bei der Generierung nicht angewendet, bis sie bearbeitet werden.

### ⚠️ Hinweise fuer API-Nutzer
- Tokens brauchen jetzt fuer jeden Endpunkt den passenden Scope, z. B. `projects:read` zusaetzlich zu `export`, um Projekte und Generierungen aufzulisten.
- `DELETE /api/categories/{id}` und `DELETE /api/values/{id}` koennen 409 `constraint_reference` liefern; mit `?force=true` wird trotzdem geloescht.
- Exporte: Azure-DevOps-CSV nutzt Komma statt Semikolon; Xray-, TestRail- und Azure-CSV enthalten keine `#`-Kopfzeile mehr; Gherkin-, Robot- und pytest-Dateien sind anders aufgebaut (siehe oben).
- Grenzwertanalyse mit mehreren Bereichen (`/bva/ranges`, `/bva/extended`): Min > Max liefert 400 statt stiller Vertauschung. Die einfache Zahlen-BVA (`/bva`, REQ-0306) vertauscht weiterhin automatisch. Zahlen sind auf Betrag < 10^15 und 10 Nachkommastellen begrenzt.
- 429-Antworten des Token-Rate-Limits haben das Format `{"detail": {"code": "rate_limit_exceeded", "detail": "..."}}`.

---

## [1.11.2] – 2026-11-25 – Bugfixes: Sicherheit, Stabilitaet, Pairwise, Grenzwertanalyse

### 🔒 Sicherheit
- **Code-Injection ueber Exporte verhindert (A-02):** Projekt-, Kategorie- und Seed-Namen mit Zeilenumbruechen oder Steuerzeichen werden abgelehnt (422). Alle Exporter (pytest, Robot, Gherkin, Markdown, CSV) schreiben Namen einzeilig und maskieren Werte; generierter Testcode kann keinen fremden Code mehr enthalten.
- **Server-Blockade verhindert (B-03, K-01, K-03, N-03):** Zeitbudget fuer alle Generierungsstrategien und die Constraint-Pruefung. Zu grosse Aufgaben liefern 422 `too_many_combinations` bzw. `generation_timeout`, statt CPU und Speicher zu blockieren. Obergrenze per `GREAT_MAX_TUPLES` (Default 1.000.000).

### 🐛 Bugfixes
- **Pairwise (B-02, K-03):** Neuer IPOG-Algorithmus erzeugt minimale Suiten mit 100 % Paarabdeckung (z. B. 3×3 → 9, 10×10 → 169, 20×10 → 223 statt 15.571 Testfaellen).
- **Rolle api_user nutzbar (A-01):** Admins legen API-Tokens fuer technische Nutzer an (`user_id`); fuer `api_user` gilt keine Passwortwechsel-Pflicht. Ungueltige Scopes liefern 422 statt 500.
- **Grenzwertanalyse Datum/Uhrzeit/Stringlaenge (C-02, C-06):** Dialog prueft passend zum Datentyp, bietet Format, Schrittweite, Zeichenvorrat und Zusatzwerte; Werte werden mit Typ `date`/`time` gespeichert.
- **Vertragsfehler Frontend/Backend (R-02, C-01, C-03, A-04):** Zahlen-BVA im Dialog, Stringlaengen-Ergebnis, API-Token-Pfade und Ablaufdatum.
- **Generierungshistorie (R-03):** `GET /api/projects/{id}/generations` liefert wieder eine Liste (wie dokumentiert).
- **Abdeckungsanzeige (R-06):** Texte uebersetzt (de/en).

### 🧪 Tests & Doku
- Backend- und Frontend-Testsuite vollstaendig gruen (CSV-Golden-Files mit CRLF, Test-DB-Isolation repariert); neue Tests fuer alle Fixes.
- REQ-4028 AK-11 (api_user-Ausnahme), Handbuch zur Rolle api_user.

### ⚠️ Hinweise fuer API-Nutzer
- `GET /api/projects/{id}/generations` liefert ein JSON-Array (in 1.11.1 kurzzeitig `{"generations": [...]}`).
- Neue 422-Codes: `too_many_combinations`, `generation_timeout`.
- Namen mit Zeilenumbruch/Tab/Steuerzeichen werden abgelehnt (Werte duerfen sie weiterhin enthalten).

---

## [1.11.1] – 2026-11-24 – Bugfixes Klassifikationsbaum und Migration

### 🐛 Bugfixes
- **REQ-6006:** Testfallmatrix im Klassifikationsbaum – Generierungsauswahl, Laden der Testfaelle, Fehlerbehandlung.
- **REQ-6009/6008/6016:** DB-Migration fuer `seed_set_id`, `coverage_meta`, `origin`, `parent_value_id`; Escaping der Tabelle `values` in SQLite.

---

## [1.11.0] – 2026-11-23 – Methodik: Constraints, Coverage, Seeds, BVA, Klassifikationsbaum, Hierarchie

### ✨ Neue Features
- **REQ-6001**: **Logische Constraints** – ConstraintBuilder im Frontend, API CRUD+Validate, Live-Validierung, Edit-Fix fuer bestehende Constraints
- **REQ-6008**: **Abdeckungsanzeige als Heatmap** – coverage.py erweitert, 3 API-Endpoints, CoverageHeatmap-Komponente, Okabe-Ito Farbschema, hierarchie-aware
- **REQ-6009**: **Pflicht-Testfaelle (Seeds) + Lueckenschluss** – Backend: seed-Logik in combinatorics/, API-Endpunkte, 92 Tests; Frontend: Seed-Dialog, Lueckenschluss-UI, 62 Tests; Gesamt 154 Tests
- **REQ-6007**: **Grenzwertanalyse fuer Datum, Uhrzeit, Stringlaenge** – BVA erweitert: 2/3/4-Punkt-Methode fuer alle Typen, symbolische Werte (>500 Zeichen), Unicode-Codepoints, API mit type-Feld, 98 Tests
- **REQ-6006**: **Klassifikationsbaum-Ansicht** – SVG-Baum (Wurzel → Kategorien → Werte), Testfallmatrix darunter, Zoom (Strg+Mausrad/+/-/Einpassen), Bearbeiten (Doppelklick/F2, Entf, +Kategorie), Export SVG/PNG, 18 Tests
- **REQ-6016**: **Hierarchische Klassen (Verfeinerung)** – HierarchyDescriptor, max 3 Ebenen, enforce_hierarchy() Post-Processing, DependencyRule + ForbiddenRule Constraints, RefineDialog im Klassifikationsbaum, 15 Tests

### 🔧 Technical
- **Backend**: Neue Module `hierarchy.py`, `hierarchy_constraints.py`, `symbolic_values.py`; coverage.py erweitert; boundary_value.py erweitert (date/time/datetime/strlen)
- **Frontend**: Neue Komponenten `ClassificationTreeView`, `ClassificationTreeMatrix`, `ClassificationTreeTab`, `CoverageHeatmap`, `RefineDialog`; bva-extended.ts; i18n ~120 neue Keys
- **API**: Neue Endpunkte `/categories/{cid}/refine`, `/categories/{cid}/hierarchy`, `/categories/{cid}/bva/extended`, Coverage-Endpoints
- **Tests**: 308+ neue Tests (154 REQ-6009, 98 REQ-6007, 18 REQ-6006, 15 REQ-6016, 76 REQ-6008, 35 REQ-6001)

### 📊 Test-Coverage
- Backend: 489+ Tests (vorher ~340)
- Frontend: 729 Tests (vorher ~527)
- Build: TypeScript + Vite OK

---

## [1.10.0] – 2026-11-18 – i18n, Exporte, API-Tokens, Testmodell als Datei

### ✨ Neue Features
- **REQ-6005:** Oberflaeche auf Deutsch und Englisch, Sprachumschalter in der Navigation und auf der Login-Seite.
- **REQ-6011:** Exporte fuer Testmanagement und Automatisierung: Gherkin (de/en), pytest, Robot Framework, JSON, Xray, TestRail, Azure DevOps, Markdown.
- **REQ-6012:** API-Tokens (Bearer, Scopes, argon2id) fuer CI und Testwerkzeuge; Token-Verwaltung in den Einstellungen.
- **REQ-6013:** Testmodell als Datei (YAML/JSON) exportieren und importieren, mit Aenderungsvorschau.

---

## [1.9.0] – 2026-11-17 – Sicherheit, Validierung & Code-Archivierung

### ✨ Neue Features
- **REQ-3034**: Generierte Testfälle werden absteigend nach kumuliertem Risiko-Score sortiert (Summe der `risk_weight` aller zugewiesenen Werte je Testfall). Testfälle mit Fehlerwerten behalten weiterhin Vorrang (REQ-3018/BUG-5) und werden unabhängig von ihrem Risiko-Score ans Ende der Liste sortiert.
- **REQ-3063**: **Fehlerwert-Kennzeichnung in allen Export-Formaten** (CSV, JSON, Excel). Neue Spalte "Fehlerwert" (JA/NEIN) bzw. `has_error_value` (true/false) markiert Testfälle, die mindestens einen Wert mit `allowed=False` enthalten.
- **REQ-4018**: Neue Einstellung "Maximale Anzahl Testfälle" (Default 1000) begrenzt die Anzahl generierter Testfälle pro Kombination, wenn kein expliziter `limit`-Wert im Request angegeben ist. Konfigurierbar über `GREAT_MAX_TESTCASES` (Backend) sowie Einstellungen-Seite (Frontend, lokal gespeichert).
- **REQ-4027**: Erststart-Hinweis auf Login-Seite: Bei Erstanmeldung zeigt die Login-Seite das Standardpasswort des Default-Admin-Accounts.
- **REQ-4028**: Pflicht-Passwortwechsel nach Erstanmeldung fuer Default-Admin. Selbst-Passwortwechsel fuer alle Benutzerrollen (Admin/Editor/Viewer).

### 🐛 Bugfixes
- **B-01**: Projektliste zeigt allen Rollen alle Projekte
- **B-02**: `all` bei zu vielen Kombinationen → 422 `too_many_combinations`
- **B-03**: `limit` max. 100.000; `t_strength` < 1 → 422
- **B-04**: Doppelte Namen → 409, leere/zu lange Namen → 422
- **B-05**: CSV/XLSX-Export schützt Formeln mit Apostroph
- **B-06**: Sitzungen enden bei Passwortwechsel, Deaktivierung, Rollenwechsel
- **B-07**: Passwort ändern nur noch für Admins
- **B-08**: Login-Rate-Limit zählt nur Fehlversuche
- **B-09**: Backup-Passwort nicht mehr per URL; neues `POST /api/backup`; Backup-Format 2.0
- **B-13**: Ungültige IDs → 422, fehlende Eltern-Ressourcen → 404
- **B-15**: `risk_weight` 1–10 auch beim Anlegen
- **B-16**: `risk_weight` 1–10 auch beim Anlegen
- **B-17**: Neues Zeitlimit für Generierung
- **B-18**: Generierungshistorie unveränderlich (category_name-Schnappschuss)
- **B-19..B-26**: Regeln validieren (Wert-Existenz, gleiche Kategorie, Duplikate, unreachable values)
- **B-27..B-50**: Diverse Backend- und Frontend-Bugfixes

### ⚠️ Verhaltensänderungen (wichtig für API-Nutzer)
- `GenerateResponse` mit neuen Feldern: `total_possible`, `truncated`, `rules_applied`, `rule_count`, `warnings`
- `DELETE /api/projects/{pid}` mit Generierungen nur mit `?force=true`
- `/whoami` und `/auth/*-only` Debug-Endpunkte entfernt
- BugMagnet-Import: Dataclasses-Variante deprecated, Datanodes kanonisch
- Frontend: Alle API-Calls über einheitliche axios-Schicht (Token-Refresh überall)

### 🔒 Sicherheit
- Token-Versioning: Sitzungen enden bei Passwortwechsel, Deaktivierung, Rollenwechsel
- Striktere Passwortregeln (Min. 12 Zeichen, Variety-Check, Common-Passwords)
- Admin-angelegte Nutzer müssen Passwort beim ersten Login ändern
- Refresh-Token: `is_active` + `token_version` geprüft
- Login-Rate-Limiter: IP + username, nur Fehlversuche

### 📦 Entfernt / Archiviert
- Desktop-Altcode "TaNoS v5.4" (PySide6) und GeTeCaDe-Backend archiviert
- Debug-Auth-Endpunkte (`/auth/admin-only`, `/auth/editor-or-admin`, etc.) entfernt
- HTMX/Jinja2-Templates archiviert
- Port-Eingabe in Einstellungen entfernt (Konfiguration via `.env`)
- Totcode: DataNodePicker, ResultCellEditor, handlers.ts, dataclassApi, bulkDelete, clearError

### ⚙️ Neue Konfigurationsvariablen
- `JWT_SECRET_KEY` / `JWT_REFRESH_SECRET_KEY` (B-25, in Production zwingend)
- `GREAT_COOKIE_SECURE` (B-26, `true` bei HTTPS, `false` für lokale Entwicklung)
- `GREAT_MAX_TESTCASES` (REQ-4018, Default 1000)

---

## ✅ Release v1.8.0 – In-App-Hilfe & Bugfixes (2026-11-12)

### ✨ Neue Features
- **In-App-Hilfe (`/help`)**: Markdown-Handbuch mit 14 Kapiteln, 18 Screenshots, Sidebar-Navigation
- **TopNav "?"-Button**: Hover "Hilfe (F1)", Klick öffnet Hilfe
- **F1-Shortcut**: Global in der App — öffnet sofort die Hilfe
- **INFO-Section**: Lizenz (MIT), Haftungsausschluss, KI-Hinweis, GitHub-Projekt-Link
- **Lazy-Loading**: HelpPage wird nur bei Bedarf geladen (Chunk-Size 620 → 410 kB)

### 🐛 Bugfixes
- **Theme-Fix (REQ-3045 + REQ-3062)**: "Normal" und "System (OS)" klar getrennt: "Normal" = HSV-Farben (dunkelblau/weiss/rot) als `:root` Default, "System (OS)" = `.theme-light` (hell) oder `.theme-dark` (dunkel) je nach OS-Einstellung
- **Risikoabdeckung Bugfix (REQ-3051)**: Berechnung zeigt korrekte Werte ≤ 100% bei "All Combinations" — Ergebnis-Kategorien werden vom Maximum ausgeschlossen
- **Name korrigiert**: "Georg" → "Georgs" (README, Handbuch)
- **Screenshots sichtbar**: Bilder als ES-Module importiert, im Build korrekt resolved
- **Handbuch Kapitel 15**: API-Einbindung fuer Entwickler (alle REST-Endpoints, Auth, Beispiel-Workflow)

### 🔧 Technical
- **Dependencies**: `react-markdown`, `remark-gfm` hinzugefuegt
- **Vite**: Screenshots von `public/` nach `src/docs/screenshots/` verschoben (korrektes URL-Resolving)
- **TypeScript**: `*.png` Import-Deklarationen in `vite-env.d.ts`

### 🔧 Release v1.6.0 – Entscheidungstabelle & Multi-User
- **Entscheidungstabelle (REQ-5000-5021)**: Vollstaendige Ursache-Wirkung-Entscheidungstabelle mit Kategorie-Typen (Ursache/Wirkung/Ergebnis), Regelgenerierung, Constraints (E/O/I/R/M), Collapsing, Validierung (Checksum, Widersprueche, Luecken), Priorisierung mit Override-Modus
- **Authentifizierung & Multi-User (REQ-4006-4020)**: JWT-Auth, Login-Seite, User-Management, Rollen (Admin/Editor/Viewer), Passwort-Policy, Rate Limiting, Projekt-Freigabe
- **Frontend**: DecisionTable, CauseEffectGraph, ProtectedRoute, StaleDataWarning, ErrorBoundary, Theme-System (Dark Mode, Steampunk, Rainbow, Heavy Metal)
- **Backend**: Neue API-Endpunkte fuer Decision Table, Auth, Sharing; Models-Package; Middleware; Migrationen

### Fixed
- **Bugfix B1 – Testfalltabelle nach "Neu generieren" bzw. "Vorherige Generierung laden" nicht sichtbar:** Der API-Client (`frontend/src/api/client.ts`) sendet die Anmelde-Cookies jetzt mit (`withCredentials: true`). Seit der Umstellung auf JWT in httpOnly-Cookies (REQ-4001) wurden Generierungs-Anfragen ohne Cookies mit 401/403 abgewiesen, dadurch blieb die Tabelle leer. Bezug: REQ-4001, REQ-2001.
- **Bugfix B2 – Schwarzer Bildschirm mit "Minified React error #300"** bei "Neu generieren" (alle Strategien) und bei "Vorherige Generierung laden": In `frontend/src/components/TestCasePanel.tsx` wurde ein Zustands-Hook bedingt im JSX aufgerufen und verletzte damit die React-Hook-Regeln. Der Wert wird jetzt einmal am Anfang der Komponente gelesen. Regressionstests: Block "BUGFIX React #300 (Rules of Hooks)" in `frontend/src/components/__tests__/TestCasePanel.test.tsx`. Bezug: REQ-3052, REQ-5006.
- **Bugfix B3 – Ein Anzeigefehler beendet die gesamte Anwendung:** Neue Fehlergrenze `frontend/src/components/ErrorBoundary.tsx`, eingebunden in `frontend/src/App.tsx`. Bei Render-Fehlern erscheint jetzt eine Fehlermeldung mit Schaltflaeche zum Neuladen statt eines schwarzen Bildschirms. Bugfix-Scope ohne eigene REQ-ID.

## [1.5.2] - 2026-09-04

### 🔧 Release-Update
- Versionsnummer in Backend- und Frontend-Metadaten auf 1.5.2 synchronisiert.
- Changelog für das aktuelle Release ergänzt.

## [1.5.1] - 2026-09-01

### 🐛 Bugfixes – Sprintabschluss
- **REQ-3041 / REQ-3042**: Dezimaltrennzeichen mit Punkt oder Komma werden in der Grenzwertanalyse jetzt konsistent akzeptiert (`10.01`, `10,01`).
- BVA-Validierung erkennt numerische Eingaben korrekt und vermeidet unnötige Fehlermeldungen beim Dateneingang.
- Sprint-Release abgeschlossen und für den nächsten Sprint vorbereitet.

## [1.5.0] - 2026-08-19

### ✨ Neue Features – Sprint 9

#### REQ-4012: Datenklassen-Überarbeitung + BugMagnet-Import
- System-Datenklassen umbenannt in "Beispiele"
- Settings-Seite: Neuer "Datenklassen"-Bereich mit Import-Button
- Live-Import von BugMagnet GitHub (https://github.com/gojko/bugmagnet)
- Nach Import: Bezeichnung wechselt zu "Bug Magnet Import"
- Endpoints: `POST /api/dataclasses/bugmagnet-import`, `GET /api/dataclasses/bugmagnet-status`

#### REQ-4013: Eigene Datenklassen Import/Export JSON
- Export: eigene Datenklassen als JSON herunterladen
- Import: JSON-Datei hochladen (Merge-Strategie, Legacy-Format unterstützt)
- UI-Kasten oben in "Meine Datenklassen"
- Endpoints: `GET /api/dataclasses/export-user`, `POST /api/dataclasses/import-user`

#### REQ-4014: Kategorien & Werte – Tabellarische Ansicht + Drag & Drop
- Spalten-Header in Werte-Tabelle (Reihenfolge, Wert, Aktionen)
- Werte per Drag & Drop umsortierbar (Reihenfolge wird gespeichert)
- BVA-Symbol größer mit "BVA"-Label
- Default-Markierung als ★ (statt ?)
- Endpoint: `PUT /api/dataclasses/{id}/values/reorder`

#### REQ-4015: BVA-Visualisierung überarbeitet + Fehlerwert-Bug-Fix
- Symbolischer Zahlenstrahl: gleichmäßige Abstände (Lesbarkeit > Maßstab)
- Multi-Range: jede Äquivalenzklasse farbig unterschieden, Lücken ausgegraut
- `BVARange.is_valid`: erlaubte/unerlaubte Äquivalenzklassen explizit markierbar
- Fehlerwert-Bug behoben: `is_error` korrekt in Kategorien & Werte angezeigt

#### REQ-4016: Neuer Typ "Ergebnis" für Kategorien (ISTQB Expected Result)
- Kategorien als "Ergebnis-Kategorie" markierbar (`is_result` Flag)
- Ergebnis-Kategorien werden **nicht** automatisch in Kombinatorik einbezogen
- Nur durch Regeln oder manuelle Eingabe befüllbar (ISTQB-konform)
- Testfall-Tabelle: Ergebnis-Spalte immer sichtbar, leere Felder farblich markiert
- `ResultCellEditor`: Dropdown + Freitext nach Generierung editierbar

### 🔧 Qualität
- 340 Backend-Tests (+7 seit v1.4.0)
- 5 PRs (#36–#40) sauber gemergt

---

## [1.1.0] - 2026-07-02 – Sprint 5: UX, Risikoabdeckung, BVA-ISTQB

### Neue Features
- **REQ-3045–3049**: Theme-System (Normal, Dark, Steampunk, Rainbow, Heavy Metal)
- **REQ-3050**: Risikoabdeckung pro Testfall (Summe `risk_weight`)
- **REQ-3051**: Risikoabdeckung-Prozentsatz pro Generierung (farbiges Badge)
- **REQ-3052**: Tabellenansicht Testfälle – sortierbare Spalten, Sticky Header, CSV-Export
- **REQ-3053**: Undo/Redo (Strg+Z / Strg+Y, max. 50 Schritte)
- **REQ-3054**: Tastaturnavigation (Pfeiltasten, Enter, Delete, F2, Escape, ARIA)
- **REQ-3062**: Dark-Mode System-Sync (OS `prefers-color-scheme`)
- **REQ-3063**: Fehlerwert-Testfälle rot markiert in Tabelle
- **REQ-3064**: Multi-Range BVA (mehrere Äquivalenzklassen, erlaubt/nicht erlaubt)

### Bugfixes
- **BUG-2**: Start.bat Timeout erhöht – Backend startet vor Frontend-Proxy
- **BUG-4**: BVA ISTQB-konform korrigiert (2/3/4-Wert-Methode nach ISTQB-Standard)

### Chores
- `.gitignore` aktualisiert – `test_bugmagnet.py` lokal erhalten

---

## [1.0.0] – 2026-07-01 – Initial Public Release

**Erstes öffentliches Release nach kompletter Neuentwicklung.**

### Grundlegende Änderungen
- Vollständige Neuentwicklung als Web-App (vormals Desktop-Lösung „Tanos")
- Umbenennung: Tanos → G.R.E.A.T. (Georg Radikal Einfacher Automatisierter TestcaseDesigner)
- Neue Architektur: Python/FastAPI Backend + React/TypeScript Frontend
- Lizenzwechsel auf AGPL-3.0 mit Dual-Licensing (kommerzielle Nutzung genehmigungspflichtig – siehe NOTICE.md)

### Backend (Python/FastAPI/SQLite)
- Projekt-Management mit Kategorien und typisierten Werten
- Wert-Eigenschaften: Risiko, Datentyp, Fehlerwert, Default-Markierung
- Regellogik: Verboten (Paar), Abhängig (Wenn-Dann), Kombinieren (Fan-out)
- Widerspruchs-Erkennung bei Regeln
- Kombinatorik-Strategien: Each-Choice, Pairwise, Lineare Expansion, Manuell
- Grenzwertanalyse (BVA) als Backend-Endpoint
- System-Datenklassen (typisierte Äquivalenzklassen)
- User-Datenklassen (custom, mit Typ-Validierung)
- REST-API mit OpenAPI-Dokumentation

### Frontend (React/TypeScript/Vite)
- Office-ähnliche Bedienung mit Zwei-Pane-Layout
- Kategorie-Baumansicht mit Inline-Bearbeitung
- Regeleditor mit Live-Konflikt-Warnung
- Testfall-Generierung mit optionaler Regel-Anwendung
- Generierungs-Historie pro Projekt (mit editierbaren Namen)
- Datenklassen-Verwaltung (System + User)
- Export: CSV, JSON, Excel
- Einheitliche Top-Navigation

### Governance
- Requirements-Traceability (REQ-IDs)
- Test-Driven Development mit 179+ Tests
- Architecture Decision Records (ADRs)

### Bekannte Einschränkungen
- Single-User-App (kein Multi-User)
- Keine Authentifizierung (lokaler Betrieb)
- Nur SQLite (kein PostgreSQL)

### Roadmap
Siehe [RELEASE_NOTES.md](RELEASE_NOTES.md) für geplante Features (Phase 3 Sprint 4+ und Phase 4).

---

# Changelog � G.R.E.A.T.

Alle wichtigen �nderungen werden in dieser Datei dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [Phase 1 Sprint 3] � 2026-06-23

### Added
- E2E-Tests mit Playwright/Chromium (tests/e2e/)
- Start.sh � Startskript f�r Linux / Raspberry Pi (REQ-0010)
- INSTALLATION.md � Schritt-f�r-Schritt Installation (Windows + RPi)
- TESTING_GUIDE.md � TDD-Workflow, Coverage, Teststruktur
- requirements-rpi.txt � Abh�ngigkeiten ohne PySide6 f�r RPi
- pytest-playwright zu requirements.txt erg�nzt

### Fixed
- boundary_value.py: Ganzzahlige Floats (18.0) als Integer formatiert

---

## [Phase 1 Sprint 2] � 2026-06-23

### Added
- Grenzwertanalyse / BVA (REQ-0306): src/combinatorics/boundary_value.py
  - API-Endpunkt: POST /categories/{cid}/bva
- Risikogewichtete Generierung (REQ-0805): src/combinatorics/risk_based.py
- JSON Export (REQ-1001): GET /generations/{id}/export/json
- Excel Export (REQ-1002): GET /generations/{id}/export/xlsx
- python-multipart in requirements.txt

### Fixed
- test_ui_crud.py: Projektname durch UUID eindeutig
- test_backend_mvp.py: CSV-Assertion korrigiert
- test_export_status.py: sep=-Zeile �bersprungen

---

## [Phase 1 Sprint 1] � 2026-06-10 / 2026-06-23

### Added
- Router-Refactoring DEBT-001: main.py von ~1400 auf 80 Zeilen
  - services.py, ui_helpers.py, templates_config.py, routers/ (5 Module)
- Lineare Expansion (REQ-0803): src/combinatorics/linear_expansion.py
- RuleEngine (REQ-0700/0701/0702): src/core/rules/rule_engine.py
- Alembic-Migrationen: src/db/migrations/
- pytest-cov + .coveragerc

---

## [Phase 0] � 2026-06-10

### Added
- Bestandsanalyse der Codebasis
- requirements_v1.1.md (~60 REQs)
- project-assessment.md, risk-log.md, decision-log.md (ADRs 001-006)
- MIT-Lizenz (c) Georg Haupt
- Technologieentscheidung Python/FastAPI (ADR-001)
- Frontend-Entscheidung React/TypeScript (ADR-003)

---

## [5.8.1] � 2025-10-07 (Legacy/MVP)

### Added
- Vollst�ndiges Datenmodell SQLite + SQLAlchemy
- HTMX-Weboberfl�che (Projektverwaltung, Kategorien, Werte, Regeln)
- Pairwise/Orthogonal Generator
- CSV Export/Import
- FastAPI mit Swagger-Dokumentation
