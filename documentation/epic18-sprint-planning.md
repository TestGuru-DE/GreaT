# EPIC-18 – Multi-User Sprint-Planning (Sprint 11–13)

**Version:** 1.0
**Erstellt:** 2026-10-05
**Erstellt von:** GREAT Program Manager Agent
**Status:** 🟡 **DRAFT – Freigabe erforderlich**
**Quelle:** requirements_v1.1.md (EPIC-18), project-assessment.md, decision-log.md, risk-log.md

---

## 1. Aktueller Sprint-Stand – Bestätigung

### 1.1 Phase & Sprint-Zuordnung

| Dimension | Wert | Quelle |
|---|---|---|
| **Aktuelle Phase** | Phase 4 – Enterprise & Stabilisierung | project-assessment.md (Roadmap) |
| **Letzter abgeschlossener Sprint** | Sprint 10 (teilweise abgeschlossen) | project-assessment.md (REQ-3034, REQ-4018 DONE/TESTED) |
| **Nächster aktiver Sprint** | Sprint 11 | project-assessment.md (EPIC-18-Abschnitt) |
| **EPIC-18 Status** | 🔵 SPRINTFÄHIG VORBEREITET | project-assessment.md (2026-09-01) |
| **ADR-012 (HYBRID)** | ✅ Accepted | decision-log.md |
| **ADR-007 (DB-Strategie)** | ⏳ Bestätigung Chief Architect ausstehend | requirements_v1.1.md (EPIC-18) |

### 1.2 Sprint-10-Zustand

| REQ | Titel | Status | Anmerkung |
|---|---|---|---|
| REQ-3034 | Risikobasierte Testfall-Sortierung | ✅ DONE/TESTED | Implementiert + Tests grün |
| REQ-4018 | Max. Testfälle-Setting | ✅ DONE/TESTED | Backend + Frontend implementiert |
| REQ-4019 | GUI-Refresh nach Sichtenwechsel | ⏳ Offen | React-State-Management |
| REQ-4007+REQ-1202 | Port-Unification | ⏳ Offen | Settings-UI-Ergänzung |
| Multi-User-Analyse | Research/Klärungsauftrag | ✅ ABGESCHLOSSEN | ADR-012 als Ergebnis |

**Feststellung:** Sprint 10 ist inhaltlich zum Großteil abgeschlossen. Offene Items (REQ-4019, Port-Unification) sind nicht EPIC-18-relevant und können als technische Schulden nachgeliefert werden. Sprint 11 kann als nächster aktiver Sprint starten, **sobald die Go/No-Go-Bedingungen erfüllt sind** (siehe Abschnitt 5).

---

## 2. Sprint-Backlog & Aufwandsschätzung

### 2.1 Gesamtüberblick

| Sprint | REQs | Anzahl | Gesamt-Aufwand | Risiko-Level |
|---|---|---|---|---|
| **Sprint 11** | REQ-4001, REQ-4020 | 2 | **XL** (≈ 160 SP) | 🔴 Hoch (security-critical) |
| **Sprint 12** | REQ-4006, REQ-4021, REQ-4022 | 3 | **XL** (≈ 160 SP) | 🔴 Hoch (DB-Engine + Concurrency) |
| **Sprint 13** | REQ-4023, REQ-4024, Lasttest | 2 + 1 | **L** (≈ 100 SP) | 🟡 Mittel |
| **Gesamt EPIC-18** | 7 REQs + Lasttest | 8 | **≈ 420 SP** | 🔴 Hoch |

*Aufwandsskala: S=20 SP, M=40 SP, L=60 SP, XL=80 SP*

### 2.2 Sprint 11 – Authentifizierung & Rollen (≈ 160 SP)

| Prio | REQ-ID | Titel | Aufwand | Risiko | TDD-Pflicht |
|---|---|---|---|---|---|
| **1** | REQ-4001 | Authentifizierung (OAuth2/JWT) | **XL (80 SP)** | 🔴 | Ja |
| **2** | REQ-4020 | Rollen & Rechte Basismodell (Admin/Editor/Viewer) | **L (60 SP)** | 🟡 | Ja |
| – | – | **Sprint-11-Buffer** (Bugfixes, Refactoring) | **M (20 SP)** | – | – |

**Begründung XL für REQ-4001:**
- Auth von Null: Login-Endpoint, JWT-Erzeugung/-Validierung, Refresh-Token-Flow, Logout
- Passwort-Hashing (bcrypt/argon2) – Security-Architect-Review erforderlich
- **ALLE** bestehenden ~40+ API-Endpunkte müssen mit `Depends(get_current_user)` abgesichert werden
- Frontend: Login-Maske, Token-Storage (httpOnly-Cookie), Auto-Redirect bei 401
- Logout invalidiert Refresh-Token serverseitig
- Security-critical: Fehler hier gefährden das gesamte Multi-User-System

**Begründung L für REQ-4020:**
- Drei Rollen (Admin/Editor/Viewer) mit serverseitiger Prüfung auf allen schreibenden Endpunkten
- Rolle × Endpunkt-Matrix als Tests (mindestens 9 Kombinationen)
- UI-Anpassungen: Aktionen für Viewer deaktivieren/ausblenden
- Erste registrierte Person → automatisch Admin (Bootstrapping)

### 2.3 Sprint 12 – Multi-User-DB, Concurrency & Stale-Warning (≈ 160 SP)

| Prio | REQ-ID | Titel | Aufwand | Risiko | TDD-Pflicht |
|---|---|---|---|---|---|
| **1** | REQ-4006 | Multi-User-Datenmodell (SQLite/PostgreSQL optional) | **L (60 SP)** | 🟡 | Ja |
| **2** | REQ-4021 | Optimistic Concurrency Control (Versionsfeld, 409) | **XL (80 SP)** | 🔴 | Ja |
| **3** | REQ-4022 | Stale-Data-Warning Frontend | **M (40 SP)** | 🟢 | Ja |
| – | – | **Sprint-12-Buffer** | **M (20 SP)** | – | – |

**Begründung L für REQ-4006:**
- DATABASE_URL-Konfiguration (SQLite Default, PostgreSQL optional)
- Alembic-Migrationen gegen beide Engines testen
- Connection Pooling für PostgreSQL
- Single-User-Betrieb (SQLite) ohne Regression

**Begründung XL für REQ-4021:**
- `version`-Feld in 4 Tabellen (projects, categories, values, testcases) – Alembic-Migration
- PUT/PATCH-Requests senden `version` mit; Backend vergleicht und gibt 409 bei Diskrepanz
- 409-Response enthält aktuellen Serverstand im Body
- Backend-Tests: zwei simulierte gleichzeitige Updates → zweites liefert 409
- Alle bestehenden PATCH/PUT-Endpunkte müssen angepasst werden

**Begründung M für REQ-4022:**
- Frontend-Banner-Komponente bei 409-Response
- Zwei Aktionen: "Neu laden" / "Trotzdem überschreiben" (mit Bestätigungsdialog)
- Vitest/RTL-Tests für Banner-Zustand bei simuliertem 409

### 2.4 Sprint 13 – Projekt-Sharing, Audit-Trail & Lasttest (≈ 100 SP)

| Prio | REQ-ID | Titel | Aufwand | Risiko | TDD-Pflicht |
|---|---|---|---|---|---|
| **1** | REQ-4023 | Projekt-Sharing / Mitgliederverwaltung | **L (60 SP)** | 🟡 | Ja |
| **2** | REQ-4024 | Minimaler Audit-Trail (last_modified_by/-at) | **S (20 SP)** | 🟢 | Ja |
| **3** | – | Lasttest 10 gleichzeitige Nutzer + E2E-Konfliktszenario | **M (40 SP)** | 🟡 | Ja |
| – | – | **Sprint-13-Buffer** | **M (20 SP)** | – | – |

**Begründung L für REQ-4023:**
- Neue Tabelle `project_members` (project_id, user_id, role)
- CRUD-Endpunkte für Mitglieder-Verwaltung
- Projektliste filtert nach Mitgliedschaft
- 403 bei Zugriff ohne Mitgliedschaft

**Begründung S für REQ-4024:**
- `last_modified_by` + `last_modified_at` in 4 Tabellen – Alembic-Migration
- Automatisches Setzen bei jedem Update (DB-level oder Service-layer)
- UI: dezente Anzeige (Tooltip)
- Kein vollständiges Audit-Log (das ist REQ-4003, separat)

**Begründung M für Lasttest:**
- Lasttest-Setup: 10 simulierte gleichzeitige Nutzer (Lesen + Schreiben)
- E2E-Konfliktszenario: zwei Nutzer bearbeiten gleichzeitig → 409 + Stale-Warning
- Lasttest gegen SQLite und PostgreSQL (falls verfügbar)

---

## 3. Abhängigkeits-Diagramm

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    SPRIT 11 (Auth + Rollen)                  │
                    │                                                               │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  REQ-4001: Authentifizierung (OAuth2/JWT)               │ │
                    │  │  Aufwand: XL (80 SP) | Risiko: 🔴 | Prio: Must          │ │
                    │  │  Blockiert: REQ-4006, REQ-4020, REQ-4021, REQ-4022,     │ │
                    │  │              REQ-4023, REQ-4024                         │ │
                    │  └──────────────────────┬──────────────────────────────────┘ │
                    │                         │                                     │
                    │                         ▼                                     │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  REQ-4020: Rollen & Rechte (Admin/Editor/Viewer)        │ │
                    │  │  Aufwand: L (60 SP) | Risiko: 🟡 | Prio: Should         │ │
                    │  │  Blockiert: REQ-4023                                    │ │
                    │  │  Abhängig von: REQ-4001                                 │ │
                    │  └──────────────────────┬──────────────────────────────────┘ │
                    └─────────────────────────┼─────────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                  SPRINT 12 (DB + Concurrency)               │
                    │                                                               │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  REQ-4006: Multi-User-Datenmodell                       │ │
                    │  │  Aufwand: L (60 SP) | Risiko: 🟡 | Prio: Must          │ │
                    │  │  Blockiert: REQ-4021, REQ-4023                          │ │
                    │  │  Abhängig von: REQ-4001, ADR-007                        │ │
                    │  └──────────────────────┬──────────────────────────────────┘ │
                    │                         │                                     │
                    │                         ▼                                     │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  REQ-4021: Optimistic Concurrency Control               │ │
                    │  │  Aufwand: XL (80 SP) | Risiko: 🔴 | Prio: Must         │ │
                    │  │  Blockiert: REQ-4022                                    │ │
                    │  │  Abhängig von: REQ-4006                                 │ │
                    │  └──────────────────────┬──────────────────────────────────┘ │
                    │                         │                                     │
                    │                         ▼                                     │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  REQ-4022: Stale-Data-Warning Frontend                  │ │
                    │  │  Aufwand: M (40 SP) | Risiko: 🟢 | Prio: Must          │ │
                    │  │  Abhängig von: REQ-4021                                 │ │
                    │  └─────────────────────────────────────────────────────────┘ │
                    └─────────────────────────┬─────────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                  SPRINT 13 (Sharing + Audit + Lasttest)     │
                    │                                                               │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  REQ-4023: Projekt-Sharing / Mitgliederverwaltung       │ │
                    │  │  Aufwand: L (60 SP) | Risiko: 🟡 | Prio: Should        │ │
                    │  │  Abhängig von: REQ-4006, REQ-4020                       │ │
                    │  └─────────────────────────────────────────────────────────┘ │
                    │                                                               │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  REQ-4024: Minimaler Audit-Trail                        │ │
                    │  │  Aufwand: S (20 SP) | Risiko: 🟢 | Prio: Should        │ │
                    │  │  Abhängig von: REQ-4001, REQ-4006                       │ │
                    │  └─────────────────────────────────────────────────────────┘ │
                    │                                                               │
                    │  ┌─────────────────────────────────────────────────────────┐ │
                    │  │  Lasttest 10 Nutzer + E2E-Konfliktszenario              │ │
                    │  │  Aufwand: M (40 SP) | Risiko: 🟡 | Prio: Must          │ │
                    │  │  Abhängig von: ALLE EPIC-18 REQs                        │ │
                    │  └─────────────────────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────────────────────┘
```

### 3.1 Kritischer Pfad

```
REQ-4001 → REQ-4006 → REQ-4021 → REQ-4022
   │          │
   │          └──→ REQ-4023 (benötigt auch REQ-4020)
   │
   └──→ REQ-4020 → REQ-4023
   └──→ REQ-4024
```

**Kritischer Pfad:** REQ-4001 → REQ-4006 → REQ-4021 → REQ-4022 (4 sequenzielle Schritte über 2 Sprints)

**Parallelisierbare Pfade:**
- REQ-4020 kann parallel zu REQ-4006/4021/4022 arbeiten (hängt nur von REQ-4001 ab)
- REQ-4024 kann parallel zu REQ-4023 arbeiten (hängt nur von REQ-4001 + REQ-4006 ab)

---

## 4. Risiko-Matrix (EPIC-18)

| ID | Risiko | W | I | Score | Ampel | Maßnahme | Sprint |
|---|---|---|---|---|---|---|---|
| **RISK-S-001** | Keine Authentifizierung – alle Endpunkte öffentlich | 5 | 4 | **20** | 🔴 | REQ-4001 in Sprint 11 zuerst; Security Architect Review vor Start | Sprint 11 |
| **RISK-T-008** | Konflikte bei gleichzeitiger Bearbeitung | 3 | 4 | **12** | 🔴 | ADR-012 (HYBRID): Optimistic Concurrency + Stale-Warning; TDD | Sprint 12 |
| **RISK-T-006** | SQLite-Schreibkonflikte bei >5 gleichzeitigen Nutzern | 2 | 4 | **8** | 🟡 | PostgreSQL optional (REQ-4006), WAL-Mode, Lasttest in Sprint 13 | Sprint 12-13 |
| **RISK-S-006** | CORS/Origin-Policy zu offen vor Rollout | 3 | 3 | **9** | 🟡 | Whitelist vor Sprint-11-Release (Schulden-Item #8) | Sprint 11 |
| **RISK-F-006** | Scope-Erwartung "Echtzeit" vs. Hybrid-Vorstufe | 3 | 3 | **9** | 🟡 | Klare Kommunikation Out-of-Scope; Abnahme durch Program Manager | EPIC |

**Eskalationspflichtig (Score ≥ 10):** RISK-S-001 (20), RISK-T-008 (12)

### 4.1 Zusätzliche Risiken (durch Sprint-Planning identifiziert)

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| **RISK-T-009** (neu) | Auth-Implementierung verzögert sich → Blockiert ALLE EPIC-18 REQs | 3 | 5 | **15** | 🔴 | Sprint 11 ausschließlich Auth+Rollen; kein Parallel-Start Sprint 12; Buffer 20 SP | Sprint 11 |
| **RISK-T-010** (neu) | Versionsfeld-Migration bricht bei bestehenden Daten (SQLite) | 2 | 4 | **8** | 🟡 | Alembic-Migration mit server_default=0; Backfill-Test vor Migration | Sprint 12 |
| **RISK-B-006** (neu) | Lasttest-Infrastruktur nicht vorhanden (10 simultane Nutzer) | 3 | 3 | **9** | 🟡 | Lasttest-Setup früh in Sprint 13 beginnen; pytest-HTTPServer-Mocks als Fallback | Sprint 13 |

---

## 5. Go/No-Go Bedingungen pro Sprint

### 5.1 Sprint 11 – Go/No-Go

| # | Bedingung | Status | Verantwortlich |
|---|---|---|---|
| 1 | **Security Architect Review** bestanden (Auth-Schema: OAuth2/JWT, bcrypt/argon2, Token-Storage) | ⏳ OFFEN | GREAT Security Architect |
| 2 | **ADR-015** (Auth-Schema-Detailentscheidung) erstellt und accepted | ⏳ OFFEN | GREAT Chief Architect |
| 3 | **CORS-Whitelist** konfiguriert (Schulden-Item #8) | ⏳ OFFEN | GREAT Senior Developer |
| 4 | **Teststrategie Sprint 11** freigegeben (Auth-Tests, Rollen-Matrix-Tests) | ⏳ OFFEN | GREAT QA Director |
| 5 | **Sprint 10** abgeschlossen (offene Items dokumentiert als Schulden) | ✅ DONE | Program Manager |

**Entscheidung:** 🔴 **NO-GO** – Sprint 11 Start blockiert durch Security Architect Review (Bedingung 1) und ADR-015 (Bedingung 2).

### 5.2 Sprint 12 – Go/No-Go

| # | Bedingung | Status | Verantwortlich |
|---|---|---|---|
| 1 | **Sprint 11 abgeschlossen** (Auth + Rollen implementiert + getestet) | ⏳ BLOCKIERT | Program Manager |
| 2 | **ADR-007** (DB-Strategie SQLite/PostgreSQL) final bestätigt | ⏳ OFFEN | GREAT Chief Architect |
| 3 | **Teststrategie Sprint 12** freigegeben (Concurrency-Tests, DB-Engine-Tests) | ⏳ OFFEN | GREAT QA Director |

**Entscheidung:** ⏳ **BLOCKIERT** – Kann nicht entschieden werden, solange Sprint 11 nicht abgeschlossen ist.

### 5.3 Sprint 13 – Go/No-Go

| # | Bedingung | Status | Verantwortlich |
|---|---|---|---|
| 1 | **Sprint 12 abgeschlossen** (Concurrency + Stale-Warning implementiert + getestet) | ⏳ BLOCKIERT | Program Manager |
| 2 | **Lasttest-Setup** bereit (10 simulierte Nutzer) | ⏳ OFFEN | GREAT QA Director |
| 3 | **Teststrategie Sprint 13** freigegeben (E2E-Konfliktszenario, Sharing-Tests) | ⏳ OFFEN | GREAT QA Director |

**Entscheidung:** ⏳ **BLOCKIERT** – Kann nicht entschieden werden, solange Sprint 12 nicht abgeschlossen ist.

---

## 6. Empfehlungen

### 6.1 Ist die Sprint-Zuordnung realistisch?

**JA, mit folgenden Qualifikationen:**

| Bewertung | Begründung |
|---|---|
| **Sprint 11 (Auth + Rollen)** | **Realistisch, aber eng.** Auth von Null mit ~40+ Endpunkten absichern ist technisch anspruchsvoll. Der Aufwand XL (80 SP) für REQ-4001 ist korrekt eingeschätzt. REQ-4020 (60 SP) kann parallel nach REQ-4001-Grundgerüst starten. **Risiko:** Auth verzögert sich → ganzer EPIC-18 rutscht. |
| **Sprint 12 (DB + Concurrency)** | **Realistisch, aber anspruchsvoll.** Drei REQs, aber REQ-4022 (Stale-Warning, 40 SP) ist reines Frontend und kann parallel zu REQ-4021 (Backend) arbeiten. REQ-4006 (DB-Engine-Switch) ist der kritische Vorläufer. **Risiko:** ADR-007-Blocker + SQLite-Migration-Problem. |
| **Sprint 13 (Sharing + Audit + Lasttest)** | **Realistisch.** REQ-4024 (Audit-Trail, 20 SP) ist klein. REQ-4023 (Sharing, 60 SP) ist mittel. Lasttest (40 SP) ist der größte Unsicherheitsfaktor. |

### 6.2 Sollten REQs verschoben werden?

**NEIN – die aktuelle Zuordnung ist optimal.**

| Analyse | Begründung |
|---|---|
| **REQ-4001 in Sprint 11** | Zwingend zuerst – blockiert ALLE anderen REQs. Keine Alternative. |
| **REQ-4020 in Sprint 11** | Kann parallel zu REQ-4001 nach Grundgerüst-Phase. Rollen-Logik benötigt Auth-Kontext. |
| **REQ-4006 in Sprint 12** | Benötigt Auth (Sprint 11) als Basis. DB-Engine-Switch ist Voraussetzung für Concurrency. |
| **REQ-4021 in Sprint 12** | Benötigt REQ-4006 (version-Feld-Migration). Kann nicht früher. |
| **REQ-4022 in Sprint 12** | Benötigt REQ-4021 (409-Response). Frontend-Komponente, parallelisierbar. |
| **REQ-4023 in Sprint 13** | Benötigt REQ-4006 + REQ-4020. Kann nicht früher. |
| **REQ-4024 in Sprint 13** | Benötigt REQ-4001 + REQ-4006. Könnte theoretisch nach Sprint 12, aber Audit-Trail gehört logisch zum Abschluss. |

### 6.3 Ist der Aufwand pro Sprint machbar?

| Sprint | Aufwand | Einschätzung |
|---|---|---|
| Sprint 11 | ≈ 160 SP (XL + L + Buffer) | **Machbar, aber intensiv.** Auth von Null ist der größte einzelne Aufwand im gesamten EPIC. Security-Review ist zwingend. |
| Sprint 12 | ≈ 160 SP (L + XL + M + Buffer) | **Machbar, aber technisch komplex.** Concurrency-Control ist der schwierigste Algorithmus-Teil. |
| Sprint 13 | ≈ 140 SP (L + S + M + Buffer) | **Machbar.** Sharing und Audit sind klar umrissene Features. Lasttest ist der Unsicherheitsfaktor. |

**Gesamtaufwand EPIC-18:** ≈ 420 SP über 3 Sprints ≈ 140 SP/Sprint.

### 6.4 Go/No-Go Empfehlung für EPIC-18-Start

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EPIC-18 START: BEDINGTES GO                             │
│                                                                             │
│  Go/No-Go:   🟡 BEDINGTES GO                                                │
│  Bedingung:  Sprint 11 Start erst NACH Security Architect Review + ADR-015  │
│  Blockierer: RISK-S-001 (Score 20) – Authentifizierung                      │
│                                                                             │
│  NÄCHSTE SCHRITTE:                                                           │
│  1. Security Architect: Auth-Schema-Review durchführen                      │
│  2. Chief Architect: ADR-015 (Auth-Schema-Detail) erstellen + ADR-007       │
│     bestätigen                                                               │
│  3. QA Director: Teststrategie Sprint 11 freigeben                          │
│  4. CORS-Whitelist konfigurieren (Schulden-Item #8)                         │
│  5. Sprint 11 starten                                                        │
│                                                                             │
│  ZEITRAHM-EINSCHÄTZUNG:                                                      │
│  Sprint 11: 2-3 Wochen (Auth + Rollen)                                      │
│  Sprint 12: 2-3 Wochen (DB + Concurrency + Stale-Warning)                   │
│  Sprint 13: 2 Wochen (Sharing + Audit + Lasttest)                           │
│  Gesamt EPIC-18: 6-8 Wochen                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Nächste Agenten

| Agent | Aufgabe | Priorität |
|---|---|---|
| **GREAT Security Architect** | Auth-Schema-Review (OAuth2/JWT, bcrypt/argon2, Token-Storage, CORS-Whitelist) | 🔴 KRITISCH |
| **GREAT Chief Architect** | ADR-015 (Auth-Schema-Detail) erstellen + ADR-007 (DB-Strategie) bestätigen | 🔴 KRITISCH |
| **GREAT QA Director** | Teststrategie Sprint 11 (Auth-Tests, Rollen-Matrix-Tests) freigeben | 🟡 HOCH |
| **GREAT Senior Developer** | TDD-Implementierung Sprint 11 (nach Go/No-Go) | ⏳ BLOCKIERT |
| **GREAT Technical Writer** | EPIC-18-Dokumentation (falls benötigt) | 🟢 NIEDRIG |

---

## 8. Anhang: Out of Scope (wiederholt aus EPIC-18)

- ❌ Echtzeit-Kollaboration (WebSocket/SSE Live-Editing, CRDT/Operational Transform)
- ❌ Live-Presence-Anzeige ("wer schaut gerade zu") und Live-Cursor
- ❌ Echtzeit-Benachrichtigungsfunktion (Push/E-Mail)
- ❌ Enterprise-SSO (SAML/LDAP/Azure AD) – nur lokale OAuth2/JWT-Nutzer
- ❌ Mandantenfähigkeit/Multi-Tenant-SaaS-Hosting
- ❌ Team-Größe > 10 Personen
- ❌ Vollständiges Audit-Log mit Historie (REQ-4003, separat)

---

**Ende des Sprint-Planning-Dokuments**