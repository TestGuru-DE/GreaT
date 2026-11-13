---
name: great-agent-customization-audit
description: "Use this skill in the G.R.E.A.T. project to audit VS Code/GitHub Copilot customization files: custom agents, instructions, prompt files, skills, hooks, MCP config, placement, frontmatter, duplicate roles, broken references, outdated model/tool names, conflicting rules, and governance drift."
argument-hint: "<customization folder, agent name, or audit scope>"
---

# GREAT Agent Customization Audit

Use this skill when maintaining the G.R.E.A.T. agent system itself.

## Scope

Audit these locations:

```text
.github/copilot-instructions.md
.github/agents/*.agent.md
.github/instructions/**/*.instructions.md
.github/prompts/**/*.prompt.md
.github/skills/*/SKILL.md
.vscode/ only if explicitly configured in VS Code settings
```

## Placement rules

- Project custom agents belong in `.github/agents/`.
- Project instructions belong in `.github/instructions/`.
- Project prompt files belong in `.github/prompts/`.
- Project skills belong in `.github/skills/<skill-name>/SKILL.md`.
- Avoid duplicate sources of truth in `.vscode` and `.github` unless there is an explicit settings-based reason.

## Audit checks

### 1. Discovery and placement

- Are files in a default-discovered location?
- Are prompt files accidentally stored as agents?
- Are instruction files actually discoverable?
- Is there an empty or wrong skills folder such as `.github/agents/skills/`?

### 2. Frontmatter validity

Check:

- `.agent.md`: `name`, `description`, `tools`, optional `agents`, `model`, `handoffs`.
- `.instructions.md`: `name`, `description`, `applyTo`; avoid unsupported fields unless knowingly tolerated.
- `.prompt.md`: `name`, `description`, `agent`, `tools`, `argument-hint`.
- `SKILL.md`: `name` must match parent directory; only lowercase letters, numbers, hyphens.

### 3. Role quality

Every agent must answer:

1. What is the role?
2. What is the decision authority?
3. What is forbidden?
4. What does it delegate?
5. Who can overrule it?
6. What evidence must it produce?

### 4. Overlap and conflict

Flag:

- Two agents owning the same final decision.
- Orchestrator that says it never implements but has broad edit tools without a clear control rule.
- Requirements Engineer and Program Manager both making final priority decisions.
- Developer and QA both owning final coverage sign-off.
- Prompt Engineer files with typos or stale references.

### 5. Broken references

Search for outdated file names and paths, especially references to `.vscode/` if `.github/` is the real source.

## Output format

```markdown
# Agent Customization Audit – G.R.E.A.T.

## Gesamtbewertung
Gut | brauchbar mit Korrekturen | riskant | nicht verlaesslich

## Kritische Befunde
| ID | Schwere | Datei | Befund | Wirkung | Empfehlung |
|---|---|---|---|---|---|

## Ablage-/Discovery-Befunde
...

## Rollen-/Overlap-Befunde
...

## Konkreter Zielzustand
```text
.github/
  copilot-instructions.md
  agents/
  instructions/
  prompts/
  skills/
```

## Priorisierte Reparatur
1. ...
2. ...
3. ...
```

