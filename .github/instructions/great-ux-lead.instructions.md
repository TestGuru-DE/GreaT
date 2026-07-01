---
name: GREAT UX Rules
description: Regeln fuer Office-aehnliche React/TypeScript-UX, Tastaturbedienung, Tabellen, Tree-Views, Drag-and-Drop, Accessibility und Fehlertoleranz.
applyTo: "{frontend/src/**,frontend/src/**/*.css,frontend/src/**/*.tsx,documentation/legacy-audit-ui.md}"
---

# GREAT UX Rules

## UX-Zielbild
G.R.E.A.T. soll sich fuer Tester wie ein praezises Office-Werkzeug fuer Testdesign anfuehlen: schnell, klar, tastaturfreundlich, fehlertolerant.

## Regeln
- Wichtige Aktionen muessen sichtbares Feedback geben.
- Tastatur-Shortcuts duerfen Eingaben nicht unerwartet zerstoeren.
- Tabellen/Listen brauchen klare Selektion, Fokus und Undo-/Abbruch-Moeglichkeiten, sofern fachlich relevant.
- Drag-and-Drop braucht Alternative oder klare Tastatur-/Button-Bedienung.
- Fehlermeldungen sagen, was passiert ist und was der Nutzer tun kann.
- Accessibility: semantische Elemente, Labels, Fokusfuehrung, Kontrast beachten.
