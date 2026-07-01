# Phase 3 – Sprint 5 Planning

**Datum:** 2026-07-01  
**Phase:** 3 (React-First + UX-Verbesserungen)  
**Status:** GO – Sprint gestartet

---

## Sprint-Ziel

Verbesserung der User Experience durch Theme-System mit 5 Themes (Normal, Dark, Steampunk, Rainbow, Heavy Metal) sowie Risikoabdeckungs-Anzeige pro Testfall und Generierung.

---

## Projektregel: Linearer Workflow (ab Sprint 5)

> **REQs werden ausschließlich sequenziell abgearbeitet.**
> - Ein Feature-Branch nach dem anderen.
> - Erst mergen, dann nächsten Branch starten.
> - Kein paralleles Arbeiten auf mehreren Feature-Branches.
>
> Grund: Eliminiert Merge-Konflikte, verbessert Code-Review-Qualität.

---

## Sprint-Backlog (Reihenfolge einhalten!)

| # | REQ | Titel | SP | Abhängigkeit |
|---|---|---|---|---|
| 1 | REQ-3045 | Theme-System Grundlage | 40 | – |
| 2 | REQ-3046 | Theme Dark | 15 | REQ-3045 |
| 3 | REQ-3047 | Theme Steampunk | 20 | REQ-3045 |
| 4 | REQ-3048 | Theme Rainbow | 15 | REQ-3045 |
| 5 | REQ-3049 | Theme Heavy Metal | 15 | REQ-3045 |
| 6 | REQ-3050 | Risikoabdeckung Testfall | 25 | – |
| 7 | REQ-3051 | Risikoabdeckung Generierung | 20 | REQ-3050 |
| | **Gesamt** | | **150 SP** | |

---

## Offene ADR-Entscheidungen (vor Sprint-Start klären)

### ADR-011: Theme-System-Ansatz
**Optionen:**
1. **CSS-Variablen + Tailwind** (Empfehlung: einfach, performant)
2. Styled-Components ThemeProvider (+50KB, maximale Flexibilität)
3. Tailwind CSS-Klassen pro Theme

**Empfehlung:** Option 1 – CSS-Variablen  
**Entscheider:** Chief Architect

### ADR-013: Risikoabdeckungs-Berechnung
**Optionen:**
1. On-the-fly (JOIN, immer aktuell, ggf. langsam bei >1000 TF)
2. Gecacht in DB (schnell, muss bei Änderungen invalidiert werden)

**Empfehlung:** Option 1 für MVP, Option 2 bei Performance-Problemen  
**Entscheider:** Senior Developer

---

## Risiken

| Risiko | Score | Maßnahme |
|---|---|---|
| Risikoabdeckung Performance bei >1000 Testfällen | 16 | Performance-Tests vor Merge |
| Theme WCAG AA Kontrast nicht erfüllt | 12 | Accessibility-Tests mit Contrast Checker |
| Steampunk-Theme: dekorative Elemente komplex | 12 | Prototyp vorab |
| FOUC beim Theme-Laden | 8 | Theme aus LocalStorage vor React-Mount |

---

## Definition of Done (Sprint 5)

- TDD: Tests vor Implementierung
- Coverage >= 90%
- 1 Branch nach dem anderen (Linearregel)
- WCAG AA für alle Themes
- Alle bestehenden 223+ Tests grün
- ADR-011 entschieden vor Start REQ-3045

---

## Phase 3 Sprint 6+ Backlog (Übersicht)

| REQ | Titel | SP | Prio | Sprint |
|---|---|---|---|---|
| REQ-3052 | Tabellenansicht Testfälle | 35 | MUST | 6 |
| REQ-3062 | Dark-Mode System-Sync | 10 | SHOULD | 6 |
| REQ-3053 | Undo/Redo | 30 | SHOULD | 6 |
| REQ-3054 | Tastaturnavigation | 20 | SHOULD | 6 |
| REQ-3058 | PDF-Export | 25 | SHOULD | 7 |
| REQ-3059 | Kategorie-Kommentare | 20 | SHOULD | 7 |
| REQ-3055 | Projekt-Vorlagen | 25 | COULD | 7 |
| REQ-3056 | CSV-Import | 30 | COULD | 7 |
| REQ-3057 | i18n | 40 | COULD | 8 |
| REQ-3060 | Testfall-Kommentare | 15 | COULD | 8 |
| REQ-3061 | Versionshistorie | 50 | COULD | Backlog |
| **Gesamt** | | **300 SP** | | |

