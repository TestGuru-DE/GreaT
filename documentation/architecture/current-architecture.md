# Current Architecture – G.R.E.A.T.
Version: 2.0
Phase: 1 Sprint 3 – Stand nach Refactoring
Erstellt: 2026-06-10 | Aktualisiert: 2026-06-23
Erstellt von: Chief Architect Agent

---

## 1. Ist-Architektur

### 1.1 Schichtmodell (aktuell)

```
┌─────────────────────────────────────────────────┐
│  Browser (HTML/HTMX/Jinja2-Templates)           │  ← Präsentation
│  SortableJS (Drag & Drop)                       │
└─────────────────────────┬───────────────────────┘
                          │ HTTP (HTMX-Requests / REST)
┌─────────────────────────▼───────────────────────┐
│  FastAPI App (src/app/main.py)                  │  ← Anwendungsschicht
│  - API-Endpunkte (REST JSON)                    │    (MONOLITHISCH)
│  - UI-Routen (HTMX-Rendering)                  │
│  - Migrations-Logik                             │
│  - Geschäftslogik (gemischt!)                  │
└──────────┬───────────────────┬──────────────────┘
           │                   │
┌──────────▼───┐    ┌──────────▼───────────────────┐
│ SQLAlchemy   │    │  Kombinatorik-Engine         │  ← Domänenschicht
│ ORM          │    │  src/combinatorics/          │    (sauber)
│ Models       │    │  - all_combinations          │
└──────────┬───┘    │  - each_choice               │
           │        │  - orthogonal (pairwise)     │
┌──────────▼───┐    └──────────────────────────────┘
│ SQLite DB    │    ┌──────────────────────────────┐
│ great.db     │    │  IO-Handler                  │
└──────────────┘    │  src/io_handlers/csv_handler │
                    └──────────────────────────────┘
```

### 1.2 Technologie-Stack (Ist)

| Schicht | Technologie | Version |
|---|---|---|
| Frontend | Jinja2 Templates + HTMX | Jinja2 3.x |
| Frontend JavaScript | SortableJS | CDN |
| Backend Framework | FastAPI | ~0.100+ |
| Backend Sprache | Python | 3.10+ |
| ORM | SQLAlchemy | ~2.x |
| Datenbank | SQLite | via Python stdlib |
| Testframework | pytest + httpx | 7.4+ |
| Datenverarbeitung | pandas | 2.1+ |
| Excel | openpyxl | 3.1+ |

---

## 2. Zielarchitektur (laut SYSTEM_v1.0.md)

```
┌─────────────────────────────────────────────────┐
│  React + TypeScript (SPA)                       │  ← Frontend
│  - Zweispaltig (Baumansicht + Tabelle)          │
│  - Office-ähnliche Bedienung (Kontextmenüs)    │
│  - CTRL+C/V/X/Z/Y, Shortcuts                   │
└─────────────────────────┬───────────────────────┘
                          │ REST API / WebSocket
┌─────────────────────────▼───────────────────────┐
│  ASP.NET Core Web API                           │  ← Backend
│  - Clean Architecture                           │
│  - DDD                                          │
│  - CQRS optional                                │
└──────────┬───────────────────┬──────────────────┘
           │                   │
    ┌──────▼─────┐    ┌────────▼──────────────────┐
    │ SQLite     │    │  Kombinatorik-Engine       │
    │ (lokal)    │    │  (portiert oder neu)       │
    └────────────┘    └───────────────────────────┘
```

**ADR-Hinweis:** Abweichung von der Zielarchitektur (Python/FastAPI statt ASP.NET Core) erfordert
ein Architecture Decision Record (ADR-001) – siehe decision-log.md.

---

## 3. Datenbankschema (Ist)

```
projects
  id | name | created_at
    │
    ├── categories
    │     id | project_id | name | order_index
    │       │
    │       └── values
    │             id | category_id | value | risk_weight | allowed | vtype | order_index
    │
    ├── generations
    │     id | project_id | strategy | created_at | coverage_meta
    │       │
    │       └── testcases
    │             id | generation_id | name
    │               │
    │               └── testcase_values
    │                     id | testcase_id | category_id | value
    │
    └── rules
          id | project_id | type | if_category_id | if_value
          then_category_id | then_value | then_values_json
```

**Bewertung:**
- ✅ Vollständiges Domänenmodell vorhanden
- ✅ CASCADE-Deletes korrekt gesetzt
- ⚠️ Keine DB-Migration (nur SQL ALTER TABLE inline in main.py)
- ⚠️ `rules.type` unterstützt nur `dependency` – `forbidden` und `combine` fehlen
- ⚠️ Keine Datenbankversion/Schema-Versionierung

---

## 4. API-Endpunkte (Ist-Stand)

### REST JSON API
| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | /projects | Alle Projekte |
| POST | /projects | Projekt anlegen |
| DELETE | /projects/{id} | Projekt löschen |
| GET | /projects/{id}/categories | Kategorien |
| POST | /projects/{id}/categories | Kategorie anlegen |
| PUT | /categories/{id} | Kategorie umbenennen |
| DELETE | /categories/{id} | Kategorie löschen |
| GET | /categories/{id}/values | Werte einer Kategorie |
| POST | /categories/{id}/values | Wert anlegen |
| PUT | /values/{id} | Wert bearbeiten |
| DELETE | /values/{id} | Wert löschen |
| POST | /projects/{id}/generate | Testfälle generieren |
| GET | /projects/{id}/generations | Generierungen |
| GET | /generations/{id}/testcases | Testfälle |
| GET/POST | /rules | Regeln verwalten |
| GET | /export/csv/{id} | CSV Export |
| POST | /import/csv/{id} | CSV Import |

### UI-Routen (HTMX/Jinja2)
| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | /ui/projects | Projektliste |
| GET | /ui/projects/{id}/data | Projektkonfiguration |
| GET | /ui/generate | Generierungs-UI |
| POST | /ui/... | HTMX Partial Updates |

---

## 5. Architektur-Bewertung

### 5.1 Stärken
- ✅ **Kombinatorik-Kern gut isoliert** – `src/combinatorics/` ist unabhängig und testbar
- ✅ **ORM-Modelle sauber** – vollständiges Domänenmodell
- ✅ **CSV-Handler vollständig** – mit Tests und Roundtrip-Validierung
- ✅ **HTMX-UI funktioniert** – pragmatische Lösung für MVP

### 5.2 Schwächen
- ❌ **Monolithischer main.py** – API, Geschäftslogik, UI-Rendering vermischt (~56KB)
- ❌ **Keine Service-Schicht** – direkte DB-Zugriffe in Route-Handlern
- ❌ **Keine Fehlerbehandlung** – kaum HTTP-Fehlercodes, keine Exception-Handler
- ❌ **Kein Migrations-Framework** – manuelle ALTER TABLE Statements
- ❌ **Zwei parallele Backends** – `src/app/` und `src/backend/` redundant
- ❌ **Keine Authentifizierung** – alle Endpunkte öffentlich (für Team-Nutzung kritisch)
- ❌ **Frontend nicht zukunftsfähig** – Jinja2/HTMX vs. Ziel React/TypeScript

### 5.3 Modularität
| Bewertung | Note |
|---|---|
| Kombinatorik-Schicht | ⭐⭐⭐⭐ gut isoliert |
| Datenschicht | ⭐⭐⭐ funktional, kein Migration-Framework |
| API-Schicht | ⭐⭐ monolithisch |
| UI-Schicht | ⭐⭐ funktional aber nicht zukunftsfähig |
| Testabdeckung | ⭐⭐⭐ vorhanden, aber Lücken |

---

## 6. Erweiterbarkeit

### 6.1 Kurz- bis mittelfristig (v1.x – Python/FastAPI)
- Aufsplittung von `main.py` in Router-Module
- Einführung Alembic für DB-Migration
- Service-Layer einführen
- Fehlende Kombinatorik-Strategien ergänzen
- Fehlende IO-Handler (JSON, Excel, XML)

### 6.2 Langfristig (v2.x – Zielarchitektur)
- Frontend-Migration: Jinja2/HTMX → React/TypeScript
- Backend-Migration: FastAPI → ASP.NET Core (falls ADR bestätigt)
- oder: ADR entscheidet Python beizubehalten (FastAPI + React)
- KI-Integration vorbereiten (Ollama, LLM-Provider-Abstraktion)

---

## 7. Technische Schulden

| ID | Beschreibung | Priorität | Aufwand |
|---|---|---|---|
| DEBT-001 | main.py aufteilen in Router-Module | Hoch | M |
| DEBT-002 | Alembic Migration einführen | Hoch | S |
| DEBT-003 | Service-Layer einführen | Hoch | L |
| DEBT-004 | src/backend/ archivieren | ~~Mittel~~ | ~~XS~~ | *(erledigt 2026-11-17)*
| DEBT-005 | Error Handling standardisieren | Hoch | M |
| DEBT-006 | Fehlende Kombinatorik (5 Strategien) | Hoch | XL |
| DEBT-007 | Fehlende IO-Handler (JSON/Excel/XML) | Mittel | M |
| DEBT-008 | Keine Authentifizierung | Hoch | L |
| DEBT-009 | requirements.txt ohne Versionspinning | Mittel | XS |
| DEBT-010 | Jinja2-Templates ohne Komponentisierung | Niedrig | M |
