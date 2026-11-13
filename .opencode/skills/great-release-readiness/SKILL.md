---
name: great-release-readiness
description: Use this skill in the G.R.E.A.T. project for sprint close, phase transition, release readiness, release blocking, changelog preparation, risk review, documentation completion, or when the user asks whether the project is ready for the next phase. It creates a formal Go/No-Go decision.
argument-hint: "<phase, sprint, release, or scope>"
---

# GREAT Release Readiness

Use this skill when deciding whether a sprint, phase, or release can be closed.

## Inputs

Identify:

- Phase/sprint/release scope.
- Included REQ IDs.
- Changes since last release decision.
- Known blockers, risks, and deferred items.

## Required sources

Inspect:

1. `Agenten und basisinfos/requirements_v1.1.md`
2. `documentation/project-assessment.md`
3. `documentation/risk-log.md`
4. `documentation/decision-log.md`
5. `documentation/testing/current-test-state.md`
6. `CHANGELOG.md` and README/user docs if present
7. Test and coverage output from `great-quality-gate-review`

## Go/No-Go criteria

A release or phase transition is **NO-GO** if any of these apply:

- Any included Must REQ is not Tested or explicitly deferred.
- Regression tests failed or were not run without documented reason.
- Coverage gate for changed code is not satisfied.
- Open high-risk issue lacks mitigation.
- Required ADR is missing.
- User-visible change lacks documentation.
- Requirements status is inconsistent with implemented code.

## Procedure

### 1. Build scope table

```markdown
| REQ | Titel | Status | Testnachweis | Doku | Entscheidung |
|---|---|---|---|---|---|
```

### 2. Review risks and ADRs

```markdown
| ID | Thema | Status | Release-Relevanz | Aktion |
|---|---|---|---|---|
```

### 3. Confirm quality gate

Summarize the latest quality-gate evidence. If none exists, run or request `great-quality-gate-review`.

### 4. Decide

Return one:

- **GO** – release/phase can proceed.
- **GO with explicit deferrals** – proceed with listed and accepted deferrals.
- **NO-GO** – blockers must be resolved first.
- **NOT ENOUGH EVIDENCE** – cannot decide until checks run.

## Output format

```markdown
# Release Readiness – G.R.E.A.T.

## Entscheidung
GO | GO mit Deferrals | NO-GO | NOT ENOUGH EVIDENCE

## Begruendung
...

## Scope
...

## Quality Gate
...

## Blocker
- ...

## Deferrals
- ...

## Naechste Aktion
[genau eine konkrete Aktion]
```

