---
name: great-frontend-office-ux
description: Use this skill in the G.R.E.A.T. project for React/TypeScript frontend work, Phase 3 React-first/HTMX replacement, Office-like UX, two-pane layouts, test-case tables, tree views, keyboard shortcuts, clipboard, undo/redo, drag-and-drop, accessibility, and user-facing interaction design. It turns UX requirements into implementable and testable frontend tasks.
argument-hint: "<frontend feature, UX issue, screen, or interaction>"
---

# GREAT Frontend Office UX

Use this skill for React/TypeScript and user-interface behavior in G.R.E.A.T., especially when the user describes desired behavior from a user perspective or asks for React-first UX improvements.

## UX north star

G.R.E.A.T. should feel like a precise Office-style test-case design tool:

- Fast keyboard-first interaction.
- Visible structure: project -> categories -> values -> rules -> generated test cases.
- Two-pane or multi-pane workflows where context stays visible.
- Predictable undo/redo and clipboard behavior.
- Accessibility and clear error messages.

## Required context

Inspect:

1. Relevant frontend REQs in `Agenten und basisinfos/requirements_v1.1.md`.
2. `documentation/vorschlagsliste-rollen.md` and UX-related docs if relevant.
3. Existing backend API contracts before designing frontend state.
4. Existing React/TypeScript files in `frontend/src/`.

## Design-to-implementation workflow

### 1. Convert user request into interaction spec

```markdown
## UX-Spezifikation
**Benutzerziel:** ...
**Primaerer Ablauf:** ...
**Tastatur/Shortcut:** ...
**Maus/DragDrop:** ...
**Fehlerfaelle:** ...
**Accessibility:** ...
**Akzeptanzkriterien:** Given/When/Then
```

### 2. Decide component boundaries

Prefer clear components:

- `ProjectTree`
- `CategoryEditor`
- `ValueGrid`
- `RuleEditor`
- `GeneratedTestCaseTable`
- `Toolbar`
- `KeyboardShortcutProvider`
- `UndoRedoProvider`

Adapt names to actual project conventions if different.

### 3. Test first

Before implementation, define tests for:

- Rendering and initial state.
- Keyboard shortcuts such as Ctrl+C, Ctrl+V, Ctrl+Z, Ctrl+Y.
- Drag/drop reorder or move behavior.
- Table sorting/filtering/search.
- Error and empty states.
- Accessibility labels and roles.

### 4. Implementation rules

- Keep UI state predictable and serializable.
- Avoid direct DOM manipulation unless unavoidable.
- Prefer accessible roles and labels.
- Do not hide destructive operations behind ambiguous shortcuts.
- Preserve German user-facing text and English code identifiers.

## Output format

```markdown
# Frontend/UX Plan

## REQs
...

## User Flow
...

## Komponenten
...

## Tests zuerst
...

## Implementierungsnotizen
...

## Risiken/Rueckfragen
...
```

