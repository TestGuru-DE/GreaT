# Phase 4 – Enterprise & Stabilisierung

**Version:** 1.0  
**Datum:** 2026-07-02  
**Status:** ✅ Kickoff-Planning akzeptiert  
**Referenzen:** project-assessment.md (Phase-3-Abschluss), phase-4-sprint-stabi-needs.md (Schulden-Analyse)

---

## Vision & Ziel

**Phase 3** (abgeschlossen 2026-07-02) hat React-Frontend solidifiziert: 367 Tests, Office-UX, Theme-System, Undo/Redo, Risikoabdeckungs-Metriken.

**Phase 4** konzentriert sich auf:
1. **Sprint 6–7:** Technische Stabilisierung (Stabi I + II)
2. **Sprint 8:** Multi-User-Enablement (PostgreSQL optional, Auth-Vorbereitung)
3. **Sprint 9+:** Enterprise-Features (Auth, MCDC/T-Wise optimiert, Ollama-Integration optional)

---

## Sprint-Struktur Phase 4

### Sprint 6 – Stabi I: Schnelle Wins (2 Wochen, ~100 SP)

**Thema:** Konfigurierbarkeit + Monitoring-Grundlagen

| REQ-ID | Titel | SP | Prio | Abhängigkeiten | Status |
|---|---|---|---|---|---|
| REQ-4007 | GREAT_PORT + .env Unterstützung | 8 | **MUST** | – | Planned |
| REQ-4008 | Health-Check Endpoint /health | 5 | **SHOULD** | REQ-4007 | Planned |
| – | Versionspinning requirements.txt vervollständigen | 3 | **SHOULD** | – | Planned |
| – | Input-Validierung erweitern (Field constraints) | 8 | **COULD** | – | Planned |
| – | Services-Refactoring (services.py → modules) | 13 | **COULD** | – | Planned |

**Sprint 6 Go/No-Go Kriterien:**
- ✅ REQ-4007 vollständig + getestet
- ✅ REQ-4008 vollständig + getestet
- ✅ 267+ Tests grün (baseline: 263 + 4 neue für REQ-4007/4008)
- ✅ Keine Regressions in Phase-3-Features
- ✅ PR-Merge ohne Konflikte

**Abhängigkeiten:** Keine  
**Blockierer:** Keine  

---

### Sprint 7 – Stabi II: Qualität & Monitoring (2 Wochen, ~100 SP)

**Thema:** Logging + Testing-Ausbau + Performance-Verifizierung

| REQ-ID | Titel | SP | Prio | Abhängigkeiten | Status |
|---|---|---|---|---|---|
| REQ-4009 | Strukturiertes Logging (structlog JSON) | 13 | **SHOULD** | REQ-4007 | Planned |
| REQ-4010 | E2E-Tests (Playwright: 5 Kern-Workflows) | 21 | **SHOULD** | – | Planned |
| – | Frontend-Coverage-Messung (Vitest) | 5 | **COULD** | – | Planned |
| – | Performance-Baseline: Pairwise < 1s, T-Wise < 5s | 8 | **COULD** | – | Planned |
| – | Health-Check erweitern (DB-Ping, Version) | 3 | **COULD** | REQ-4008 | Planned |

**Sprint 7 Go/No-Go Kriterien:**
- ✅ REQ-4009 vollständig (JSON-Logs via structlog)
- ✅ REQ-4010 5 E2E-Szenarien (Playwright) grün
- ✅ 290+ Tests grün (baseline: 267 + E2E-Coverage)
- ✅ Performance-Report: Generierung < 5s für Standard-Projekte
- ✅ Keine Known Bugs, nur Minor Warnings

**Abhängigkeiten:** REQ-4007 (für Logging Config)  
**Blockierer:** Keine  

---

### Sprint 8 – Multi-User Vorbereitung (3 Wochen, ~130 SP)

**Thema:** Auth + Database-Optionen + Session-Management

| REQ-ID | Titel | SP | Prio | Abhängigkeiten | Status |
|---|---|---|---|---|---|
| REQ-4006 | Multi-User: PostgreSQL optional neben SQLite | 34 | **MUST** | ADR-007 | Planned |
| – | Session-Management: User-Context in FastAPI | 13 | **MUST** | REQ-4006 | Planned |
| – | OAuth2/JWT Auth-Schema (optional, vorbereitet) | 21 | **SHOULD** | REQ-4006 | Planned |
| – | CORS-Konfiguration: allow_origins per ENV | 5 | **SHOULD** | REQ-4007 | Planned |
| – | Rate-Limiting Middleware (optional) | 13 | **COULD** | – | Planned |

**Sprint 8 Go/No-Go Kriterien:**
- ✅ PostgreSQL-Support + Tests (optional alternate DB)
- ✅ User-Context in FastAPI (SQLAlchemy scoped_session)
- ✅ Auth-Schema designed (ADR-012) – Implementation optional für Sprint 9
- ✅ 310+ Tests grün
- ✅ Keine Regression in Single-User-Mode (SQLite)

**Abhängigkeiten:** REQ-4007, REQ-4008, REQ-4009, REQ-4010  
**Blockierer:** ADR-007 (DB-Strategy: SQLite persistent oder PostgreSQL optional)  

---

### Sprint 9+ – Enterprise Features (TBD)

**Thema:** Auth-Implementation, Advanced Combinatorics, KI-Integration

| REQ-ID | Titel | Sprint | Prio | Status |
|---|---|---|---|---|
| REQ-4001 | Authentifizierung (OAuth2/JWT) | Sprint 9 | **MUST** | Planned |
| REQ-4002 | Team-Verwaltung (Projekte teilen) | Sprint 10 | **SHOULD** | Planned |
| REQ-4003 | Audit-Log (Wer hat was wann geändert) | Sprint 11 | **COULD** | Planned |
| REQ-4004 | MCDC + T-Wise Optimierung | Sprint 9 | **SHOULD** | Planned |
| REQ-4005 | Ollama / LLM-Integration (optional) | Sprint 12 | **COULD** | Planned |

---

## Neue Requirements (Phase 4 Upstream)

### REQ-4007: GREAT_PORT Umgebungsvariable

**Priority:** Must  
**Sprint:** Sprint 6  
**Geschätzt:** 8 SP  
**Status:** Planned  

**Beschreibung:**
FastAPI soll auf via GREAT_PORT env-Variable konfigurierbarem Port laufen, nicht hardcoded 8000.

**Akzeptanzkriterien:**
1. GREAT_PORT=9000 → API läuft auf Port 9000
2. Kein GREAT_PORT gesetzt → Default 8000 (Backward-compatible)
3. Start.bat unterstützt SET GREAT_PORT=PORT bevor uvicorn startet
4. .env-Datei wird mit python-dotenv automatisch geladen

**Abhängigkeiten:** python-dotenv Dependency  
**Tested By:** test_environment_config.py  

---

### REQ-4008: Health-Check Endpoint

**Priority:** Should  
**Sprint:** Sprint 6  
**Geschätzt:** 5 SP  
**Status:** Planned  

**Beschreibung:**
GET /health Endpunkt meldet System-Status für Docker/Kubernetes liveness probes.

**Response (200 OK):**
```json
{
  "status": "ok",
  "database": "connected",
  "version": "1.1.0",
  "timestamp": "2026-07-02T12:34:56Z"
}
```

**Fehler (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "database": "disconnected",
  "reason": "SQLite not accessible"
}
```

**Abhängigkeiten:** Keine (Router unabhängig)  
**Tested By:** test_health_check.py  

---

### REQ-4009: Strukturiertes Logging

**Priority:** Should  
**Sprint:** Sprint 7  
**Geschätzt:** 13 SP  
**Status:** Planned  

**Beschreibung:**
Strukturierte JSON-Logs statt nur print() + uvicorn. Konfigurierbar via GREAT_LOG_LEVEL env.

**Features:**
- JSON-Output (timestamp, level, message, context)
- Log-Rotation (max 10 MB pro File, 5 Files kept)
- Optional Datei-Output (LOG_FILE env)
- GREAT_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR

**Abhängigkeiten:** structlog ≥24.1, python-json-logger  
**Tested By:** test_structured_logging.py  

---

### REQ-4010: E2E-Tests (Playwright)

**Priority:** Should  
**Sprint:** Sprint 7  
**Geschätzt:** 21 SP  
**Status:** Planned  

**Beschreibung:**
Playwright E2E-Test-Suite für 5 kritische Workflows:

1. **Workflow 1:** Create Project → Add Category → Add Values → Generiere Pairwise → Verify Table
2. **Workflow 2:** Import CSV → Verify in Table → Export CSV → Roundtrip Check
3. **Workflow 3:** Create Regel (Forbidden) → Generate → Verify Testfälle nicht betroffen
4. **Workflow 4:** Undo/Redo: Delete → Undo → Verify wiederhergestellt
5. **Workflow 5:** Theme-Switch: Hellbar → Dark → Verify CSS-Variablen geändert

**Setup:**
- Playwright.config.ts für WebKit + Chrome
- fixtures für Server-Start + Cleanup
- Page-Objects für UI-Navigation

**Abhängigkeiten:** pytest-playwright ✅ (bereits in requirements.txt)  
**Tested By:** tests/e2e/*.py (new)  

---

### REQ-4006: Multi-User / PostgreSQL Optional

**Priority:** Must  
**Sprint:** Sprint 8  
**Geschätzt:** 34 SP (+ 52 weitere)  
**Status:** Planned  

**Beschreibung:**
System vorbereiten für Multi-User via optionale PostgreSQL statt nur SQLite.

**Features:**
- SQLAlchemy Engine-Switch via DATABASE_URL env
- Alembic-Migrationen für SQLite + PostgreSQL
- Connection Pooling (sqlalchemy.pool.QueuePool)
- User-Context Tracking (Sprache für Sprint 9)

**Architektur:**
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tanos.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
```

**Abhängigkeiten:** psycopg2 (optional), sqlalchemy ✅, alembic ✅  
**Tested By:** tests/test_multi_user_db.py (SQLite + PostgreSQL-Skip-If)  

---

## Phasen-Abhängigkeiten

```
Phase 3 ✅ DONE
    ↓
Phase 4 Sprint 6 (Stabi I) ← REQ-4007, REQ-4008
    ↓
Phase 4 Sprint 7 (Stabi II) ← REQ-4009, REQ-4010 (depends on Sprint 6)
    ↓
Phase 4 Sprint 8 (Multi-User) ← REQ-4006 (depends on Sprint 7)
    ↓
Phase 4 Sprint 9+ (Enterprise) ← REQ-4001–4005
```

**Blockierer für Phase 4 Start:** ✅ Keine (Phase 3 abgeschlossen)

---

## Governance & Freigaben

### Sprint 6 Freigabe (vor Start)

- ⏳ **Chief Architect:** ADR-007 (PostgreSQL optional ja/nein) unterschreiben
- ⏳ **Program Manager:** Sprint-6-Backlog priorisieren
- ⏳ **Senior QA Director:** Test-Strategy für REQ-4007/4008 approved

### Sprint 7 Freigabe (vor Start)

- ⏳ **Chief Architect:** Logging-Framework (structlog vs. python-logging) ADR
- ⏳ **Senior QA Director:** E2E-Test-Strategy + Playwright-Acceptance

### Sprint 8 Freigabe (vor Start)

- ⏳ **Chief Architect:** ADR-007 + Multi-User Architecture
- ⏳ **Security Architect:** Auth-Schema + CORS-Policy Review
- ⏳ **Program Manager:** Sprint-8 Scope-Lock (Auth optional oder Must?)

---

## Known Risks (aus risk-log.md)

| Risk-ID | Beschreibung | Mitigation |
|---|---|---|
| RISK-S-001 | Keine Authentifizierung | REQ-4001 (Sprint 9) |
| RISK-B-001 | Keine CI/CD | GitHub Actions in Phase 4 Sprint 7–8 |
| RISK-T-003 | Abhängigkeitskonflikte | Versionspinning in Sprint 6 |
| RISK-T-006 | SQLite für Multi-User ungeeignet | PostgreSQL-Support in Sprint 8 |

---

## Priorisierungs-Workshop

**Vor Sprint 6 Start:**
User wählt aus `phase-4-sprint-stabi-needs.md` Top-5-Kandidaten:

1. **REQ-4007** (GREAT_PORT) – **SOFORT** ✅
2. **REQ-4008** (Health-Check) – Sprint 6 ✅
3. **REQ-4009** (Logging) – Sprint 7 ✅
4. **REQ-4010** (E2E-Tests) – Sprint 7 ✅
5. **REQ-4006** (Multi-User) – Sprint 8 ✅

**Weitere Optionen (falls Capacity):**
- Services-Refactoring (Aufwand hoch, Impact niedrig)
- Input-Validierung erweitern
- Frontend-Coverage-Messung

---

## Success Metrics (EoP4 = 2026-09-30)

| Metrik | Target | Baseline | Trend |
|---|---|---|---|
| Tests gesamt | ≥ 350 | 263 | ⬆️ +87 |
| Code Coverage | ≥ 90% | unbekannt | 📊 Measure |
| E2E-Szenarien | ≥ 5 | 0 | ⬆️ +5 |
| API Endpoints | ≥ 25 | 22 | ⬆️ +3 (/health, etc) |
| Build-Zeit | < 30s | ~45s (Vite) | ⬇️ Optimize |
| Deployment-Zeit | < 5m | N/A | 📊 Measure |

---

## Dokumente (nach Phase 4 Sprint 6+7+8)

- `documentation/phase-4-sprint-6-planning.md` (detailliert vor Sprint 6)
- `documentation/phase-4-sprint-7-planning.md` (detailliert vor Sprint 7)
- `documentation/phase-4-sprint-8-planning.md` (detailliert vor Sprint 8)
- `documentation/phase-4-architecture-decisions.md` (ADR-007+)
- `documentation/DEPLOYMENT.md` (Docker, Kubernetes, .env-Config)

---

## Timeline

| Milestone | Datum | Phase | REQs |
|---|---|---|---|
| Phase 3 ✅ ABGESCHLOSSEN | 2026-07-02 | 3 | REQ-3045–3064 |
| Sprint 6 START | 2026-07-08 | 4 | REQ-4007, REQ-4008 |
| Sprint 6 DONE | 2026-07-22 | 4 | + 4 Tests |
| Sprint 7 START | 2026-07-22 | 4 | REQ-4009, REQ-4010 |
| Sprint 7 DONE | 2026-08-05 | 4 | + E2E-Tests |
| Sprint 8 START | 2026-08-05 | 4 | REQ-4006 |
| Sprint 8 DONE | 2026-08-26 | 4 | Multi-User-Ready |
| Sprint 9 START | 2026-08-26 | 4 | REQ-4001 (Auth) |
| **Release v1.2.0** | 2026-09-30 | 4 | Enterprise-Ready |

