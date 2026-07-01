---
name: GREAT Legacy Rules
description: Regeln fuer Legacy-Code, Archiv-statt-Loeschen, HTMX-Ablosung, Datei-Klassifizierung und Archivdokumentation.
applyTo: "{archive/**,archive-log.md,documentation/legacy/**,documentation/legacy-audit-ui.md,src/backend/**,src/app/templates/**}"
---

# GREAT Legacy Rules

## Klassifizierung
- REUSE: unveraendert weiter nutzbar.
- REFACTOR: fachlich wertvoll, strukturell verbessern.
- REPLACE: fachlich noetig, Technologie/Struktur ersetzen.
- ARCHIVE: nicht mehr aktiv noetig, aber nachvollziehbar aufbewahren.

## Archivregel
Nicht loeschen. In `archive/YYYY-MM-DD/` verschieben und `archive-log.md` aktualisieren. Vorher Referenzen, Imports, Tests, Startskripte und Doku pruefen.

## HTMX/Alt-Frontend
React ist die aktive Richtung. HTMX-Teile gelten als Legacy, sofern Requirements/Project Assessment nichts anderes festlegen.
