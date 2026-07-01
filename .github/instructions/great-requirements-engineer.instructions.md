---
name: GREAT Requirements Rules
description: Regeln fuer REQ-ID-Suche, User Stories, Akzeptanzkriterien, Status, Traceability und Duplikatvermeidung.
applyTo: "{Agenten und basisinfos/requirements*.md,documentation/themenspeicher.md,documentation/project-assessment.md}"
---

# GREAT Requirements Rules

- `Agenten und basisinfos/requirements_v1.1.md` ist die aktive Requirements-Quelle, solange keine neuere Datei explizit als Source of Truth markiert ist.
- Vor jeder neuen REQ semantisch suchen: gleicher Nutzerwert, gleiche Akzeptanzkriterien, gleiche Phase.
- Bestehende REQ erweitern statt Duplikat anlegen, wenn der Nutzerwert gleich ist.
- Status nur mit Evidenz aendern: Tests, Code-Aenderung, Program-Entscheidung oder Doku-Beschluss.
- Neue REQ im Format: Titel, Prioritaet, Status, Phase/Sprint, User Story, Akzeptanzkriterien, Abhaengigkeiten.
- REQ-Bereiche koennen wachsen; aktuelle 3000/4000-Bereiche aus der Datei respektieren.
