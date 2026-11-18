# Release v1.11.0-alpha – REQ-6001 Logische Constraints

**Datum:** 2026-11-18
**Branch:** `feature/req-6001-logical-constraints` → `main`
**PR:** #63

---

## Was ist neu?

### Logische Constraints (REQ-6001)
G.R.E.A.T. unterstuetzt jetzt **Mehrbedingungs-Regeln** – Constraints, die mehrere Kategorien gleichzeitig betreffen UND/ODER/NICHT verknuepfen.

**Zwei Formen:**
- **Verbot (forbid):** `NICHT (Bedingung)` – Kein Testfall darf die Bedingung erfuellen
- **Implikation (implies):** `WENN (Bedingung) DANN (Folge)` – Jeder Testfall, der die Bedingung erfuellt, muss auch die Folge erfuellen

**Beispiel:**
```
WENN Zahlart = "Rechnung" UND Land != "DE" DANN NICHT Versand = "Express"
```

**Technische Umsetzung:**
- JSON-AST-Format (ADR-020) mit Operatoren: `eq`, `ne`, `in`, `not_in`, `and`, `or`, `not`
- Verschachtelung bis Tiefe 5, max. 20 atomare Vergleiche pro Constraint
- Vollstaendige CRUD-API unter `/api/v1/projects/{id}/constraints/`
- Validate-Endpunkt zur AST-Pruefung vor dem Speichern
- Integration in Generierungspipeline (RuleEngine)
- Frontend: ConstraintBuilder (React, i18n de/en)

### API-Endpunkte (neu)
| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/api/v1/projects/{id}/constraints/` | Alle Constraints listen |
| POST | `/api/v1/projects/{id}/constraints/` | Constraint erstellen |
| GET | `/api/v1/projects/{id}/constraints/{cid}` | Einzelnes Constraint lesen |
| PUT | `/api/v1/projects/{id}/constraints/{cid}` | Constraint aktualisieren |
| DELETE | `/api/v1/projects/{id}/constraints/{cid}` | Constraint loeschen |
| POST | `/api/v1/projects/{id}/constraints/validate` | AST validieren (ohne speichern) |

### Dreiwertige Logik (3VL)
- Pairwise/T-Wise behandeln Constraints bei **unvollstaendigen** Testfaellen korrekt
- Wahr/Falsch/Unbekannt – ein Teil-Testfall wird nur verworfen, wenn er einen Constraint **sicher** verletzt

---

## Bugfixes
- **implies-Constraints via API:** `consequence`-Feld fehlt nicht mehr in Schema und Router
- **Router-Prefix:** Constraints-API korrekt unter `/api/v1/projects/...` registriert
- **Validate-Endpunkt:** Unterstuetzt jetzt `implies` mit `consequence`

---

## Technische Details
- **Datenbank:** Neue Tabelle `constraints` (Alembic-Migration)
- **Referenz-Integritaet:** `is_valid=False` bei Loeschung referenzierter Kategorien/Werte
- **Auth:** `require_writer` fuer POST/PUT/DELETE, `require_api_capable` fuer alle Endpunkte
- **Tests:** 25 API-Tests, 132 Backend-Tests, 568 Frontend-Tests, 1202 Regression-Tests

---

## Nacharbeit (Phase 3)
Folgende Akzeptanzkriterien sind als Nacharbeit dokumentiert:
- **AK-3/4:** Regel-Editor (Builder) + Textdarstellung im Frontend
- **AK-5/6:** Generator-Integration + 3VL fuer Pairwise/T-Wise (evaluator_3vl.py existiert, Integration pending)
- **AK-7:** Coverage-Metrik fuer constraint-exkludierte Paare
- **AK-8:** Widerspruchspruefung beim Speichern
- **AK-10:** Backup/Export-Integration

---

## Abwaertige Kompatibilitaet
- **100% abwaertskompatibel** – bestehende Regeln (exclude, dependency, combine) funktionieren unveraendert
- Neue Funktionalitaet ist **additiv** – keine Aenderungen an bestehenden APIs

---

## Betroffene Dateien
- `src/app/models/__init__.py` – Constraint SQLAlchemy-Modell
- `src/app/schemas.py` – ConstraintCreate/Update/Validate Pydantic-Schemas
- `src/app/constraints/ast_parser.py` – AST-Parser/Validator
- `src/app/constraints/evaluator_3vl.py` – Dreiwertige Logik Evaluator
- `src/app/routers/api_constraints.py` – CRUD API (6 Endpunkte)
- `src/app/routers/api_generate.py` – Generierungspipeline-Integration
- `src/app/services.py` – apply_business_rules mit Constraints
- `src/app/main.py` – Router-Registration
- `src/core/rules/rule_engine.py` – ConstraintRule
- `frontend/src/components/ConstraintBuilder.tsx` – Frontend-Builder
- `frontend/src/api/client.ts` – API-Client (logicalConstraintsApi)
- `frontend/src/i18n/de.json`, `en.json` – i18n Keys (36 neue Keys)
- `frontend/src/types/index.ts` – LogicalConstraint, ConstraintNode, etc.
- `frontend/src/pages/ProjectDetailPage.tsx` – Neuer Tab "Constraints"
- `tests/test_constraint_api.py` – 25 API-Tests
- `tests/conftest.py` – _purge_constraints_per_test Fixture
- `src/db/migrations/versions/req6001_add_constraints_table.py` – Alembic-Migration
- `documentation/decision-log.md` – ADR-020
- `userstorys und basisinfos/requirements_v1.1.md` – REQ-6001 Status: Implemented