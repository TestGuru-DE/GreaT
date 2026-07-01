---
name: great-web-research
description: Fuehrt eine quellenbasierte Web-/Dokumentationsrecherche fuer G.R.E.A.T. aus und liefert eine projektspezifische Empfehlung.
agent: GREAT Web Research Agent
argument-hint: "<Recherchethema und Ziel>"
tools:
  - fetch
  - codebase
---

# Web Research - G.R.E.A.T.

Recherchethema: `${input:topic:Thema}`
Ziel/Entscheidungsfrage: `${input:goal:Was soll entschieden oder verstanden werden?}`

Liefere:
- Kurzfazit.
- Quellen mit Datum und Relevanz.
- Vergleich von Optionen, falls sinnvoll.
- Lizenz-/Maintenance-Hinweis bei Dependencies.
- Empfehlung fuer G.R.E.A.T. mit betroffenen REQs/ADRs/Risiken.
- Offene Unsicherheiten.
