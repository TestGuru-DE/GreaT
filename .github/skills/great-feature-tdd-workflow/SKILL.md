---
name: great-feature-tdd-workflow
description: Use this skill in the G.R.E.A.T. project for any feature, bug fix, refactor, API change, frontend change, or behavior change that may require code edits. It enforces REQ traceability, RED-GREEN-REFACTOR, coverage checks, architecture checks, documentation updates, and a final self-review suitable for a non-programming user.
argument-hint: "<REQ-ID or feature/fix description>"
---

# GREAT Feature TDD Workflow

Use this skill for every code-affecting change in G.R.E.A.T. The workflow is mandatory even when the user asks informally.

## Preconditions

1. Identify the REQ ID in `Agenten und basisinfos/requirements_v1.1.md`.
2. If no REQ exists, use `great-requirements-traceability` first.
3. Inspect architecture constraints in `documentation/decision-log.md` and `documentation/architecture/current-architecture.md`.
4. Identify existing tests in `tests/` that cover the affected behavior.

## RED-GREEN-REFACTOR process

### 1. Plan the smallest safe slice
Return a short plan:

```markdown
## TDD-Schnitt
REQ: REQ-XXXX
Aenderung: ...
Test zuerst: tests/test_...
Erwarteter erster Fehler: AssertionError | ImportError | ValidationError | HTTP status mismatch | other
Betroffene Produktivdateien: ...
```

### 2. Write or update tests first
Tests must express user-visible behavior or algorithmic contract. Include `# REQ-XXXX` in or near each new test.

Test naming:

- Backend/API: `tests/test_<feature>.py`
- Combinatorics: `tests/test_<strategy>.py`
- Frontend: use the project test standard once React/TypeScript exists.

### 3. Prove RED
Run the narrowest relevant test command first. Examples:

```bash
python -m pytest tests/test_<feature>.py -v -x
```

On Windows PowerShell if imports need `src`:

```powershell
$env:PYTHONPATH="src"; python -m pytest tests/test_<feature>.py -v -x
```

Record the failing test and the expected reason. If the test unexpectedly passes, stop and improve the test before implementing.

### 4. Implement minimally
Follow the existing architecture:

- Router -> Service -> Repository -> DB; do not skip layers.
- Keep `src/app/main.py` small; do not add business logic there.
- SQLAlchemy ORM only; no raw SQL.
- Type hints for new Python code.
- Logging instead of `print()` in production code.
- No new dependency without checking license and ADR impact.

### 5. Prove GREEN
Run the same narrow test. Then run the relevant regression set.

```bash
python -m pytest tests/ -v
python -m pytest --cov=src --cov-report=term-missing --cov-branch tests/
```

If full regression is slow or unavailable, state exactly what was run and what remains unverified.

### 6. Refactor safely
Only refactor after tests are green. Re-run the relevant tests after refactoring.

### 7. Update traceability and docs
Update as applicable:

- `Agenten und basisinfos/requirements_v1.1.md` status and traceability.
- `documentation/decision-log.md` if architecture decision changed.
- `documentation/risk-log.md` if a risk is introduced, reduced, or closed.
- `CHANGELOG.md` or project documentation for user-visible changes.

## Final response format

```markdown
## Ergebnis
- Umsetzung: erledigt | teilweise erledigt | blockiert
- REQ: REQ-XXXX
- Geaenderte Bereiche: ...

## Nachweis
- RED-Test: [Befehl + Ergebnis]
- GREEN-Test: [Befehl + Ergebnis]
- Regression/Coverage: [Befehl + Ergebnis]

## Kritische Selbstpruefung
- Architektur: bestanden | Befund
- Security: bestanden | Befund
- UX/Benutzerwirkung: bestanden | Befund
- Doku/Traceability: bestanden | Befund

## Naechster sinnvoller Schritt
[genau ein Vorschlag]
```

## Stop conditions

Stop and ask or escalate if:

- No REQ ID can be found or created safely.
- Acceptance criteria conflict with existing requirements.
- Tests cannot be made meaningful.
- A required command cannot run because dependencies or files are missing.
- A change requires an ADR but none exists.

