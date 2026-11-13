# Teststrategie EPIC-18 – Multi-User (Sprint 11–13)

| Feld | Wert |
|---|---|
| **EPIC** | EPIC-18 – Multi-User Nutzung (Teams bis 10 Personen) |
| **Sprints** | 11, 12, 13 (Phase 4) |
| **Version** | 1.0 |
| **Erstellt** | 2026-10-05 |
| **Erstellt von** | GREAT QA Director |
| **Status** | DRAFT – zur Freigabe durch Program Manager |
| **Source of Truth** | `requirements_v1.1.md` (EPIC-18), `decision-log.md` (ADR-012), `risk-log.md` |
| **Governance** | ADR-005 (TDD + pytest-cov), AGENTS.md (TDD-Pflicht, Quality Gate) |

---

## 1. Ziel und Scope

Diese Teststrategie definiert den vollständigen Testplan fuer EPIC-18 (Multi-User). Sie legt fest:
- Welche Test-Level welche REQs abdecken
- Wie Test-Daten strukturiert sind
- Welche Coverage-Ziele pro Sprint gelten
- Welche Quality-Gate-Kriterien pro Sprint gelten
- Welche Risiken existieren und wie sie gemildert werden

**Out of Scope dieser Strategie:**
- Test-Implementierung (nur Planung)
- Echte Realtime-Kollaboration (ADR-012: bewusst out of Scope)
- Enterprise-SSO (SAML/LDAP/Azure AD)

---

## 2. Test-Landschaft (Bestand)

| Ebene | Tool | Konfiguration | Bestehende Tests |
|---|---|---|---|
| **Backend Unit/Integration** | `pytest` + `pytest-cov` + `fastapi.testclient.TestClient` | `pytest.ini` (testpaths=tests), `.coveragerc` (branch=True, fail_under=0) | 40+ Testdateien in `tests/` (z.B. `test_multiuser.py`, `test_health.py`) |
| **Frontend Unit** | `vitest` + `@testing-library/react` (RTL) + `jsdom` | `frontend/package.json` (test: vitest) | 34 Testdateien in `frontend/src/**/__tests__/` |
| **E2E** | `@playwright/test` | `frontend/playwright.config.ts` | Konfiguration vorhanden, erste Tests in `tests/test_ui_crud.py` (TestClient-basiert) |
| **Lasttest** | Noch nicht im Projekt | Empfohlen: `locust` (Python, passt zum Stack) | – |

### Bestehende Konventionen (werden beibehalten)

1. **Backend-Tests**: `tests/test_<feature>.py`, Klassen-basiert (`class TestXxx`) oder funktionale Tests, `conftest.py` mit DB-Seed
2. **Frontend-Tests**: `__tests__`-Verzeichnisse neben Komponenten/Stores, `vitest` describe/it/expect, RTL-Queries
3. **REQ-Referenz**: Testdateien und describe-Blöcke referenzieren REQ-IDs im Kommentar
4. **TDD**: RED → GREEN → REFACTOR (ADR-005, AGENTS.md)

---

## 3. Test-Level Matrix (alle 7 REQs)

### 3.1 REQ-4001 – Authentifizierung (OAuth2/JWT) | Sprint 11

| Test-Level | Test-Suite | Test-Szenarien | Anzahl (geplant) |
|---|---|---|---|
| **Backend Unit** | `tests/test_req4001_auth_tokens.py` | Token-Erzeugung (Access + Refresh), Token-Validierung, Token-Expiration, Refresh-Token-Rotation, Logout invalidiert Refresh-Token, bcrypt-Hashing (niemals Klartext) | 12 |
| **Backend Integration** | `tests/test_req4001_auth_endpoints.py` | POST /auth/login (gueltig/ungueltig), 401 bei fehlendem Token, 401 bei abgelaufenem Token, Depends(get_current_user) auf bestehenden Endpunkten | 15 |
| **Frontend Unit** | `frontend/src/components/__tests__/LoginForm.test.tsx` | Login-Maske rendern, gueltige Credentials → Redirect, unguelte Credentials → Fehler-Message, Token-Speicherung (httpOnly-Cookie), Passwort-Feld masked | 8 |
| **Frontend Unit** | `frontend/src/components/__tests__/ProtectedRoute.test.tsx` | Unauthenticated → Login-Redirect, Authenticated → Content, Token-Expiration → Login-Redirect | 5 |
| **E2E (Playwright)** | `e2e/auth/login.spec.ts` | Login-Flow (gueltig), Login-Flow (ungueltig), Logout-Flow, 401-Redirect nach Session-Ende | 4 |
| **Security** | `tests/test_req4001_security.py` | Brute-Force-Schutz (Rate-Limiting: N Versuche → Block), Invalid Token Formats, JWT-Tampering (geaenderte Claims), SQL-Injection in Login-Fields | 8 |

**Gesamt: ~52 Tests**

### 3.2 REQ-4020 – Rollen & Rechte (Admin/Editor/Viewer) | Sprint 11

| Test-Level | Test-Suite | Test-Szenarien | Anzahl (geplant) |
|---|---|---|---|
| **Backend Unit** | `tests/test_req4020_roles.py` | 3 Rollen x N Endpunkte-Matrix (s.u.), erste registrierte Person → Admin, Rollen-Assignment CRUD | 18 |
| **Backend Integration** | `tests/test_req4020_role_endpoints.py` | 403 bei Viewer + Schreibaktion pro Endpunkt, 200 bei Admin + alle Aktionen, 200 bei Editor + Lese+Schreib (kein Nutzermanagement) | 15 |
| **Frontend Unit** | `frontend/src/components/__tests__/RoleBasedUI.test.tsx` | Viewer: keine Schreib-Buttons sichtbar, Editor: Schreib-Buttons aktiv, Admin: alle Buttons inkl. Nutzerverwaltung, Deaktivierte Buttons (disabled-State) | 8 |
| **E2E (Playwright)** | `e2e/roles/role-access.spec.ts` | Login als Viewer → 403-Message bei Schreibversuch, Login als Editor → Schreibaktion erfolgreich, Login als Admin → Nutzerverwaltung sichtbar | 5 |
| **Security** | `tests/test_req4020_privilege_escalation.py` | Viewer versucht Admin-Endpunkt direkt (Token-Manipulation), Editor versucht Nutzerverwaltung, Rolle-Wechsel ohne Berechtigung | 6 |

**Rollen-Endpunkt-Matrix (Backend):**

| Endpunkt-Typ | Admin | Editor | Viewer |
|---|---|---|---|
| GET /projects (Liste) | ✅ 200 | ✅ 200 | ✅ 200 |
| POST /projects (Erstellen) | ✅ 200 | ✅ 200 | ❌ 403 |
| PUT /projects/{id} (Aendern) | ✅ 200 | ✅ 200 | ❌ 403 |
| DELETE /projects/{id} | ✅ 200 | ❌ 403 | ❌ 403 |
| GET /users (Liste) | ✅ 200 | ❌ 403 | ❌ 403 |
| POST /users (Erstellen) | ✅ 200 | ❌ 403 | ❌ 403 |
| PUT /users/{id}/role | ✅ 200 | ❌ 403 | ❌ 403 |
| GET /projects/{id} (Detail) | ✅ 200 | ✅ 200 | ✅ 200 |
| PUT /categories/{id} | ✅ 200 | ✅ 200 | ❌ 403 |
| PUT /values/{id} | ✅ 200 | ✅ 200 | ❌ 403 |

**Gesamt: ~52 Tests**

### 3.3 REQ-4006 – Multi-User-DB (SQLite/PostgreSQL) | Sprint 12

| Test-Level | Test-Suite | Test-Szenarien | Anzahl (geplant) |
|---|---|---|---|
| **Backend Unit** | `tests/test_req4006_db_engine.py` | DATABASE_URL konfigurierbar, Engine-Switch SQLite→PostgreSQL, Connection Pooling (QueuePool) aktiv, Alembic-Migrationen gegen beide Engines | 8 |
| **Backend Integration** | `tests/test_req4006_db_integration.py` | CRUD-Operationen auf SQLite, CRUD-Operationen auf PostgreSQL (skip-if-unavailable), Concurrent Reads (10 Threads) – bestehend aus `test_multiuser.py` erweitern | 10 |
| **Lasttest** | `tests/test_req4006_load.py` (oder `locustfiles/`) | 10 simulierte Nutzer, gemischte Lese/Schreib-Last, keine Deadlocks, Response-Time < 2s (PostgreSQL) | 5 |

**Hinweis:** `test_multiuser.py` existiert bereits (concurrent reads, schema checks). Diese Tests werden erweitert und parametrisiert.

**Gesamt: ~23 Tests**

### 3.4 REQ-4021 – Optimistic Concurrency Control | Sprint 12

| Test-Level | Test-Suite | Test-Szenarien | Anzahl (geplant) |
|---|---|---|---|
| **Backend Unit** | `tests/test_req4021_concurrency.py` | version-Feld existiert (Project, Category, Value, TestCase), version inkrementiert bei Update, 409 bei Version-Mismatch, 200 bei gueltiger Version, version mit in Response | 10 |
| **Backend Integration** | `tests/test_req4021_concurrency_integration.py` | Zwei simulierte gleichzeitige Updates (gleiche Ausgangs-Version) → zweites liefert 409, 409-Response enthält aktuellen Serverstand, parallele Lesevorgaenge bleiben uneingeschraenkt | 8 |
| **Frontend Unit** | `frontend/src/hooks/__tests__/useOptimisticUpdate.test.ts` | API-Call sendet version-Feld mit, 409-Response wird als Konflikt erkannt, version wird nach erfolgreichem Update aktualisiert | 5 |
| **E2E (Playwright)** | `e2e/concurrency/conflict.spec.ts` | Zwei Browser-Tabs, gleichzeitig bearbeiten → Konflikt-Dialog | 3 |

**Gesamt: ~26 Tests**

### 3.5 REQ-4022 – Stale-Data-Warning Frontend | Sprint 12

| Test-Level | Test-Suite | Test-Szenarien | Anzahl (geplant) |
|---|---|---|---|
| **Frontend Unit** | `frontend/src/components/__tests__/StaleDataBanner.test.tsx` | Banner erscheint bei 409-Response, Banner zeigt "von {Nutzer} geaendert", "Neu laden" Button vorhanden, "Trotzdem ueberschreiben" Button vorhanden, Banner verschwindet nach Aktion, Kein automatisches Ueberschreiben | 8 |
| **Frontend Unit** | `frontend/src/components/__tests__/StaleDataBanner.test.tsx` | Bestaetigungsdialog bei "Trotzdem ueberschreiben", Banner nicht sichtbar bei 200-Response | 4 |
| **E2E (Playwright)** | `e2e/concurrency/stale-banner.spec.ts` | Banner-Interaktion: "Neu laden" → Daten neu geladen, Banner-Interaktion: "Trotzdem ueberschreiben" → Bestaetigung → Ueberschreibung | 3 |

**Gesamt: ~15 Tests**

### 3.6 REQ-4023 – Projekt-Sharing / Mitgliederverwaltung | Sprint 13

| Test-Level | Test-Suite | Test-Szenarien | Anzahl (geplant) |
|---|---|---|---|
| **Backend Unit** | `tests/test_req4023_sharing.py` | Mitgliederliste CRUD (hinzufuegen, entfernen, Rolle aendern), Nutzer ohne Mitgliedschaft sieht Projekt nicht in GET /projects, 403 bei Zugriff ohne Mitgliedschaft, Owner kann Mitglieder verwalten | 10 |
| **Backend Integration** | `tests/test_req4023_sharing_integration.py` | Projekt teilen mit Editor → Editor kann bearbeiten, Projekt teilen mit Viewer → Viewer kann nur lesen, Mitglied entfernen → kein Zugriff mehr | 6 |
| **Frontend Unit** | `frontend/src/components/__tests__/ProjectMembers.test.tsx` | Mitgliederliste rendern, Mitglied hinzufuegen (Dropdown + Rolle), Mitglied entfernen, Rolle aendern | 6 |
| **E2E (Playwright)** | `e2e/sharing/project-sharing.spec.ts` | Projekt teilen Flow, Zugriff pruefen (zweiter Nutzer), Mitglied entfernen → Zugriff entzogen | 4 |

**Gesamt: ~26 Tests**

### 3.7 REQ-4024 – Minimaler Audit-Trail | Sprint 13

| Test-Level | Test-Suite | Test-Szenarien | Anzahl (geplant) |
|---|---|---|---|
| **Backend Unit** | `tests/test_req4024_audit.py` | last_modified_by wird bei Update gesetzt, last_modified_at wird bei Update gesetzt, Felder existieren in Schema (Project, Category, Value, TestCase), Felder werden in API-Response mitgeliefert | 8 |
| **Frontend Unit** | `frontend/src/components/__tests__/AuditTooltip.test.tsx` | Tooltip zeigt "Zuletzt geaendert von X am Y", Tooltip erscheint bei Hover, Formatierung (Datum/Zeit) | 5 |

**Gesamt: ~13 Tests**

---

### 3.8 Zusammenfassung aller Tests

| REQ | Backend Unit | Backend Integration | Frontend Unit | E2E (Playwright) | Security | Lasttest | Gesamt |
|---|---|---|---|---|---|---|---|
| REQ-4001 (Auth) | 12 | 15 | 13 | 4 | 8 | – | **52** |
| REQ-4020 (Rollen) | 18 | 15 | 8 | 5 | 6 | – | **52** |
| REQ-4006 (Multi-User-DB) | 8 | 10 | – | – | – | 5 | **23** |
| REQ-4021 (Concurrency) | 10 | 8 | 5 | 3 | – | – | **26** |
| REQ-4022 (Stale-Warning) | – | – | 12 | 3 | – | – | **15** |
| REQ-4023 (Sharing) | 10 | 6 | 6 | 4 | – | – | **26** |
| REQ-4024 (Audit-Trail) | 8 | – | 5 | – | – | – | **13** |
| **SUMME** | **66** | **54** | **49** | **19** | **14** | **5** | **207** |

---

## 4. Test-Daten Strategie

### 4.1 Test-Nutzer (feste Identitaeten)

| Nutzer-ID | Rolle | Passwort (getestet) | Verwendung |
|---|---|---|---|
| `admin_user` | Admin | `TestAdmin123!` | Admin-Aktionen, Nutzerverwaltung, Projekt-Sharing als Owner |
| `editor_user` | Editor | `TestEditor123!` | Schreibaktionen, Konflikt-Tests |
| `viewer_user` | Viewer | `TestViewer123!` | Nur-Lese-Zugriff, 403-Tests |
| `unregistered_user` | – | – | 401-Tests, nicht authentifizierter Zugriff |
| `concurrent_user_1` | Editor | `TestConcur1!` | Concurrency-Tests (User A) |
| `concurrent_user_2` | Editor | `TestConcur2!` | Concurrency-Tests (User B) |

**Anmerkung:** Passwoerter sind nur in Testkontext (in-memory DB oder Test-DB). Niemals in Produktivcode oder Versionierung.

### 4.2 Test-Projekte (feste Identitaeten)

| Projekt-ID | Owner | Mitglieder | Verwendung |
|---|---|---|---|
| `shared_project` | admin_user | editor_user (Editor), viewer_user (Viewer) | Sharing-Tests, Rollen-Tests |
| `private_project` | editor_user | (kein anderer) | 403-Tests (kein Zugriff fuer andere) |
| `no_access_project` | admin_user | (kein viewer_user) | Viewer sieht Projekt nicht |
| `concurrency_project` | concurrent_user_1 | concurrent_user_2 (Editor) | Concurrency-Tests |

### 4.3 Test-Szenarien (wiederverwendbar)

| Szenar-Name | Beschreibung | REQ-Bezug |
|---|---|---|
| `SCENARIO_CONCURRENT_UPDATE` | Zwei Nutzer bearbeiten gleichzeitig dieselbe Entitaet | REQ-4021 |
| `SCENARIO_ROLE_ESCALATION` | Viewer versucht Admin-Aktion via direkter API-Aufruf | REQ-4020, Security |
| `SCENARIO_TOKEN_EXPIRY` | Token laeuft ab waehrend Session | REQ-4001 |
| `SCENARIO_SHARE_UNSHARE` | Projekt teilen, dann Mitglied entfernen | REQ-4023 |
| `SCENARIO_STALE_RECOVER` | 409 → "Neu laden" vs. "Trotzdem ueberschreiben" | REQ-4022 |

### 4.4 Test-Fixtures (conftest.py Ergaenzungen)

```python
# tests/conftest.py – EPIC-18 Ergaenzungen (geplant)

# Auth-Fixtures
@pytest.fixture
def admin_token(client):
    """JWT-Token fuer admin_user"""
    ...

@pytest.fixture
def editor_token(client):
    """JWT-Token fuer editor_user"""
    ...

@pytest.fixture
def viewer_token(client):
    """JWT-Token fuer viewer_user"""
    ...

# Concurrency-Fixtures
@pytest.fixture
def concurrent_project(client, admin_token, editor_token):
    """Projekt mit zwei Editoren fuer Concurrency-Tests"""
    ...

# DB-Fixtures
@pytest.fixture
def postgres_engine():
    """PostgreSQL Engine (skip-if-unavailable)"""
    ...
```

---

## 5. Coverage-Ziele

### 5.1 Backend (pytest-cov)

| Metrik | Ziel | Messung |
|---|---|---|
| **Statement Coverage** | >= 90% | `.coveragerc` (branch=True), `pytest --cov=src --cov-fail-under=90` |
| **Branch Coverage** | >= 85% | `.coveragerc` (branch=True) |
| **Auth-Endpunkte** | 100% | Separate Coverage-Report fuer `src/app/auth/` |

**Bestand:** `.coveragerc` hat aktuell `fail_under = 0`. Fuer EPIC-18 wird dies schrittweise erhoeht:
- Sprint 11: `fail_under = 85`
- Sprint 12: `fail_under = 88`
- Sprint 13: `fail_under = 90`

### 5.2 Frontend (Vitest)

| Metrik | Ziel | Messung |
|---|---|---|
| **Component Coverage** | >= 80% | `vitest --coverage` (v8- oder istanbul-Provider) |
| **Auth-Komponenten** | 100% | `LoginForm`, `ProtectedRoute`, `StaleDataBanner` |

### 5.3 E2E (Playwright)

| Metrik | Ziel | Messung |
|---|---|---|
| **Kritische Pfade** | 100% | Login, Logout, Konflikt-Dialog, Sharing-Flow |
| **Definition "kritisch"** | Pfade die Datenverlust oder Sicherheitsluecken verursachen koennen | |

### 5.4 Security

| Metrik | Ziel | Messung |
|---|---|---|
| **Auth-Endpunkte** | 100% der ACs getestet | OWASP Testing Guide v4, Auth-Section |
| **Privilege Escalation** | 100% der Rolle-Endpunkt-Kombinationen | Matrix aus Abschnitt 3.2 |

---

## 6. Quality Gate pro Sprint

### 6.1 Sprint 11 (Auth + Rollen)

| # | Kriterium | Status | Blocker? |
|---|---|---|---|
| 1 | Alle Auth-Unit-Tests (REQ-4001) gruen | ☐ | 🔴 Ja |
| 2 | Login/Logout E2E (Playwright) gruen | ☐ | 🔴 Ja |
| 3 | Brute-Force-Schutz getestet (Rate-Limiting) | ☐ | 🔴 Ja |
| 4 | Rollen-Matrix (3 Rollen × 10 Endpunkte) getestet | ☐ | 🔴 Ja |
| 5 | Privilege-Escalation-Tests gruen | ☐ | 🔴 Ja |
| 6 | Backend Coverage >= 85% | ☐ | 🟡 Ja (ab Sprint 11) |
| 7 | Frontend Coverage >= 80% (Auth-Komponenten) | ☐ | 🟡 Ja |
| 8 | Security-Review bestanden (RISK-S-001) | ☐ | 🔴 Ja |
| 9 | Password-Hashing: bcrypt/argon2, niemals Klartext | ☐ | 🔴 Ja |
| 10 | Token-Speicherung: httpOnly-Cookie (kein localStorage) | ☐ | 🔴 Ja |

**Go/No-Go:** Alle 🔴-Kriterien muessen gruen sein. 🟡-Kriterien duerfen mit dokumentierter Ausnahme und Remediation-Plan uebersprungen werden.

### 6.2 Sprint 12 (Concurrency + Stale-Warning + Multi-User-DB)

| # | Kriterium | Status | Blocker? |
|---|---|---|---|
| 1 | 409-Conflict Tests gruen (2 gleichzeitige Updates) | ☐ | 🔴 Ja |
| 2 | Stale-Data-Banner Tests gruen (alle 6 ACs) | ☐ | 🔴 Ja |
| 3 | Engine-Switch Tests gruen (SQLite + PostgreSQL) | ☐ | 🔴 Ja |
| 4 | Connection Pooling aktiv und getestet | ☐ | 🔴 Ja |
| 5 | Backend Coverage >= 88% | ☐ | 🟡 Ja |
| 6 | Frontend Coverage >= 80% (Concurrency-Komponenten) | ☐ | 🟡 Ja |
| 7 | Keine Race-Conditions in Tests (deterministisch) | ☐ | 🔴 Ja |
| 8 | Alembic-Migrationen gegen beide Engines erfolgreich | ☐ | 🔴 Ja |
| 9 | Parallele Lesevorgaenge bleiben uneingeschraenkt | ☐ | 🔴 Ja |

**Go/No-Go:** Alle 🔴-Kriterien muessen gruen sein.

### 6.3 Sprint 13 (Sharing + Audit + Lasttest)

| # | Kriterium | Status | Blocker? |
|---|---|---|---|
| 1 | Mitglieder-CRUD Tests gruen | ☐ | 🔴 Ja |
| 2 | 403-Filter Tests gruen (kein Zugriff ohne Mitgliedschaft) | ☐ | 🔴 Ja |
| 3 | Audit-Trail Tests gruen (last_modified_by/at) | ☐ | 🔴 Ja |
| 4 | Lasttest 10 Nutzer gruen (keine Deadlocks, < 2s Response) | ☐ | 🔴 Ja |
| 5 | Backend Coverage >= 90% | ☐ | 🔴 Ja |
| 6 | Frontend Coverage >= 80% | ☐ | 🟡 Ja |
| 7 | E2E-Regression (alle bestehenden Tests) gruen | ☐ | 🔴 Ja |
| 8 | E2E Sharing-Flow gruen | ☐ | 🔴 Ja |
| 9 | Single-User-Betrieb (SQLite) ohne Regression | ☐ | 🔴 Ja |

**Go/No-Go:** Alle 🔴-Kriterien muessen gruen sein.

---

## 7. Risiken und Gegenmassnahmen

| ID | Risiko | W | I | Score | Ampel | Gegenmassnahme |
|---|---|---|---|---|---|---|
| **RISK-E18-T-001** | Auth-Tests unvollstaendig (Luecken in Token-Validierung) | 3 | 5 | 15 | 🔴 | Property-Based-Tests fuer Token (hypothesis), fuzzer fuer Edge-Cases (ungueltige Signaturen, manipulierte Claims) |
| **RISK-E18-T-002** | Race-Conditions in Concurrency-Tests nicht reproduzierbar | 3 | 4 | 12 | 🔴 | Deterministische Tests mit Time-Mocking (`freezegun`), multiple Retries (3x), Thread-sleep-Reduktion in Tests |
| **RISK-E18-T-003** | Lasttest instabil (SQLite-Locks auf CI) | 2 | 4 | 8 | 🟡 | PostgreSQL-Lasttest als Primary, SQLite-Lasttest als Secondary (skip-if-sqlite-on-ci) |
| **RISK-E18-T-004** | E2E-Tests flaky (Token-Expiration waehrend Test) | 2 | 3 | 6 | 🟡 | Token-Refresh in E2E-Setup, lange Token-Life fuer Tests (24h statt 15min), automatische Re-Auth im Playwright-Setup |
| **RISK-E18-T-005** | Rolle-Eskalation nicht getestet (Viewer → Editor via Token-Manipulation) | 3 | 5 | 15 | 🔴 | Explizite Privilege-Escalation-Tests pro Endpunkt (jeder Viewer-Test auch mit manipuliertem Token) |
| **RISK-E18-T-006** | PostgreSQL nicht auf CI verfuegbar | 2 | 4 | 8 | 🟡 | Docker-Container fuer PostgreSQL in CI, `@pytest.mark.skipif` fuer PostgreSQL-Tests ohne DB |
| **RISK-E18-T-007** | Bestehende Tests brechen durch Auth-Overlay (alle Endpunkte jetzt auth-pflichtig) | 4 | 4 | 16 | 🔴 | Fixture-basierte Token-Injection in alle bestehenden Tests (conftest.py), schrittweise Migration |
| **RISK-E18-T-008** | Concurrency-Tests auf Windows (Thread-Verhalten vs. Unix) | 2 | 3 | 6 | 🟡 | Platform-spezifische Test-Adaption, `pytest.mark.windows` / `pytest.mark.linux` |

### Eskalationspflichtig (Score ≥ 10)

| ID | Score | Massnahme |
|---|---|---|
| RISK-E18-T-001 | 15 | Property-Based-Tests + Fuzzer in Sprint 11 |
| RISK-E18-T-002 | 12 | Deterministische Concurrency-Tests in Sprint 12 |
| RISK-E18-T-005 | 15 | Privilege-Escalation-Tests in Sprint 11 |
| RISK-E18-T-007 | 16 | Token-Fixtures in conftest.py vor Sprint 11-Start |

---

## 8. Test-Ausfuehrungsstrategie

### 8.1 Backend-Tests (pytest)

```bash
# Alle Backend-Tests mit Coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# EPIC-18 spezifisch (Sprint 11)
pytest tests/test_req4001_*.py tests/test_req4020_*.py --cov=src

# EPIC-18 spezifisch (Sprint 12)
pytest tests/test_req4006_*.py tests/test_req4021_*.py --cov=src

# EPIC-18 spezifisch (Sprint 13)
pytest tests/test_req4023_*.py tests/test_req4024_*.py --cov=src
```

### 8.2 Frontend-Tests (Vitest)

```bash
# Alle Frontend-Tests mit Coverage
npm run test -- --coverage

# EPIC-18 spezifisch (Sprint 11)
npx vitest frontend/src/components/__tests__/LoginForm.test.tsx \
            frontend/src/components/__tests__/ProtectedRoute.test.tsx \
            frontend/src/components/__tests__/RoleBasedUI.test.tsx

# EPIC-18 spezifisch (Sprint 12)
npx vitest frontend/src/components/__tests__/StaleDataBanner.test.tsx \
            frontend/src/hooks/__tests__/useOptimisticUpdate.test.ts

# EPIC-18 spezifisch (Sprint 13)
npx vitest frontend/src/components/__tests__/ProjectMembers.test.tsx \
            frontend/src/components/__tests__/AuditTooltip.test.tsx
```

### 8.3 E2E-Tests (Playwright)

```bash
# Alle E2E-Tests
npx playwright test

# EPIC-18 spezifisch (Sprint 11)
npx playwright test e2e/auth/ e2e/roles/

# EPIC-18 spezifisch (Sprint 12)
npx playwright test e2e/concurrency/

# EPIC-18 spezifisch (Sprint 13)
npx playwright test e2e/sharing/
```

### 8.4 Lasttest (geplant)

```bash
# Locust (Python, passt zum Stack)
locust -f locustfiles/epic18_load.py --users 10 --spawn-rate 1 --run-time 5m

# Alternative: k6 (falls JavaScript-Lasttests bevorzugt)
k6 run loadtests/epic18_load.js
```

---

## 9. Test-Dateien Struktur (geplant)

```
tests/
├── conftest.py                          # EPIC-18: +Auth-Fixtures, +DB-Fixtures
├── test_req4001_auth_tokens.py          # NEW: Token-Erzeugung/Validierung
├── test_req4001_auth_endpoints.py       # NEW: Auth-Endpunkte
├── test_req4001_security.py             # NEW: Brute-Force, Invalid Tokens
├── test_req4020_roles.py                # NEW: Rollen-Unit-Tests
├── test_req4020_role_endpoints.py       # NEW: Rollen-Endpunkt-Matrix
├── test_req4020_privilege_escalation.py # NEW: Privilege-Escalation
├── test_req4006_db_engine.py            # NEW: Engine-Switch, Pooling
├── test_req4006_db_integration.py       # NEW: DB-Integration (erweitert test_multiuser.py)
├── test_req4006_load.py                 # NEW: Lasttest-Skeleton
├── test_req4021_concurrency.py          # NEW: Version-Feld, 409-Conflict
├── test_req4021_concurrency_integration.py  # NEW: 2 gleichzeitige Updates
├── test_req4023_sharing.py              # NEW: Mitglieder-CRUD
├── test_req4023_sharing_integration.py  # NEW: Sharing-Integration
├── test_req4024_audit.py                # NEW: last_modified_* Tests
├── test_multiuser.py                    # EXISTIEREND: wird erweitert/parametrisiert

frontend/src/
├── components/__tests__/
│   ├── LoginForm.test.tsx               # NEW
│   ├── ProtectedRoute.test.tsx          # NEW
│   ├── RoleBasedUI.test.tsx             # NEW
│   ├── StaleDataBanner.test.tsx         # NEW
│   ├── ProjectMembers.test.tsx          # NEW
│   └── AuditTooltip.test.tsx            # NEW
├── hooks/__tests__/
│   └── useOptimisticUpdate.test.ts      # NEW
├── store/__tests__/
│   └── authStore.test.ts                # NEW (Token-State Management)

e2e/                                      # NEW: Playwright E2E-Verzeichnis
├── auth/
│   └── login.spec.ts                    # NEW
├── roles/
│   └── role-access.spec.ts              # NEW
├── concurrency/
│   ├── conflict.spec.ts                 # NEW
│   └── stale-banner.spec.ts             # NEW
└── sharing/
    └── project-sharing.spec.ts          # NEW
```

---

## 10. Abhaengigkeiten und Voraussetzungen

### 10.1 Vor Sprint-11-Start (zwingend)

| Voraussetzung | Status | Verantwortlich |
|---|---|---|
| Security Architect Review Auth-Schema (RISK-S-001) | ☐ Ausstehend | Security Architect |
| CORS-Whitelist-Konfiguration (Schulden-Item #8) | ☐ Ausstehend | Chief Architect |
| conftest.py mit Auth-Fixtures vorbereitet | ☐ Geplant | QA Director |
| `.coveragerc` fail_under auf 85 gesetzt | ☐ Geplant | QA Director |

### 10.2 REQ-Abhaengigkeiten (aus requirements_v1.1.md)

```
REQ-4001 (Auth)
  └── Blockiert: REQ-4006, REQ-4020, REQ-4021, REQ-4022, REQ-4023, REQ-4024

REQ-4020 (Rollen)
  ├── Abhaengig: REQ-4001
  └── Blockiert: REQ-4023

REQ-4006 (Multi-User-DB)
  ├── Abhaengig: REQ-4001
  └── Blockiert: REQ-4021, REQ-4023

REQ-4021 (Concurrency)
  ├── Abhaengig: REQ-4006
  └── Blockiert: REQ-4022

REQ-4022 (Stale-Warning)
  └── Abhaengig: REQ-4021

REQ-4023 (Sharing)
  ├── Abhaengig: REQ-4006, REQ-4020

REQ-4024 (Audit-Trail)
  ├── Abhaengig: REQ-4001, REQ-4006
```

**Folgerung:** REQ-4001 MUSS in Sprint 11 vollstaendig getestet und freigegeben sein, bevor Sprint 12 starten kann.

---

## 11. Auswirkung auf bestehende Tests

### 11.1 Auth-Overlay

Wenn REQ-4001 implementiert ist, werden ALLE bestehenden API-Endpunkte auth-pflichtig. Das bedeutet:

- **Alle bestehenden 40+ Backend-Tests** muessen mit Token-Fixtures arbeiten
- **conftest.py** muss eine automatische Token-Injection bieten
- **Migrationsstrategie:**
  1. Phase 1: Auth-Endpunkte haben eigenen Test-Client (ohne Auth)
  2. Phase 2: Bestehende Tests erhalten `@pytest.fixture` fuer Token
  3. Phase 3: Alle Tests laufen mit Auth-Overlay

### 11.2 Bestehende test_multiuser.py

Die existierende Datei `tests/test_multiuser.py` (106 Zeilen) wird:
- **Erweitert** um PostgreSQL-Tests (REQ-4006)
- **Parametrisiert** fuer Engine-Switch
- **Nicht ersetzt** – bestehende Tests bleiben als Regression-Schutz

---

## 12. QA-Entscheidungsvorlage (pro Sprint)

Nach jedem Sprint wird folgende QA-Entscheidung erstellt:

```markdown
# QA-Entscheidung – EPIC-18 Sprint XX

**Status:** PASS | FAIL | CONDITIONAL PASS | NOT VERIFIED

**REQs abgedeckt:** REQ-XXXX, REQ-YYYY, ...

**Ausgefuehrte Tests:**
- Backend: XX/XX gruen (YY% Coverage)
- Frontend: XX/XX gruen (ZZ% Coverage)
- E2E: XX/XX gruen
- Security: XX/XX gruen
- Lasttest: XX/XX gruen (falls zutreffend)

**Blocker:**
- [ ] Keine / Liste der Blocker

**Coverage:**
- Backend: XX% (Ziel: YY%)
- Frontend: XX% (Ziel: YY%)

**Naechste Aktion:**
- [ ] Release freigegeben / Sprint-Transition freigegeben
- [ ] Remediation fuer CONDITIONAL-PASS-Items
```

---

## 13. Anhang

### A. OWASP Testing Guide Referenzen

| Bereich | OWASP v4 Section | EPIC-18 Relevanz |
|---|---|---|
| Auth Testing | Authentication Testing | REQ-4001 |
| Authorization Testing | Authorization Testing | REQ-4020 |
| Session Management | Session Management Testing | REQ-4001 (Token) |
| Input Validation | Input Validation Testing | Alle Schreib-Endpunkte |

### B. ISTQB Referenzen

| Begriff | ISTQB Source | EPIC-18 Relevanz |
|---|---|---|
| Boundary Value Analysis | CTFL v4.0 | Konflikt-Grenzwerte (version-Feld) |
| Equivalence Partitioning | CTFL v4.0 | Rollen-Partitionen (Admin/Editor/Viewer) |
| Error Guessing | CTAL-TA | Privilege-Escalation-Szenarien |

### C. Tool-Empfehlungen

| Zweck | Tool | Begründung |
|---|---|---|
| Lasttest | `locust` (Python) | Passt zum Python-Stack, keine JS-Abhaengigkeit |
| Property-Based-Tests | `hypothesis` (Python) | Token-Edge-Cases, Version-Numer |
| Time-Mocking | `freezegun` (Python) | Deterministische Concurrency-Tests |
| Security Scanning | `bandit` (Python) | Statische Security-Analyse |
| JWT-Testing | `PyJWT` (direkt) | Token-Manipulation in Tests |

---

## 14. Freigabe

| Rolle | Name | Unterschrift | Datum |
|---|---|---|---|
| QA Director | GREAT QA Director | ☐ | |
| Program Manager | GREAT Program Manager | ☐ | |
| Security Architect | GREAT Security Architect | ☐ | |
| Chief Architect | GREAT Chief Architect | ☐ | |
| Projektinhaber | Georg Hartel | ☐ | |

---

*Diese Teststrategie ist ein lebendes Dokument. Aenderungen werden versioniert und im decision-log.md als ADR-Ergaenzung dokumentiert.*