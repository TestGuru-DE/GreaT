---
name: great-task-intake
description: Use this skill in the G.R.E.A.T. project when the user gives a business-level request, feedback, feature idea, bug report, or change request to the GREAT Orchestrator. It converts non-technical user input into a clear implementation brief with REQ impact, missing questions, affected files, responsible agents, risk, acceptance criteria, and a test-first execution plan.
argument-hint: "<user request, bug, feedback, or feature idea>"
---

# GREAT Task Intake

Use this skill whenever the user talks from a product or user perspective and does not provide implementation details. The user is not expected to program.

## Goal
Turn the user request into a safe, executable brief for the G.R.E.A.T. agent team without inventing requirements or silently changing scope.

## Required context to inspect
Before proposing work, inspect the current project context:

1. `Agenten und basisinfos/requirements_v1.1.md` for existing REQ IDs, status, dependencies, and acceptance criteria.
2. `documentation/project-assessment.md` for current project phase and known limitations.
3. `documentation/decision-log.md` for ADR constraints.
4. `documentation/risk-log.md` for active risks.
5. Relevant `src/`, `tests/`, `documentation/`, and customization files only after the affected area is known.

## Intake workflow

### 1. Restate the user intent
Write a short German summary in user language:

```markdown
## Verstandene Anfrage
[1-3 Saetze]
```

Do not translate the request into code prematurely.

### 2. Requirement mapping
Search for matching REQs semantically and by keywords. Return one of:

- **Existing REQ found:** use the existing REQ ID.
- **Existing REQ needs extension:** propose the extension and ask for confirmation.
- **No REQ found:** draft a new REQ candidate, but do not implement before explicit confirmation unless the change is purely internal cleanup.

Output:

```markdown
## REQ-Abgleich
- Gefundene REQs: REQ-XXXX, ...
- Status: Planned | Approved | In Progress | Implemented | Tested | Released | nicht vorhanden
- Bewertung: verwenden | erweitern | neu anlegen | Rueckfrage erforderlich
```

### 3. Clarify only blockers
Ask at most 3 focused questions, and only if implementation would otherwise require guessing user-visible behavior. Do not ask technical questions the agent team can resolve by code inspection.

### 4. Build an execution brief
Use this exact structure:

```markdown
## Umsetzungsbrief
**Ziel:** ...
**Nicht-Ziel:** ...
**Betroffene REQ-IDs:** ...
**Akzeptanzkriterien:**
- Given ... When ... Then ...
**Betroffene Bereiche:** Backend | Frontend | Kombinatorik | Requirements | Doku | Agenten/Skills
**Primaer-Agent:** @GREAT ...
**Pruefung durch:** @GREAT ...
**Risiken:** ...
**TDD-Start:** Welche Tests muessen zuerst rot sein?
**Definition of Done:** Tests, Coverage, Doku, REQ-Status, ADR/Risk-Update
```

### 5. Route to the right workflow
After intake, trigger or recommend the matching skill:

- Code change: `great-feature-tdd-workflow`
- Pure requirement update: `great-requirements-traceability`
- Algorithmic/combinatorics change: `great-combinatorics-validation` plus TDD workflow
- Architecture-sensitive change: `great-architecture-review`
- Phase/release decision: `great-release-readiness`
- UI/React/Office-like UX: `great-frontend-office-ux`
- Agent/customization cleanup: `great-agent-customization-audit`

## Guardrails

- Never implement without a REQ ID or a documented temporary exception.
- Never assume a missing user decision; ask or create an explicit decision record proposal.
- Keep the response understandable for a non-programmer.
- If the user asks for a quick change, still perform REQ and test impact checks, but keep the explanation short.

