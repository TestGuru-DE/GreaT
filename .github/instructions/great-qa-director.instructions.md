---
name: GREAT QA Rules
description: Regeln fuer TDD, Testdesign, Coverage, Regression, Quality Gates und Release-Blocking.
applyTo: "{tests/**,pytest.ini,.coveragerc,frontend/src/**/*.test.*,frontend/src/**/*.spec.*,frontend/src/test-setup.ts}"
---

# GREAT QA Rules

## TDD
- RED-Test vor Produktivcode, wenn Verhalten geaendert wird.
- Test muss REQ oder expliziten Bugfix-Kontext nachvollziehbar machen.
- Wenn ein Test unerwartet schon gruen ist, Test verbessern oder Scope klaeren.

## Quality Gate
- Relevante Narrow Tests und Regressionstests ausfuehren.
- Coverage fuer geaenderten Code pruefen; Abweichungen offen begruenden.
- Frontend-Aenderungen brauchen passende Vitest/Build/Lint-Pruefung, soweit Projekt tooling vorhanden ist.
- Keine Pre-existing Failure behaupten ohne dokumentierte Quelle.

## Gate Status
PASS, CONDITIONAL PASS, FAIL oder NOT VERIFIED. Kein anderer Status.
