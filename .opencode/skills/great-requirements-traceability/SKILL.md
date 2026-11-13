---
name: great-requirements-traceability
description: Use this skill in the G.R.E.A.T. project when creating, changing, validating, or mapping requirements, REQ IDs, user stories, acceptance criteria, traceability, and requirement status. It prevents duplicate REQs and keeps requirements aligned with tests, code, architecture decisions, and user-visible behavior.
argument-hint: "<feature, user story, REQ-ID, or change request>"
---

# GREAT Requirements Traceability

Use this skill before implementation if no clear REQ exists, and after implementation to update traceability.

## Source of truth

`Agenten und basisinfos/requirements_v1.1.md` is the active requirements source unless the project explicitly supersedes it.

## Workflow

### 1. Find existing requirements first
Search by:

- REQ ID if provided.
- User-facing terms from the request.
- Related feature area, API, UI element, combinatorics strategy, or data object.
- Acceptance criteria and status.

Never create a new REQ before checking for semantic duplicates.

### 2. Classify the request
Return exactly one classification:

- **Use existing REQ** – implementation can proceed with that ID.
- **Extend existing REQ** – propose exact changes and ask for confirmation.
- **Create new REQ** – draft it and ask for confirmation.
- **Reject/clarify** – the request conflicts with existing requirements or lacks user-level intent.

### 3. Draft or update in a consistent format
Use this structure when creating or extending requirements:

```markdown
## REQ-XXXX – [Titel]
**Status:** Planned | Approved | In Progress | Implemented | Tested | Released | Deprecated
**Prioritaet:** Must | Should | Could
**Phase/Sprint:** Phase X / Sprint Y
**User Story:** Als <Rolle> moechte ich <Ziel>, damit <Nutzen>.
**Beschreibung:** ...
**Akzeptanzkriterien:**
- Given ... When ... Then ...
**Traceability:** TEST-... | CODE-... | ADR-... | RISK-...
**Abhaengigkeiten:** REQ-.... | keine
**Notizen:** ...
```

If the existing file uses a different but consistent format, preserve the existing format and add missing fields minimally.

### 4. Status rules

- `Planned`: captured but not approved.
- `Approved`: accepted for implementation.
- `In Progress`: tests or implementation started.
- `Implemented`: code exists and narrow tests pass.
- `Tested`: QA/coverage gate passed.
- `Released`: included in a released/tagged version.
- `Deprecated`: kept for history; never delete REQ IDs.

### 5. Traceability rules

Every changed test or implementation must reference `REQ-XXXX`. Prefer comments near tests and docstrings where the relation is non-obvious.

## Output format

```markdown
## Requirements-Pruefung
**Klassifikation:** Use existing | Extend existing | Create new | Reject/clarify
**REQ-ID(s):** ...
**Begruendung:** ...

## Vorgeschlagene Aenderung
[Markdown block for new/changed REQ]

## Freigabe benoetigt?
Ja | Nein
```

