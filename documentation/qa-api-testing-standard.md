# QA-API-Testing-Standard

**Version:** 1.0
**Stand:** 2026-10-09
**Gilt ab:** Sofort

---

## Pflichtanweisung: API-Schnittstellentests

Ab diesem Datum gelten folgende verbindliche Regeln fuer alle Aenderungen an G.R.E.A.T.:

### 1. Jede Funktion muss via API testbar sein

- Jeder neue Endpoint in `src/app/routers/` benoetigt mindestens einen API-Test
- Bestehende Endpunkte ohne API-Test erhalten nachzuholen
- Tests liegen in `tests/test_*.py`

### 2. Immer ein API-Regressionstest

Bei jeder Code-Aenderung:
- Mindestens ein Regressionstest fuer den betroffenen Endpoint
- Testet den Happy Path (200/201 Response)
- Testet mindestens einen Error-Case (401, 403, 404, 422)
- Verwendet Auth-Fixtures (siehe unten)

### 3. Auth-Fixtures verwenden

**NIEMALS** ohne Auth testen. Alle Tests muessen eine der folgenden Fixtures verwenden:

| Fixture | Rolle | Verwendung |
|---|---|---|
| `admin_cookies` | admin | Admin-only Endpunkte, Backup reset/restore, BugMagnet-Import |
| `editor_cookies` | editor | Schreib-Operationen (require_writer) |
| `viewer_cookies` | viewer | Lese-Operationen (require_api_capable) |
| `api_user_cookies` | api_user | API-only Zugriff (read-only) |

**Vorhanden in:** `tests/conftest.py`

### 4. Teststruktur

Jeder API-Test sollte folgende Struktur haben:

```python
def test_endpoint_happy_path(client, admin_cookies):
    # Given: authentifizierter User
    # When: Request an Endpoint
    resp = client.get("/api/projects", cookies=admin_cookies)
    # Then: 200 OK und korrekte Response
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_endpoint_unauthenticated(client):
    # Given: kein Token
    # When: Request an Endpoint
    resp = client.get("/api/projects")
    # Then: 401 Unauthorized
    assert resp.status_code == 401

def test_endpoint_wrong_role(client, viewer_cookies):
    # Given: User mit falscher Rolle
    # When: Schreib-Operation
    resp = client.post("/api/projects", json={...}, cookies=viewer_cookies)
    # Then: 403 Forbidden
    assert resp.status_code == 403
```

### 5. Rollen-spezifische Tests

Fuer jeden Endpoint testen:

| Endpoint-Typ | admin | editor | viewer | api_user | ohne Auth |
|---|---|---|---|---|---|
| **Lese (GET)** | 200 | 200 | 200 | 200 | 401 |
| **Schreib (POST/PUT/PATCH/DELETE)** | 200/201 | 200/201 | 403 | 403 | 401 |
| **Admin-only (reset/restore/import)** | 200/201 | 403 | 403 | 403 | 401 |

### 6. Testdateien-Namenskonvention

| Bereich | Testdatei |
|---|---|
| Projects API | `test_projects_api.py` |
| Generate API | `test_generate_api.py` |
| Dataclasses API | `test_dataclasses_api.py` |
| Datatodes API | `test_datanodes_api.py` |
| Backup API | `test_backup_api.py` |
| Decision Table API | `test_decision_table_api.py` |
| Sharing API | `test_sharing_api.py` |
| Users API | `test_users_api.py` |
| Auth Overlay | `test_auth_overlay.py` |
| Docs Auth | `test_docs_auth_middleware.py` |
| API User Roles | `test_api_user_roles.py` |

### 7. Quality Gate

Vor jedem Commit/PR:
- [ ] Alle API-Tests passen (`pytest tests/ -v`)
- [ ] Jeder neue Endpoint hat mindestens 3 Tests (Happy Path + 2 Error-Cases)
- [ ] Auth-Fixtures werden verwendet
- [ ] Rollen-spezifische Tests sind vorhanden

### 8. Nicht-getestete Endpunkte

Bei Uebernahme eines Endpoints ohne Tests:
1. Zuerst Regressionstests erstellen
2. Erst dann Aenderungen am Code vornehmen
3. Tests muessen VOR der Implementierung rot sein (TDD)

---

## Haftungsausschluss

Diese Anweisung ist **verbindlich** fuer alle Agenten (QA Director, Senior Developer, UX Lead, etc.).

Abweichungen nur mit expliziter Genehmigung des Orchestrators und Dokumentation im Decision-Log.

---

## Verweis

- Auth-Fixtures: `tests/conftest.py`
- Bestehende API-Tests: `tests/test_auth_overlay.py`, `tests/test_api_user_roles.py`
- Auth-Dependencies: `src/app/auth_deps.py`