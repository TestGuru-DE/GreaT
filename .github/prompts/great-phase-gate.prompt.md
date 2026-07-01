---
name: great-phase-gate
description: Prueft Sprint-, Phase- oder Release-Freigabe fuer G.R.E.A.T. mit Program Manager, Architect und QA Director.
agent: GREAT Orchestrator
argument-hint: "<Phase, Sprint oder Release-Scope>"
tools:
  - agent
  - codebase
---

# GREAT Phase/Release Gate

Scope: `${input:scope:Phase/Sprint/Release}`

Nutze den Skill `great-release-readiness`.

Pflichtbeteiligung:
1. QA Director: Tests, Coverage, Regression, Quality Gate.
2. Chief Architect: Architektur-Schulden, ADRs, technische Risiken.
3. Program Manager: Scope, Risiken, Roadmap, Go/No-Go.
4. Security/DevOps nur wenn Security, Deployment, Build oder CI betroffen sind.

Ergebnisformat:
- Status: GO | NO-GO | CONDITIONAL GO | NOT VERIFIED
- Evidenz: Tests/Reviews/Dokumente
- Blocker
- Freigabe-Auflagen
- Naechste Schritte
