---
name: great-architecture-review
description: Use this skill in the G.R.E.A.T. project for architecture-sensitive changes, ADR decisions, backend structure, database/migration changes, dependency choices, API design, refactoring, or when a code change may violate the project architecture. It produces an actionable architecture review and ADR recommendation.
argument-hint: "<change, design question, dependency, or files>"
---

# GREAT Architecture Review

Use this skill before implementing structural changes and after implementation to verify architecture conformance.

## Required context

Inspect:

1. `documentation/decision-log.md` for accepted ADRs.
2. `documentation/architecture/current-architecture.md` for current target structure.
3. `documentation/risk-log.md` for known technical risks.
4. Relevant code under `src/` and tests under `tests/`.

## Architecture rules

- FastAPI routers must not contain business logic.
- Flow is Router -> Service -> Repository -> DB.
- SQLAlchemy ORM only; no raw SQL.
- Migrations belong under `src/db/migrations/` or the project-approved Alembic structure.
- `src/app/main.py` stays a thin entry point.
- No circular imports.
- New strategic dependencies require license and ADR review.
- Code identifiers are English; documentation is German.

## ADR decision test

Create or update an ADR if the change:

- Introduces or removes a framework, database, build tool, or major library.
- Changes module boundaries or layering.
- Changes persistence, migration, authentication, authorization, or deployment strategy.
- Establishes a pattern that future features must follow.
- Accepts a technical risk or intentionally deviates from an existing rule.

Do not create ADRs for small local implementation details.

## Review workflow

### 1. Map the change

```markdown
## Architektur-Impact
- Aenderung: ...
- Betroffene Module: ...
- Betroffene ADRs: ...
- Betroffene Risiken: ...
```

### 2. Check conformance

Use this table:

```markdown
| Regel | Status | Befund |
|---|---|---|
| Router ohne Businesslogik | PASS/FAIL/N/A | ... |
| Layering eingehalten | PASS/FAIL/N/A | ... |
| Kein Raw SQL | PASS/FAIL/N/A | ... |
| Migration/DB sauber | PASS/FAIL/N/A | ... |
| main.py bleibt schlank | PASS/FAIL/N/A | ... |
| Keine zirkulaeren Imports | PASS/FAIL/N/A | ... |
| Dependency/License ok | PASS/FAIL/N/A | ... |
```

### 3. Decide

Return one architecture decision:

- **Approved** – implementation can proceed.
- **Approved with constraints** – proceed only with listed constraints.
- **Needs ADR** – draft ADR before code changes.
- **Rejected** – violates architecture; provide safer alternative.

## ADR mini-template

```markdown
## ADR-XXX – [Titel]
**Status:** Proposed
**Datum:** YYYY-MM-DD
**Kontext:** ...
**Entscheidung:** ...
**Alternativen:**
1. ...
2. ...
**Konsequenzen:** ...
**Betroffene REQs:** REQ-...
```

