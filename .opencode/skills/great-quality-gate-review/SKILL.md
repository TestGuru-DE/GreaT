---
name: great-quality-gate-review
description: Use this skill in the G.R.E.A.T. project before declaring work done, after code changes, before commits/PRs/releases, or when the user asks whether the agents have critically checked the code. It runs or guides tests, coverage, architecture, security, requirements traceability, documentation, and regression self-review.
argument-hint: "<changed feature, REQ-ID, branch, or files>"
---

# GREAT Quality Gate Review

Use this skill whenever work might be considered finished. The goal is to prevent the agent from saying "fertig" without evidence.

## Mandatory evidence

Collect evidence for:

1. Tests: relevant narrow tests and regression tests.
2. Coverage: statement and branch coverage for changed code.
3. Architecture: no business logic in routers, no raw SQL, no circular imports, no oversized `main.py` changes.
4. Requirements: every code/test change maps to `REQ-XXXX`.
5. Security: no secrets, unsafe CORS, raw SQL, debug production settings, or unvalidated input.
6. Documentation: user-visible behavior and requirements status updated.
7. Repository hygiene: no generated caches, DB files, `__pycache__`, `.pytest_cache`, or accidental binaries committed.

## Optional helper scripts

If appropriate, the agent may use one of these scripts from the skill directory:

- [PowerShell quality gate](./scripts/run_quality_gate.ps1)
- [Bash quality gate](./scripts/run_quality_gate.sh)

The scripts are helpers, not substitutes for reasoning. If they fail due to missing dependencies, inspect the failure and report it.

## Review checklist

Use the detailed checklist in [review-checklist.md](./references/review-checklist.md) when reviewing changed files.

## Procedure

### 1. Identify scope
List changed files, affected REQs, and affected subsystems.

### 2. Run checks
Prefer actual commands over assumptions:

```bash
python -m pytest tests/ -v
python -m pytest --cov=src --cov-report=term-missing --cov-branch tests/
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH="src"; python -m pytest --cov=src --cov-report=term-missing --cov-branch tests/
```

Also run targeted checks for frontend tooling once React/TypeScript exists, such as typecheck, lint, and test commands defined in `package.json`.

### 3. Inspect failures critically
Do not classify a failure as "pre-existing" unless it is documented in `documentation/testing/current-test-state.md` or the task brief explicitly says so.

### 4. Decide gate status
Return one of:

- **PASS:** all required checks ran and passed.
- **CONDITIONAL PASS:** non-blocking documented issue remains, with owner and follow-up.
- **FAIL:** tests, coverage, architecture, security, traceability, or docs are insufficient.
- **NOT VERIFIED:** tool/dependency/environment prevented verification.

## Output format

```markdown
# Quality Gate – G.R.E.A.T.

## Status
PASS | CONDITIONAL PASS | FAIL | NOT VERIFIED

## Scope
- REQs: ...
- Dateien: ...

## Ausgefuehrte Pruefungen
| Pruefung | Befehl/Quelle | Ergebnis |
|---|---|---|
| Tests | ... | ... |
| Coverage | ... | ... |
| Architektur | Review | ... |
| Security | Review | ... |
| Traceability | Review | ... |
| Doku | Review | ... |

## Blocker
- ...

## Kritische Befunde
- ...

## Empfehlung
[freigeben | nacharbeiten | Rueckfrage an Nutzer | Eskalation an Agent]
```
