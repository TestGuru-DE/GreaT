---
applyTo: "**"
---

# G.R.E.A.T. - Copilot Projektanweisungen

Du arbeitest am Projekt **G.R.E.A.T.** (Georg Radikal Einfacher Automatisierter TestcaseDesigner).

## Source of Truth
Lies fuer aktuelle Entscheidungen nur die relevanten Ausschnitte aus:

1. `Agenten und basisinfos/SYSTEM_v1.0.md` - Governance.
2. `Agenten und basisinfos/requirements_v1.1.md` - aktive Requirements.
3. `documentation/project-assessment.md` - aktueller Projektstand/Roadmap.
4. `documentation/decision-log.md` - ADRs.
5. `documentation/risk-log.md` - Risiken.

## Nicht verhandelbare Regeln

1. **REQ-Pflicht:** Jede fachliche Implementierung braucht eine REQ-ID oder einen explizit dokumentierten Bugfix-Scope.
2. **TDD-Pflicht:** Verhalten erst testen, dann implementieren, dann refactoren.
3. **Quality Gate:** Nicht "fertig" sagen ohne Test-/Review-Evidenz oder klaren Status `NOT VERIFIED`.
4. **Archiv statt Loeschen:** Dateien nicht loeschen; nach `archive/YYYY-MM-DD/` verschieben und `archive-log.md` aktualisieren.
5. **Open Source Only:** Nur MIT/Apache/BSD-kompatible Dependencies, wenn nicht explizit anders entschieden.
6. **Sprache:** Dokumentation und Berichte Deutsch; Code-Bezeichner Englisch.
7. **Repo-Hygiene:** Keine DBs, Caches, `node_modules`, `dist`, `__pycache__`, `.pytest_cache` als aktive Aenderung.

## Aktueller Arbeitsmodus

- Der Nutzer spricht normalerweise mit `GREAT Orchestrator`.
- Der Orchestrator nutzt echte Subagents ueber das `agent`-Tool.
- Projekt-Skills liegen unter `.github/skills/` und sollen fuer wiederholbare Workflows genutzt werden.
- Aktueller Stand nicht hart codieren: aus Requirements und Project Assessment ableiten. Zum Zeitpunkt dieser Customization ist Phase 2 dokumentiert abgeschlossen und Phase 3 als React-First/HTMX-Ablosung geplant.

## Prioritaeten bei Konflikten

1. Fachliche Korrektheit
2. Testbarkeit
3. Wartbarkeit
4. Nachvollziehbarkeit
5. Dokumentation
6. Benutzerfreundlichkeit
7. Performance
