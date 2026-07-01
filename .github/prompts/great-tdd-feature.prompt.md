---
name: great-tdd-feature
description: Fuehrt eine TDD-Iteration fuer ein G.R.E.A.T.-Feature oder einen Bugfix ueber den Orchestrator aus.
agent: GREAT Orchestrator
argument-hint: "<REQ-ID oder Feature/Bug-Beschreibung>"
tools:
  - agent
  - codebase
---

# TDD Feature/Fix - G.R.E.A.T.

Starte mit dem `GREAT Orchestrator` und nutze den Skill `great-feature-tdd-workflow`.

Aufgabe: `${input:task:REQ-ID oder fachliche Beschreibung}`

Pflicht:
1. REQ-ID klaeren oder Requirements Engineer beauftragen.
2. QA Director fuer RED-Testdesign beauftragen.
3. Senior Developer erst danach implementieren lassen.
4. QA Director fuer Quality Gate beauftragen.
5. Nutzerbericht mit Tests, geaenderten Dateien und offenen Risiken liefern.
