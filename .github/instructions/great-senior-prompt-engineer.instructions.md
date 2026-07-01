---
name: GREAT Prompt Engineering Rules
description: Regeln fuer Agenten-, Instructions-, Prompt- und Skill-Qualitaet, Subagent-Routing, Token-Optimierung und Governance in G.R.E.A.T.
applyTo: "{.github/agents/**,.github/instructions/**,.github/prompts/**,.github/skills/**,documentation/prompt-governance/**}"
---

# GREAT Prompt Engineering Rules

## Qualitaetskriterien
Jede Customization muss klar beantworten:
- Rolle und Grenze.
- Entscheidungskompetenz.
- Verbote.
- Delegation/Eskalation.
- Erwartete Evidenz.
- Outputformat.

## Token-Optimierung
- Lange Regeln nicht in Agenten duplizieren; Agenten bleiben Router/Rolle, Details liegen in Instructions oder Skills.
- `applyTo: "**"` nur fuer wirklich globale Regeln verwenden.
- Alte Roadmaps/Phasen nicht in mehreren Dateien hart codieren.
- Subagents nur bei echtem Mehrwert nutzen; nicht jede Anfrage durch alle Agenten schicken.

## Ablage
- Agents: `.github/agents/*.agent.md`
- Instructions: `.github/instructions/*.instructions.md`
- Prompts: `.github/prompts/*.prompt.md`
- Skills: `.github/skills/<skill-name>/SKILL.md`

## Gebrochene Bezuege verhindern
- Keine `.vscode/`-Referenzen, solange nicht explizit konfiguriert.
- Dateinamen exakt halten: `great-senior-prompt-engineer`, nicht `engeneer`.
- Skill-Name muss zum Ordnernamen passen.
