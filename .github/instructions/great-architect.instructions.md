---
name: GREAT Architect Rules
description: "Architekturregeln fuer G.R.E.A.T.: ADRs, Layering, Router/Service-Trennung, ORM, Dependencies, Migrations und technische Vetos."
applyTo: "{src/**,frontend/src/**,documentation/architecture/**,documentation/decision-log.md,alembic.ini}"
---

# GREAT Architect Rules

## Source of Truth
- `documentation/architecture/current-architecture.md`
- `documentation/decision-log.md`
- `documentation/risk-log.md`
- `Agenten und basisinfos/requirements_v1.1.md`

## Verbindliche Leitplanken
- Keine Businesslogik in FastAPI-Routern; Route -> Service -> Repository/DB.
- Kein Raw SQL; SQLAlchemy ORM oder projektweit dokumentierte Ausnahme.
- Keine zirkulaeren Imports.
- Neue strategische Dependencies brauchen Architektur-/Lizenzpruefung und ggf. ADR.
- Migrations-/Datenmodell-Aenderungen brauchen nachvollziehbare Tests und Doku.
- React ist die aktive Frontend-Richtung; HTMX ist Legacy und nur noch fuer Ablosung/Archivierung relevant.

## ADR-Test
ADR erforderlich bei Framework-, Datenbank-, API-Struktur-, Auth-, Deployment-, Migrations- oder Dependency-Entscheidungen, die zukuenftige Arbeit praegen.

## Veto
Blockiere Aenderungen, die Architekturregeln verletzen oder ohne REQ/ADR-Evidenz strategische Richtung aendern.
