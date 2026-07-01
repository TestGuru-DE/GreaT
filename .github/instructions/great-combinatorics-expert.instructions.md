---
name: GREAT Combinatorics Rules
description: Regeln fuer Kombinatorik-Algorithmen, Testfallgenerierung, ISTQB-Begriffe, Constraints, Korrektheitsnachweis und algorithmische Tests.
applyTo: "{src/combinatorics/**,src/core/rules/**,tests/test_*combination*.py,tests/test_*pairwise*.py,tests/test_*linear*.py,tests/test_*each*.py,tests/test_*risk*.py,tests/test_*boundary*.py}"
---

# GREAT Combinatorics Rules

## Aktuellen Status bestimmen
Nutze `Agenten und basisinfos/requirements_v1.1.md`, `src/combinatorics/` und `tests/` als aktuelle Wahrheit. Verlasse dich nicht auf alte Sprint-Tabellen in Prompt-Dateien.

## Fachliche Regeln
- Each Choice: jeder gueltige Wert mindestens einmal.
- Linear Expansion: Baseline plus genau eine Abweichung je Nicht-Default-Wert.
- All Combinations: vollstaendiger kartesischer Produktraum, gefiltert durch gueltige Regeln.
- Pairwise/IPOG: jedes gueltige Wertepaar ueber Kategorien mindestens einmal.
- Risk-Based: Risikosortierung darf Coverage nicht verlieren.
- BVA: Grenzwerte nur fuer passende Datentypen, deterministisch und nachvollziehbar.
- MCDC/T-Wise/Business Rule Based nur gemaess aktueller REQ-Planung implementieren.

## Qualitaetsregeln
- Deterministische Ausgabe oder expliziter Seed.
- Edge Cases testen: leere Kategorien, Ein-Wert-Kategorien, ungleiche Groessen, Konfliktregeln, Duplikate.
- Nicht-triviale Algorithmen brauchen Invarianten/Komplexitaet im Docstring oder in Doku.
- Algorithmus-Logik, RuleEngine und I/O getrennt halten.
