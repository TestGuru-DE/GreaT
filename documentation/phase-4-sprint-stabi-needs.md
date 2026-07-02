# Technische Schulden & Stabilisierungs-Sprint Kandidaten

## Analysiert am: 2026-07-02

### Methodik
Jede Schuld bewertet nach **Impact** (Hoch/Mittel/Niedrig), **Aufwand** (Hoch/Mittel/Niedrig) und **Kategorie** (Architektur / Sicherheit / Testing / Performance / DX / Wartung).

---

## Kategorie: Architektur

### 1. ❌ GREAT_PORT Umgebungsvariable fehlt
- **Impact:** Mittel  
- **Aufwand:** Niedrig  
- **Status:** Blocking für Docker-Deployment  
- **Beschreibung:** Port ist hardcoded (8000). REQ-4007 verlangt konfigurierbar via GREAT_PORT env.  
- **Lösung:** main.py: `PORT = os.getenv("GREAT_PORT", "8000")`  
- **Tests:** Start mit `GREAT_PORT=9000` → API auf Port 9000 erreichbar  
- **Abhängigkeiten:** Keine  

### 2. ❌ Health-Check Endpoint /health fehlt
- **Impact:** Mittel  
- **Aufwand:** Niedrig  
- **Status:** Optional für Monitoring  
- **Beschreibung:** REQ-4008 verlangt `/health` → `{"status": "ok", "db": "connected", "version": "1.1.0"}`  
- **Lösung:** Router `api_health.py` mit DB-Ping  
- **Tests:** GET /health → 200 mit JSON  
- **Abhängigkeiten:** Keine  

### 3. ⚠️ Strukturiertes Logging (nur print + uvicorn)
- **Impact:** Mittel  
- **Aufwand:** Mittel  
- **Status:** Development OK, Production problematisch  
- **Beschreibung:** REQ-4009 verlangt strukturiertes Logging (JSON, timestamp, level). Aktuell nur `print()` + uvicorn stdout.  
- **Lösung:** `structlog` oder `python-json-logger` für JSON-Output + Log-Rotation  
- **Tests:** Start mit LOG_LEVEL=DEBUG → JSON-Logs in stdout/file  
- **Dependencies:** structlog ≥24.1 (MIT-kompatibel)  
- **Abhängigkeiten:** Keine (parallel zu anderen Schulden)  

### 4. ⚠️ requirements.txt: Versionspinning unvollständig
- **Impact:** Mittel  
- **Aufwand:** Niedrig  
- **Status:** Versionskonflikt-Risiko  
- **Beschreibung:** requests, httpx, python-multipart haben keine Versions-Constraints.  
- **IST:** `requests` (keine Version) → ggf. `requests==2.32.0`  
- **Lösung:** Alle Packages mit Lock-Version pinnen oder `requirements-lock.txt` generieren  
- **Tests:** pip install mit exakten Versionen → Reproducible Builds  
- **Abhängigkeiten:** Keine  

### 5. ❓ Services.py & api_generate.py: Datei-Größe im Grenzbereich
- **Impact:** Niedrig (funktioniert noch)  
- **Aufwand:** Hoch (Refactoring)  
- **Status:** Wartbarkeit-Schuld  
- **Beschreibung:** services.py 423 Zeilen, api_generate.py 376 Zeilen. Single-Responsibility-Prinzip wird strapaziert.  
- **Ideal:** services.py → services_generation.py, services_project.py, services_dataclass.py  
- **Lösung:** Service-Layer-Refactoring (nicht dringend, eher Sprint 7 nach Stabi)  
- **Tests:** Bestehende Tests bleiben grün; neue Tests für neue Module  
- **Abhängigkeiten:** Keine  

### 6. ❌ Keine Dependency Injection für DB-Sessions
- **Impact:** Niedrig (FastAPI TestClient absorbiert das)  
- **Aufwand:** Mittel  
- **Status:** Tech Debt  
- **Beschreibung:** DB-Session wird global in main.py erzeugt, statt dependency-injection in Router-Funktionen.  
- **Lösung:** FastAPI `Depends(get_db)` Pattern in allen Routern  
- **Tests:** Existing tests müssen nicht ändern (TestClient greift DB ab)  
- **Abhängigkeiten:** Keine  

---

## Kategorie: Sicherheit

### 7. ⚠️ Keine Input-Validierung auf Nutzer-Texte (Name, Beschreibung)
- **Impact:** Mittel (XSS-Risk in UI, aber React escapet das)  
- **Aufwand:** Mittel  
- **Status:** Partially mitigated durch React-Rendering  
- **Beschreibung:** Pydantic-Schemas (ProjectCreate, CategoryUpdate) erlauben jede Zeichenkette. Keine Längenprüfung, keine Sonderzeichen-Filterung.  
- **Lösung:** Pydantic Field-Constraints: `name: str = Field(..., min_length=1, max_length=255)`  
- **Tests:** POST /projects mit name="" → 422 Validation Error  
- **Abhängigkeiten:** Keine (Pydantic v2 hat das built-in)  

### 8. ❌ CORS-Konfiguration zu offen (*)
- **Impact:** Mittel  
- **Aufwand:** Niedrig  
- **Status:** Aktuell lokale-only, OK. Aber vor Multi-User-Release ändern.  
- **Beschreibung:** main.py: `CORSMiddleware(..., allow_origins=["*"])` erlaubt alle Origins.  
- **Lösung:** Vor REQ-4006 (Multi-User): allow_origins auf Liste (z.B. ["http://localhost:5173", "https://great.example.com"])  
- **Tests:** Kein Test nötig (Config-Change)  
- **Abhängigkeiten:** REQ-4006  

### 9. ❌ Keine Rate-Limiting
- **Impact:** Niedrig (nicht Single-User-relevant)  
- **Aufwand:** Mittel  
- **Status:** Optional bis Multi-User  
- **Beschreibung:** API-Endpunkte haben keine Drosselung gegen DoS/Brute Force.  
- **Lösung:** `slowapi` Middleware für FastAPI (optional, nicht für Phase 4 Sprint 6 geplant)  
- **Tests:** Parallel-Requests → 429 Too Many Requests (später)  
- **Abhängigkeiten:** REQ-4006 (Multi-User trigger)  

### 10. ❌ SQL-Injection durch Raw-SQL (gering, aber prüfen)
- **Impact:** Niedrig (ORM schützt durch parametrisierte Queries)  
- **Aufwand:** Niedrig (nur Prüfung nötig)  
- **Status:** Sauber (SQLAlchemy ORM)  
- **Beschreibung:** Alle Queries durch SQLAlchemy ORM. Kein Raw SQL sichtbar.  
- **Lösung:** Code-Review bestätigt: Keine Raw-SQL. Keine Action nötig.  
- **Tests:** Grep für "raw_sql\|execute(" in routers + services → Null-Fund bestätigt Sicherheit  

---

## Kategorie: Testing

### 11. ❌ Keine E2E-Tests (Playwright geplant REQ-4010)
- **Impact:** Hoch  
- **Aufwand:** Hoch  
- **Status:** Blocking für QA-Freigabe  
- **Beschreibung:** 263 Backend-Tests vorhanden, ~25 Frontend-Component-Tests. Keine End-to-End-Tests (User-Workflows über Browser).  
- **Lösung:** Playwright E2E-Suite: "Create project → Add categories → Generate → Export CSV"  
- **Tests:** REQ-4010 Test-Suite (Sprint 7)  
- **Abhängigkeiten:** Keine  

### 12. ⚠️ Frontend-Test-Coverage unbekannt
- **Impact:** Mittel  
- **Aufwand:** Mittel  
- **Status:** Vitest installiert, aber Coverage nicht gemessen  
- **Beschreibung:** frontend/src/components/ haben ~25 Unit-Tests. Keine Coverage-Reports.  
- **Lösung:** Vitest + @vitest/coverage in npm scripts: `"test:cov": "vitest --coverage"`  
- **Tests:** Lokal: npm run test:cov → HTML-Report in coverage/  
- **Abhängigkeiten:** Keine  

### 13. ⚠️ Fehlende Integration-Tests (API + DB zusammen)
- **Impact:** Mittel  
- **Aufwand:** Mittel  
- **Status:** Teilweise durch Backend-Tests abgedeckt  
- **Beschreibung:** Backend-Tests nutzen FastAPI TestClient + :memory: SQLite. Frontend-Tests mocken API. Keine wahren End-to-End-Tests ohne Mock.  
- **Lösung:** REQ-4010 E2E-Tests (Playwright) + optionale Integration-Test-Suite  
- **Tests:** "Create project via API → Verify in DB → Read via API → Verify in React UI"  
- **Abhängigkeiten:** Keine  

### 14. ⚠️ Kombinatorik-Algorithmen: Constraint-Engine ungetestet für alle Strategien
- **Impact:** Niedrig (core 3 Strategien getestet: Pairwise, Each Choice, All Combinations)  
- **Aufwand:** Hoch  
- **Status:** Advanced (T-Wise, MCDC, Risk-Based, Linear) = New Features  
- **Beschreibung:** REQ-3039–3044 (Sprint 5) haben Tests. Aber ältere MCDC, T-Wise, Risk-Based brauchen Verifizierung gegen Constraint-Engine.  
- **Lösung:** Phase-3-Sprint-5 bereits abgeschlossen. Constraint-Tests in place. ✅ OK für Phase 4.  
- **Tests:** test_req3040_constraint_aware.py, test_req3044_mcdc.py ✅  

---

## Kategorie: Performance

### 15. ❌ Keine DB-Indizes definiert (außer PK)
- **Impact:** Niedrig (SQLite + Testdatengröße O(1000) → Queries < 100ms)  
- **Aufwand:** Niedrig  
- **Status:** Erst relevant bei N > 100.000 Records  
- **Beschreibung:** Modelle (models.py) haben PK-Index. Keine Indizes auf project_id, category_id, value_id in FK-Relationen.  
- **Lösung:** SQLAlchemy Index auf FK-Spalten hinzufügen oder Alembic-Migration  
- **Tests:** EXPLAIN QUERY PLAN → Verifies Index Hits  
- **Abhängigkeiten:** Keine (PostgreSQL-relevant für REQ-4006)  

### 16. ⚠️ Pairwise-Algorithmus: Unter Last-Test fehlt
- **Impact:** Niedrig  
- **Aufwand:** Mittel  
- **Status:** Funktioniert, aber keine Stress-Metriken  
- **Beschreibung:** Pairwise funktioniert bei Test-Projekten. Keine Benchmarks für |Categories| = 100, |Values/Cat| = 1000.  
- **Lösung:** Performance-Test mit `pytest-benchmark`: Generate Pairwise für großes Projekt < 5s  
- **Tests:** test_pairwise_performance.py (optional, nicht Critical)  
- **Abhängigkeiten:** Keine  

### 17. ⚠️ Frontend-Bundle-Größe: 280 KB (akzeptabel, aber wächst)
- **Impact:** Niedrig  
- **Aufwand:** Niedrig  
- **Status:** Aktuell OK  
- **Beschreibung:** React + Tailwind + Zustand + Decimal.js + Theme-System = ~280 KB. Ziel: < 300 KB.  
- **Lösung:** Tree-Shaking verified. Optional: Code Splitting nach Seiten (später).  
- **Tests:** vite build → Output: ~280 KB  

---

## Kategorie: Developer Experience

### 18. ❌ Keine .env-Unterstützung
- **Impact:** Hoch (DX-Blocker für lokale Entwicklung)  
- **Aufwand:** Niedrig  
- **Status:** Blocking für GREAT_PORT + Multi-User-Config  
- **Beschreibung:** main.py hat hardcoded PORT=8000, DB="tanos.db". Keine python-dotenv Integration.  
- **Lösung:** python-dotenv zu requirements.txt, load_dotenv() in main.py  
- **Example .env:**  
  ```
  GREAT_PORT=8000
  GREAT_DB=tanos.db
  GREAT_LOG_LEVEL=INFO
  GREAT_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
  ```
- **Tests:** Start mit `.env` → Config übernommen, Start ohne .env → Defaults  

### 19. ❌ Keine pre-commit Hooks
- **Impact:** Niedrig (Qualität)  
- **Aufwand:** Niedrig  
- **Status:** Optional  
- **Beschreibung:** Black, isort, flake8, mypy könnten pre-commit laufen.  
- **Lösung:** `.pre-commit-config.yaml` optional für Phase 4 Sprint 8  
- **Tests:** Keine  

### 20. ⚠️ Dokumentation: Keine API-Dokumentation im README
- **Impact:** Mittel (DX)  
- **Aufwand:** Mittel  
- **Status:** FastAPI /docs (Swagger) vorhanden, aber README verlinkt nicht  
- **Beschreibung:** README.md erwähnt API nicht. Keine Beispiel-cURL-Requests.  
- **Lösung:** README-Sektion "API Reference" + Link zu /docs  
- **Tests:** README existiert und hat API-Sektion  

---

## Kategorie: Wartung

### 21. ❌ Alembic-Migrationen: Baseline etabliert, aber Prozess nicht dokumentiert
- **Impact:** Mittel  
- **Aufwand:** Niedrig  
- **Status:** Functional, aber Manual  
- **Beschreibung:** Alembic vorhanden (0001_initial.py). Prozess für zukünftige Migrationen nicht dokumentiert.  
- **Lösung:** DEVELOPMENT.md: "alembic upgrade head" + "alembic revision --autogenerate -m ..."  
- **Tests:** alembic current → Migration Version bestätigt  

### 22. ⚠️ archive/ Verzeichnis wächst ohne Cleanup-Prozess
- **Impact:** Niedrig (Git-Speicher OK, aber Repo bloat)  
- **Aufwand:** Niedrig  
- **Status:** Informativ  
- **Beschreibung:** archive/ hat mehrere YYYY-MM-DD/Unterordner. Keine Lösch-Policy.  
- **Lösung:** Dokumentieren: Archive >= 6 Monaten → separate Branch/Tag  
- **Tests:** Keine  

### 23. ❌ Keine Health-Check-Startup-Validierung
- **Impact:** Niedrig  
- **Aufwand:** Niedrig  
- **Status:** Start-Fehler nicht erkannt  
- **Beschreibung:** Start.bat/Start.sh starten Backend/Frontend ohne Check. Fehler = silent failure.  
- **Lösung:** Start.bat sollte prüfen: Port erreichbar → uvicorn läuft, vor Frontend-Start  
- **Tests:** Start.bat mit ungültigem PORT → Error mit Msg "Port X in use"  

### 24. ⚠️ Logging-Infrastruktur: Keine Log-Rotation / Datei-Persistenz
- **Impact:** Mittel (Production)  
- **Aufwand:** Niedrig  
- **Status:** Logs nur in stdout (OK local, nicht für Server)  
- **Beschreibung:** Logs gehen an stdout. Bei längerer Nutzung keine Persistenz/Rotation.  
- **Lösung:** Python logging.handlers.RotatingFileHandler (Sprint 7 mit REQ-4009)  
- **Tests:** Keine  

---

## Kategorie: Abhängigkeiten & Lizenzen

### 25. ✅ Lizenz-Status: MIT
- **Impact:** ✅ Kein Action  
- **Status:** LICENSE vorhanden, ADR-006 akzeptiert  
- **Alle Dependencies MIT/Apache/BSD-kompatibel ✅**

---

## TOP-5-Schulden nach Impact + Aufwand (Prio für Sprint 6)

| Rank | Schuld | Impact | Aufwand | REQ-ID | Status |
|---|---|---|---|---|---|
| 1 | GREAT_PORT Umgebungsvariable | Hoch | Niedrig | REQ-4007 | **SOFORT** |
| 2 | .env-Unterstützung | Hoch | Niedrig | Part of REQ-4007 | **SOFORT** |
| 3 | Health-Check /health | Mittel | Niedrig | REQ-4008 | Sprint 6 |
| 4 | Strukturiertes Logging | Mittel | Mittel | REQ-4009 | Sprint 7 |
| 5 | E2E-Tests (Playwright) | Hoch | Hoch | REQ-4010 | Sprint 7 |

**Sprint 6 Priorisierung (2 Wochen):**
- REQ-4007: GREAT_PORT + .env → done in 1-2 Tage
- REQ-4008: Health-Check → done in 1-2 Tage
- Remaining capacity: Services-Refactoring oder Input-Validierung erweitern

**Sprint 7 Priorisierung (2 Wochen):**
- REQ-4009: Strukturiertes Logging
- REQ-4010: E2E-Tests (Playwright)

---

## Nicht-Schulden (OK zu belassen)

- ✅ SQLAlchemy ORM: Sauber, SQL-Injection-sicher
- ✅ Pairwise-Algorithmus: Mathematisch verifiziert
- ✅ Frontend-Bundle: 280 KB ist OK
- ✅ Test-Coverage: 263 Tests = solid Basis
- ✅ React/TypeScript/Vite: Modern, wartbar
- ✅ HTMX/Jinja2: Bleibt zur Archivierung (Phase 3 Sprint 4 Plan)

