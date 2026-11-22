# RED-Testdesign: REQ-6009 — Pflicht-Testfälle (Seeds) und Lückenschluss

---

## Meta

| Feld | Wert |
|---|---|
| **REQ-ID** | REQ-6009 |
| **Titel** | Vorgegebene Testfälle beibehalten und nur die fehlende Abdeckung ergänzen; Lücken bestehender Generierungen nachträglich schließen |
| **Prioritaet** | Must |
| **Phase** | 5, Release v1.11.0 |
| **Epic** | EPIC-21 (Methodik-Release) |
| **Abhaengigkeiten** | REQ-3016, REQ-6008 (gemeinsame Abdeckungsberechnung), REQ-6001; schnelles Pairwise aus v1.9.0 |
| **Status** | Planned |
| **Autor** | GREAT QA Director (Subagent) |
| **Datum** | 2026-11-22 |

---

## Test-Dateien-Struktur

```
tests/
├── test_req6009_seed_generation.py          # Backend Unit-Tests: Kerngenerierung mit Seeds
├── test_req6009_seed_model.py               # Backend Unit-Tests: Seed-Modell, Validierung, CSV-Parsing
├── test_req6009_seed_api.py                 # Backend API-Integration-Tests
├── test_req6009_gap_fill.py                 # Backend Unit-Tests: Lueckenschluss
├── test_req6009_seed_report.py              # Backend Unit-Tests: Ergebnisbericht
├── test_req6009_seed_property.py            # Property-Tests (zufaellige Moedelle + Seeds)
└── test_req6009_seed_constraints.py         # Backend Unit-Tests: Seeds gegen Regeln/Constraints

frontend/src/
├── store/__tests__/seedStore.test.ts        # Zustand-Store fuer Seed-Saetze
├── components/__tests__/SeedEditor.test.tsx  # Zeileneditor-Komponente
├── components/__tests__/SeedImportDialog.test.tsx  # CSV-Import-Dialog
├── components/__tests__/SeedSetManager.test.tsx    # Seed-Satz-Verwaltung (speichern, loeschen, waehlen)
└── components/__tests__/GenerationPanel.seed.test.tsx  # Seed-Auswahl im Generierungs-Panel
```

---

## MOCK-DATEN

### Modell 1: Einfaches 2x2 (CATS_2X2)

```python
CATS_2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
}
```

### Modell 2: 2x2x2 (CATS_2X2X2)

```python
CATS_2X2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
    "C": ["c1", "c2"],
}
```

### Modell 3: Browser/OS mit Ergebnis-Kategorie (CATS_BROWSER_OS)

```python
CATS_BROWSER_OS = {
    "Browser": ["Chrome", "Firefox"],
    "OS": ["Windows", "Linux"],
    "Result": ["Pass", "Fail"],
}
```

### Modell 4: 3x3 (CATS_3X3)

```python
CATS_3X3 = {
    "A": ["a1", "a2", "a3"],
    "B": ["b1", "b2", "b3"],
}
```

### Seed-Satz 1: Vollstaendige Seeds (SEEDS_COMPLETE)

```python
SEEDS_COMPLETE = [
    {"A": "a1", "B": "b1"},
    {"A": "a2", "B": "b2"},
]
```

### Seed-Satz 2: Unvollstaendige Seeds (SEEDS_PARTIAL)

```python
SEEDS_PARTIAL = [
    {"A": "a1", "B": None},       # B = "beliebig" -> Werkzeug fuellt auf
    {"A": None, "B": "b1"},       # A = "beliebig" -> Werkzeug fuellt auf
    {"A": None, "B": None},       # beide = "beliebig"
]
```

### Seed-Satz 3: Regelwidrige Seeds (SEEDS_RULE_VIOLATING)

```python
# Regel: (A=a2, B=b2) verboten
SEEDS_RULE_VIOLATING = [
    {"A": "a1", "B": "b1"},
    {"A": "a2", "B": "b2"},       # Verstoßt gegen ForbiddenRule
]
```

### Seed-Satz 4: CSV-Import-Daten (CSV_SEEDS)

```python
CSV_SEEDS_TEXT = """A,B
a1,b1
a2,b2
a1,b2
"""

CSV_SEEDS_WITH_UNKNOWN = """A,B
a1,b1
a1,b_unknown    # Unbekannter Wert -> Warnung
a2,b2
"""

CSV_SEEDS_PARTIAL = """A,B
a1,
,b1
,
"""
```

### Seed-Satz 5: Lueckenschluss (GAP_FILL_SEEDS)

```python
# Bestehende Generierung mit 3 von 4 Paaren
EXISTING_GENERATION_TC = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
    # (a2, b2) fehlt
]

# Erwartetes Ergebnis nach Lueckenschluss
EXPECTED_GAP_FILL_RESULT = [
    {"A": "a1", "B": "b1", "origin": "seed"},
    {"A": "a1", "B": "b2", "origin": "seed"},
    {"A": "a2", "B": "b1", "origin": "seed"},
    {"A": "a2", "B": "b2", "origin": "supplemented"},
]
```

### Seed-Satz 6: Max-Grenze (SEEDS_MAX_10000)

```python
# 10.001 Seeds -> soll abgewiesen werden
SEEDS_OVER_LIMIT = [{"A": f"a{i}", "B": f"b{i}"} for i in range(10001)]

# 10.000 Seeds -> soll akzeptiert werden
SEEDS_AT_LIMIT = [{"A": f"a{i}", "B": f"b{i}"} for i in range(10000)]
```

### Seed-Satz 7: Duplikate (SEEDS_DUPLICATES)

```python
SEEDS_DUPLICATES = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b1"},  # Duplikat
    {"A": "a2", "B": "b2"},
]
```

### Seed-Satz 8: Empty (SEEDS_EMPTY)

```python
SEEDS_EMPTY = []
```

---

## TEST-KLASSEN UND -FaelLE

### 1. `test_req6009_seed_generation.py` — Kerngenerierung mit Seeds

**Ziel:** `combinatorics/seed_generation.py` — Kernalgorithmus

#### Klasse: `TestSeedGenerationBasic`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 1.1 | TEST-REQ-6009-GEN-001 | `test_seeds_preserved_in_result` | CATS_2X2 + SEEDS_COMPLETE | Alle 2 Seeds unveraendert im Ergebnis, plus Ergaenzung falls noetig |
| 1.2 | TEST-REQ-6009-GEN-002 | `test_seeds_plus_supplement_covers_all_pairs` | CATS_2X2 + SEEDS_COMPLETE | Paarabdeckung 100% nach Ergaenzung |
| 1.3 | TEST-REQ-6009-GEN-003 | `test_no_supplement_when_seeds_already_cover` | CATS_2X2 + [alle 4 Kombinationen als Seeds] | Ergebnis = nur Seeds, keine Ergaenzung |
| 1.4 | TEST-REQ-6009-GEN-004 | `test_empty_seeds_equals_normal_generation` | CATS_2X2 + SEEDS_EMPTY | Ergebnis = normale Pairwise-Generierung |
| 1.5 | TEST-REQ-6009-GEN-005 | `test_result_not_larger_than_seeds_plus_pairwise` | CATS_2X2X2 + 3 Seeds | len(result) <= len(seeds) + len(pairwise_without_seeds) |
| 1.6 | TEST-REQ-6009-GEN-006 | `test_origin_field_seed_vs_supplemented` | CATS_2X2 + SEEDS_COMPLETE | Jeder TC hat `origin` in ["seed", "supplemented"] |
| 1.7 | TEST-REQ-6009-GEN-007 | `test_supplemented_count_matches_uncovered_pairs` | CATS_3X3 + 2 Seeds | supplemented_count == Anzahl unbedeckter Paare (minimal) |

#### Klasse: `TestSeedGenerationIncompleteSeeds`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 1.8 | TEST-REQ-6009-GEN-008 | `test_partial_seed_filled_with_first_value` | CATS_2X2 + [{"A": "a1", "B": None}] | B wird mit erstem Wert "b1" gefuellt (oder einem Wert, der Paare abdeckt) |
| 1.9 | TEST-REQ-6009-GEN-009 | `test_partial_seed_filled_optimally` | CATS_2X2 + [{"A": None, "B": "b1"}] | A wird mit Wert gefuellt, der maximale Paarabdeckung bringt |
| 1.10 | TEST-REQ-6009-GEN-010 | `test_fully_empty_seed_becomes_valid_tc` | CATS_2X2 + [{"A": None, "B": None}] | Beide Werte werden gefuellt; Ergebnis ist gueltiger TC |
| 1.11 | TEST-REQ-6009-GEN-011 | `test_partial_seed_respects_rules` | CATS_2X2 + [{"A": "a2", "B": None}] + ForbiddenRule(a2,b2) | B wird mit "b1" gefuellt (nicht "b2" wegen Regel) |
| 1.12 | TEST-REQ-6009-GEN-012 | `test_partial_seed_origin_marked_filled` | CATS_2X2 + [{"A": "a1", "B": None}] | TC hat origin="seed" aber gefuellte Zellen sind gekennzeichnet (z.B. `filled_fields: ["B"]`) |

#### Klasse: `TestSeedGenerationStrategies`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 1.13 | TEST-REQ-6009-GEN-013 | `test_seeds_with_pairwise_strategy` | CATS_2X2 + SEEDS_COMPLETE, strategy="pairwise" | Seeds enthalten + pairwise-Ergaenzung |
| 1.14 | TEST-REQ-6009-GEN-014 | `test_seeds_with_t_wise_strategy` | CATS_2X2X2 + SEEDS_COMPLETE, strategy="t_wise", t=3 | Seeds enthalten + t-wise-Ergaenzung |
| 1.15 | TEST-REQ-6009-GEN-015 | `test_seeds_with_each_choice_strategy` | CATS_2X2 + SEEDS_COMPLETE, strategy="each" | Seeds enthalten + each-choice-Ergaenzung |
| 1.16 | TEST-REQ-6009-GEN-016 | `test_seeds_with_linear_strategy` | CATS_2X2 + SEEDS_COMPLETE, strategy="linear" | Seeds enthalten + linear-Ergaenzung |
| 1.17 | TEST-REQ-6009-GEN-017 | `test_seeds_with_all_combinations_strategy` | CATS_2X2 + SEEDS_COMPLETE, strategy="all" | Seeds enthalten + all-combinations-Ergaenzung |

---

### 2. `test_req6009_seed_model.py` — Seed-Modell, Validierung, CSV-Parsing

**Ziel:** `app/models/seed.py` (neu) + `app/services_seed.py` (neu)

#### Klasse: `TestSeedSetModel`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 2.1 | TEST-REQ-6009-MDL-001 | `test_seed_set_created_with_name` | name="Meine Seeds", seeds=[...], project_id=1 | SeedSet-Objekt mit name, project_id, seeds |
| 2.2 | TEST-REQ-6009-MDL-002 | `test_multiple_seed_sets_per_project` | 3 SeedSets mit gleichem project_id | Alle 3 existieren, unterschiedliche IDs |
| 2.3 | TEST-REQ-6009-MDL-003 | `test_seed_set_name_unique_per_project` | 2 SeedSets mit gleichem Namen im Projekt | Zweiter wird abgewiesen (409) oder umbenannt |
| 2.4 | TEST-REQ-6009-MDL-004 | `test_seed_set_max_10000` | 10001 Seeds | ValueError / HTTP 422 mit Meldung "Max 10.000 Seeds" |
| 2.5 | TEST-REQ-6009-MDL-005 | `test_seed_set_exactly_10000` | 10000 Seeds | Erfolgreich gespeichert |
| 2.6 | TEST-REQ-6009-MDL-006 | `test_seed_set_zero_seeds_allowed` | [] | Erlaubt (leerer Satz) |
| 2.7 | TEST-REQ-6009-MDL-007 | `test_seed_deleted_with_project` | Project loeschen | SeedSets werden CASCADE-ge-loescht |

#### Klasse: `TestSeedValidation`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 2.8 | TEST-REQ-6009-VAL-001 | `test_seed_unknown_category_rejected` | {"UnknownCat": "val"} | ValueError mit Kategorie-Name |
| 2.9 | TEST-REQ-6009-VAL-002 | `test_seed_unknown_value_reported` | {"A": "unknown_value"} | Warnung mit Wert-Name; nicht stillschweigend verworfen |
| 2.10 | TEST-REQ-6009-VAL-003 | `test_seed_empty_string_treated_as_any` | {"A": "", "B": "b1"} | "" -> None (beliebig) |
| 2.11 | TEST-REQ-6009-VAL-004 | `test_seed_missing_category_treated_as_any` | {"A": "a1"} (B fehlt) | B -> None (beliebig) |
| 2.12 | TEST-REQ-6009-VAL-005 | `test_seed_duplicate_detection` | SEEDS_DUPLICATES | Duplikat-Warnung; Duplikate entfernt oder gemeldet |

#### Klasse: `TestCSVSeedImport`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 2.13 | TEST-REQ-6009-CSV-001 | `test_csv_import_basic` | CSV_SEEDS_TEXT + CATS_2X2 | 3 Seeds, alle gueltig |
| 2.14 | TEST-REQ-6009-CSV-002 | `test_csv_import_unknown_value_warning` | CSV_SEEDS_WITH_UNKNOWN | Warnung: "b_unknown nicht in Kategorie B" |
| 2.15 | TEST-REQ-6009-CSV-003 | `test_csv_import_empty_cell_as_any` | CSV_SEEDS_PARTIAL | Leere Zelle -> None (beliebig) |
| 2.16 | TEST-REQ-6009-CSV-004 | `test_csv_import_unknown_column_warning` | CSV mit Spalte "UnknownCol" | Warnung: Spalte nicht bekannt |
| 2.17 | TEST-REQ-6009-CSV-005 | `test_csv_import_empty_file` | "" | 0 Seeds, keine Fehler |
| 2.18 | TEST-REQ-6009-CSV-006 | `test_csv_import_header_only` | "A,B\n" | 0 Seeds, keine Fehler |
| 2.19 | TEST-REQ-6009-CSV-007 | `test_csv_import_special_characters` | CSV mit Umlauten, Sonderzeichen | Werte korrekt eingelesen |
| 2.20 | TEST-REQ-6009-CSV-008 | `test_csv_import_max_seeds_exceeded` | CSV mit 10001 Zeilen | Abgewiesen mit Fehlermeldung |

---

### 3. `test_req6009_seed_api.py` — API-Integration-Tests

**Ziel:** `app/routers/api_seed.py` (neu) + Erweiterung `api_generate.py`

#### Klasse: `TestSeedSetCRUD`

| Nr. | Test-ID | Funktion | Endpoint | Erwartung |
|-----|---------|----------|----------|-----------|
| 3.1 | TEST-REQ-6009-API-001 | `test_create_seed_set` | POST /api/projects/{pid}/seed-sets | 201, name + seeds gespeichert |
| 3.2 | TEST-REQ-6009-API-002 | `test_list_seed_sets` | GET /api/projects/{pid}/seed-sets | 200, Liste aller Saetze |
| 3.3 | TEST-REQ-6009-API-003 | `test_get_seed_set` | GET /api/projects/{pid}/seed-sets/{ssid} | 200, korrekte Daten |
| 3.4 | TEST-REQ-6009-API-004 | `test_update_seed_set` | PUT /api/projects/{pid}/seed-sets/{ssid} | 200, aktualisierte Seeds |
| 3.5 | TEST-REQ-6009-API-005 | `test_delete_seed_set` | DELETE /api/projects/{pid}/seed-sets/{ssid} | 204, Satz geloescht |
| 3.6 | TEST-REQ-6009-API-006 | `test_create_seed_set_max_exceeded` | POST mit 10001 Seeds | 422, Fehlermeldung |
| 3.7 | TEST-REQ-6009-API-007 | `test_create_seed_set_unknown_values` | POST mit unbekannten Werten | 201 + warnings-Array in Response |
| 3.8 | TEST-REQ-6009-API-008 | `test_seed_set_not_found` | GET .../seed-sets/99999 | 404 |
| 3.9 | TEST-REQ-6009-API-009 | `test_seed_set_wrong_project` | GET .../seed-sets/{ssid} (fremdes Projekt) | 403 oder 404 |

#### Klasse: `TestGenerateWithSeeds`

| Nr. | Test-ID | Funktion | Endpoint | Erwartung |
|-----|---------|----------|----------|-----------|
| 3.10 | TEST-REQ-6009-API-010 | `test_generate_with_seed_set_id` | POST /api/projects/{pid}/generate + seed_set_id | 200, alle Seeds im Ergebnis |
| 3.11 | TEST-REQ-6009-API-011 | `test_generate_with_seeds_inline` | POST /api/projects/{pid}/generate + seeds: [...] | 200, Seeds enthalten |
| 3.12 | TEST-REQ-6009-API-012 | `test_generate_result_has_origin_field` | POST .../generate + seeds | Jeder TC hat `origin`: "seed" oder "supplemented" |
| 3.13 | TEST-REQ-6009-API-013 | `test_generate_result_has_report` | POST .../generate + seeds | Response enthaelt `report` mit seeds_count, supplemented_count, coverage_before, coverage_after |
| 3.14 | TEST-REQ-6009-API-014 | `test_generate_without_seeds_ignores_field` | POST .../generate ohne seeds | Normale Generierung, kein origin-Feld |

#### Klasse: `TestSeedImportAPI`

| Nr. | Test-ID | Funktion | Endpoint | Erwartung |
|-----|---------|----------|----------|-----------|
| 3.15 | TEST-REQ-6009-API-015 | `test_csv_import_endpoint` | POST /api/projects/{pid}/seed-sets/import-csv | 200, SeedSet erstellt |
| 3.16 | TEST-REQ-6009-API-016 | `test_csv_import_warnings_in_response` | CSV mit unbekannten Werten | Response enthaelt `warnings`-Array |
| 3.17 | TEST-REQ-6009-API-017 | `test_csv_import_max_seeds` | CSV mit 10001 Zeilen | 422 |

#### Klasse: `TestGapFillAPI`

| Nr. | Test-ID | Funktion | Endpoint | Erwartung |
|-----|---------|----------|----------|-----------|
| 3.18 | TEST-REQ-6009-API-018 | `test_gap_fill_creates_new_generation` | POST /api/generations/{gid}/gap-fill | 200, neue Generation-ID, alte unveraendert |
| 3.19 | TEST-REQ-6009-API-019 | `test_gap_fill_old_generation_unchanged` | Vorher/Nachher-Vergleich alte Generation | Alte TCs identisch |
| 3.20 | TEST-REQ-6009-API-020 | `test_gap_fill_new_generation_has_origin` | Neue Generation | Alle alte TCs = "seed", neue = "supplemented" |
| 3.21 | TEST-REQ-6009-API-021 | `test_gap_fill_report_before_after_coverage` | Response | coverage_before < coverage_after (bei Luecken) |

---

### 4. `test_req6009_gap_fill.py` — Lueckenschluss

**Ziel:** `combinatorics/gap_fill.py` (neu)

#### Klasse: `TestGapFillBasic`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 4.1 | TEST-REQ-6009-GAP-001 | `test_gap_fill_adds_missing_pairs` | EXISTING_GENERATION_TC + CATS_2X2 | (a2,b2) ergaenzt |
| 4.2 | TEST-REQ-6009-GAP-002 | `test_gap_fill_preserves_existing_tc` | EXISTING_GENERATION_TC | Alle 3 originale TCs unveraendert |
| 4.3 | TEST-REQ-6009-GAP-003 | `test_gap_fill_no_addition_when_full` | Alle 4 TCs + CATS_2X2 | Keine Ergaenzung |
| 4.4 | TEST-REQ-6009-GAP-004 | `test_gap_fill_new_generation_id` | Generation mit gap_fill() | Neue Generation mit neuer ID |
| 4.5 | TEST-REQ-6009-GAP-005 | `test_gap_fill_old_generation_immutable` | Nach gap_fill: alte Generation abfragen | Unveraendert |
| 4.6 | TEST-REQ-6009-GAP-006 | `test_gap_fill_origin_tracking` | Ergebnis | origin="seed" fuer alte, "supplemented" fuer neue |
| 4.7 | TEST-REQ-6009-GAP-007 | `test_gap_fill_with_rules` | EXISTING_GENERATION_TC + ForbiddenRule(a2,b2) | (a2,b2) nicht ergaenzt (regelbedingt unmoeglich) |
| 4.8 | TEST-REQ-6009-GAP-008 | `test_gap_fill_report_impossible_tuples` | Mit Regeln | report.impossible_tuples enthaelt (a2,b2) |

#### Klasse: `TestGapFillStrategies`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 4.9 | TEST-REQ-6009-GAP-009 | `test_gap_fill_pairwise_strategy` | strategy="pairwise" | Nur fehlende Paare ergaenzt |
| 4.10 | TEST-REQ-6009-GAP-010 | `test_gap_fill_t_wise_strategy` | t=3, CATS_2X2X2 | Fehlende Tripel ergaenzt |
| 4.11 | TEST-REQ-6009-GAP-011 | `test_gap_fill_minimal_supplement` | Minimal noetige Ergaenzung | supplemented_count minimal (nicht ueberschossen) |

---

### 5. `test_req6009_seed_report.py` — Ergebnisbericht

**Ziel:** `combinatorics/seed_report.py` (neu) oder Teil von `seed_generation.py`

#### Klasse: `TestSeedReport`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 5.1 | TEST-REQ-6009-RPT-001 | `test_report_seeds_count` | 2 Seeds + 2 ergaenzt | seeds_count == 2 |
| 5.2 | TEST-REQ-6009-RPT-002 | `test_report_supplemented_count` | 2 Seeds + 2 ergaenzt | supplemented_count == 2 |
| 5.3 | TEST-REQ-6009-RPT-003 | `test_report_coverage_before` | 2 Seeds in 2x2 | coverage_before == 50.0 (2/4 Paare) |
| 5.4 | TEST-REQ-6009-RPT-004 | `test_report_coverage_after` | 2 Seeds + 2 ergaenzt | coverage_after == 100.0 |
| 5.5 | TEST-REQ-6009-RPT-005 | `test_report_impossible_tuples` | Mit ForbiddenRule | impossible_tuples == [(a2,b2)] |
| 5.6 | TEST-REQ-6009-RPT-006 | `test_report_total_testcases` | 2 + 2 | total == 4 |
| 5.7 | TEST-REQ-6009-RPT-007 | `test_report_strategy` | strategy="pairwise" | report.strategy == "pairwise" |
| 5.8 | TEST-REQ-6009-RPT-008 | `test_report_partial_seeds_filled` | 1 Seed mit None | report.filled_fields pro Seed |

---

### 6. `test_req6009_seed_property.py` — Property-Tests

**Ziel:** Property-basierte Tests mit zufaelligen Eingaben

#### Klasse: `TestSeedProperty`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 6.1 | TEST-REQ-6009-PROP-001 | `test_random_model_seeds_preserved` | Zufallsmode ll (2-5 Cats, 2-4 Werte) + zufaellige Seeds | Alle Seeds (nach Auffuellung) unveraendert im Ergebnis |
| 6.2 | TEST-REQ-6009-PROP-002 | `test_random_model_pair_coverage_100` | Zufallsmode ll + Seeds | Paarabdeckung 100% (außer regelbedingt unmoeglich) |
| 6.3 | TEST-REQ-6009-PROP-003 | `test_result_size_bounded` | Zufallsmode ll + Seeds | len(result) <= len(seeds) + len(pairwise_without_seeds) |
| 6.4 | TEST-REQ-6009-PROP-004 | `test_seeds_preserved_with_rules` | Zufallsmode ll + Rules + Seeds (inkl. regelwidriger) | Gueltige Seeds unveraendert; regelwidrige markiert |
| 6.5 | TEST-REQ-6009-PROP-005 | `test_partial_seeds_filled_validly` | Zufallsmode ll + Seeds mit None | Alle None-Werte durch gueltige Werte ersetzt |
| 6.6 | TEST-REQ-6009-PROP-006 | `test_gap_fill_coverage_monotonic` | Zufallsmode ll + unvollstaendige Generation | coverage_after >= coverage_before |
| 6.7 | TEST-REQ-6009-PROP-007 | `test_origin_consistency` | Beliebige Seeds | Jeder TC hat origin; seed-TCs == seeds, supplemented-TCs == rest |

**Implementierungshinweis:** 20-50 Iterationen pro Property-Test mit `random`-Seed fuer Reproduzierbarkeit.

---

### 7. `test_req6009_seed_constraints.py` — Seeds gegen Regeln/Constraints

**Ziel:** Interaktion zwischen Seed-Validierung und RuleEngine

#### Klasse: `TestSeedRuleConflict`

| Nr. | Test-ID | Funktion | Input | Erwartung |
|-----|---------|----------|-------|-----------|
| 7.1 | TEST-REQ-6009-CST-001 | `test_forbidden_seed_warned_not_removed` | SEEDS_RULE_VIOLATING + ForbiddenRule | Warnung; Seed bleibt (Nutzer entscheidet) |
| 7.2 | TEST-REQ-6009-CST-002 | `test_forbidden_seed_keep_option` | + keep_violating=True | Seed im Ergebnis, origin="seed" |
| 7.3 | TEST-REQ-6009-CST-003 | `test_forbidden_seed_exclude_option` | + keep_violating=False | Seed ausgeschlossen, origin nicht im Ergebnis |
| 7.4 | TEST-REQ-6009-CST-004 | `test_combine_rule_seed_warning` | Seed + CombineRule (nur bestimmte Werte erlaubt) | Warnung wenn Seed-Wert nicht in erlaubter Liste |
| 7.5 | TEST-REQ-6009-CST-005 | `test_dependency_rule_seed_adjustment` | Seed + DependencyRule | Seed-Werte werden durch Dependency angepasst (mit Kennzeichnung) |
| 7.6 | TEST-REQ-6009-CST-006 | `test_constraint_rule_seed_warning` | Seed + ConstraintRule (logisches Constraint) | Warnung bei Verstoß |
| 7.7 | TEST-REQ-6009-CST-007 | `test_multiple_rule_violations_reported` | Seed mit 2 Regelverstoessen | Beide in warnings-Array |
| 7.8 | TEST-REQ-6009-CST-008 | `test_seed_partial_fill_respects_forbidden` | {"A": "a2", "B": None} + Forbidden(a2,b2) | B != "b2" (wird mit "b1" gefuellt) |

---

## FRONTEND-TESTS

### `seedStore.test.ts` — Zustand-Store

| Nr. | Test-ID | Funktion | Erwartung |
|-----|---------|----------|-----------|
| F1 | TEST-REQ-6009-FE-001 | `test_add_seed_row` | Neue Zeile im Store |
| F2 | TEST-REQ-6009-FE-002 | `test_remove_seed_row` | Zeile entfernt |
| F3 | TEST-REQ-6009-FE-003 | `test_set_seed_cell_value` | Zellenwert gesetzt |
| F4 | TEST-REQ-6009-FE-004 | `test_clear_seed_cell` | Zelle auf null/undefined |
| F5 | TEST-REQ-6009-FE-005 | `test_save_seed_set` | API-Aufruf POST /seed-sets |
| F6 | TEST-REQ-6009-FE-006 | `test_load_seed_sets` | API-Aufruf GET /seed-sets |
| F7 | TEST-REQ-6009-FE-007 | `test_select_seed_set_for_generation` | seedSetId im Generate-Form |
| F8 | TEST-REQ-6009-FE-008 | `test_import_csv_seeds` | CSV-Parsing + Store-Fuellung |
| F9 | TEST-REQ-6009-FE-009 | `test_max_seeds_validation` | > 10000 -> Error-Flag |
| F10 | TEST-REQ-6009-FE-010 | `test_warnings_display` | warnings-Array sichtbar |

### `SeedEditor.test.tsx` — Zeileneditor

| Nr. | Test-ID | Funktion | Erwartung |
|-----|---------|----------|-----------|
| F11 | TEST-REQ-6009-FE-011 | `test_render_empty_editor` | Leere Tabelle mit "Hinzufuegen"-Button |
| F12 | TEST-REQ-6009-FE-012 | `test_add_row_button` | Neue Zeile mit Dropdowns pro Kategorie |
| F13 | TEST-REQ-6009-FE-013 | `test_category_dropdown_values` | Dropdown zeigt alle Werte der Kategorie |
| F14 | TEST-REQ-6009-FE-014 | `test_select_any_value` | "— beliebig —" Option in Dropdown |
| F15 | TEST-REQ-6009-FE-015 | `test_remove_row_button` | Zeile wird entfernt |
| F16 | TEST-REQ-6009-FE-016 | `test_empty_cell_shown_as_any` | Leere Zelle zeigt "beliebig" |

### `SeedImportDialog.test.tsx` — CSV-Import

| Nr. | Test-ID | Funktion | Erwartung |
|-----|---------|----------|-----------|
| F17 | TEST-REQ-6009-FE-017 | `test_file_input_accepts_csv` | accept=".csv" |
| F18 | TEST-REQ-6009-FE-018 | `test_preview_table_after_upload` | Vorschau-Tabelle mit geparsten Seeds |
| F19 | TEST-REQ-6009-FE-019 | `test_warnings_shown_for_unknown_values` | Warnungen als gelbe Box |
| F20 | TEST-REQ-6009-FE-020 | `test_import_button_creates_seed_set` | API-Call + Store-Update |

### `SeedSetManager.test.tsx` — Seed-Satz-Verwaltung

| Nr. | Test-ID | Funktion | Erwartung |
|-----|---------|----------|-----------|
| F21 | TEST-REQ-6009-FE-021 | `test_list_seed_sets` | Liste aller Seed-Saetze |
| F22 | TEST-REQ-6009-FE-022 | `test_rename_seed_set` | Name editierbar |
| F23 | TEST-REQ-6009-FE-023 | `test_delete_seed_set_confirmation` | Confirm-Dialog vor Loeschen |
| F24 | TEST-REQ-6009-FE-024 | `test_select_seed_set_for_generation` | Checkbox/Radio fuer Auswahl |

### `GenerationPanel.seed.test.tsx` — Seed-Auswahl im Generierungs-Panel

| Nr. | Test-ID | Funktion | Erwartung |
|-----|---------|----------|-----------|
| F25 | TEST-REQ-6009-FE-025 | `test_seed_set_selector_visible` | Dropdown fuer Seed-Satz-Auswahl |
| F26 | TEST-REQ-6009-FE-026 | `test_generate_with_selected_seeds` | API-Call mit seed_set_id |
| F27 | TEST-REQ-6009-FE-027 | `test_gap_fill_button_on_generation` | "Luecken schliessen"-Button pro Generation |
| F28 | TEST-REQ-6009-FE-028 | `test_origin_column_in_testcase_table` | "Herkunft"-Spalte: Seed / ergaenzt |
| F29 | TEST-REQ-6009-FE-029 | `test_report_shown_after_generation` | seeds_count, supplemented_count, coverage_before/after |
| F30 | TEST-REQ-6009-FE-030 | `test_seed_warnings_modal` | Regelverstoess-Modal mit "trotzdem behalten" / "ausschliessen" |

---

## EDGE CASES

| Nr. | Szenario | Erwartetes Verhalten |
|-----|----------|---------------------|
| E1 | Seed mit allen Kategorien leer (alle None) | Alle Werte werden gefuellt; origin="seed" |
| E2 | Seed mit mehr Werten als Kategorien im Modell | Ueberschuessige Keys ignoriert + Warnung |
| E3 | Seed mit weniger Werten als Kategorien | Fehlende Kategorien = None (beliebig) |
| E4 | Seed-Satz mit 0 Seeds + Generierung | Wie normale Generierung ohne Seeds |
| E5 | Seed-Satz mit 10.000 Seeds + kleines Modell | Akzeptiert; Generierung kann lange dauern (Timeout) |
| E6 | Seed-Satz mit 10.001 Seeds | Abgewiesen mit 422 |
| E7 | Alle Seeds verletzen Regeln | Alle mit Warnung; Nutzer muss entscheiden |
| E8 | Lueckenschluss bei bereits 100% Coverage | Keine Ergaenzung; Report: coverage_before == coverage_after == 100% |
| E9 | CSV mit BOM (UTF-8-BOM) | BOM wird ignoriert |
| E10 | CSV mit semikolon-Trennzeichen | Erkennung und korrektes Parsen |
| E11 | Seed-Wert mit Komma im Namen (CSV-Escape) | Korrektes Parsen mit Quotes |
| E12 | Duplizierte Seeds im selben Satz | Warnung + Duplikate entfernt |
| E13 | Seed aus geloeschter Generierung | Referenz nicht mehr gueltig; Warnung |
| E14 | Lueckenschluss mit Ergebnis-Kategorie | Ergebnis-Kategorie ignoriert (wie REQ-6008) |
| E15 | Seed mit Fehlerwert (allowed=False) | Fehlerwert wird akzeptiert (wie BUG-6) |

---

## ABHANGIGE IMPLEMENTIERUNGEN (für RED-Phase)

Folgende Module muessen existieren, damit die Tests laufen koennen (RED-Phase = alle Tests failen):

| Modul | Pfad | Beschreibung |
|-------|------|-------------|
| `SeedSet` Model | `src/app/models/seed.py` | SQLAlchemy-Modell fuer Seed-Saetze |
| `seed_generation` | `src/combinatorics/seed_generation.py` | Kernalgorithmus: Seeds + Ergaenzung |
| `gap_fill` | `src/combinatorics/gap_fill.py` | Lueckenschluss-Algorithmus |
| `seed_report` | `src/combinatorics/seed_report.py` | Ergebnisbericht-Generierung |
| `seed_service` | `src/app/services_seed.py` | Business-Logic fuer Seed-CRUD |
| `api_seed` Router | `src/app/routers/api_seed.py` | REST-Endpunkte fuer Seeds |
| `api_generate` Erweiterung | `src/app/routers/api_generate.py` | `seed_set_id` Parameter + `gap_fill` Action |
| `seedStore` | `frontend/src/store/seedStore.ts` | Zustand-Store |
| `SeedEditor` | `frontend/src/components/SeedEditor.tsx` | Zeileneditor-Komponente |
| `SeedImportDialog` | `frontend/src/components/SeedImportDialog.tsx` | CSV-Import-Dialog |
| `SeedSetManager` | `frontend/src/components/SeedSetManager.tsx` | Seed-Satz-Verwaltung |

---

## TEST-AUSFUEHRUNGSREIHENFOLGE (TDD)

```
Phase 1: RED (alle Tests failen)
  ├── test_req6009_seed_property.py       # Property-Tests zuerst (REQ-TDD-Hinweis)
  ├── test_req6009_seed_generation.py     # Kernalgorithmus
  ├── test_req6009_seed_model.py          # Modell + Validierung
  ├── test_req6009_seed_constraints.py    # Regel-Interaktion
  ├── test_req6009_gap_fill.py            # Lueckenschluss
  ├── test_req6009_seed_report.py         # Ergebnisbericht
  └── test_req6009_seed_api.py            # API-Integration

Phase 2: GREEN (Implementierung pro Testklasse)
  ├── combinatorics/seed_generation.py    # Kernalgorithmus
  ├── combinatorics/gap_fill.py           # Lueckenschluss
  ├── combinatorics/seed_report.py        # Bericht
  ├── app/models/seed.py                  # DB-Modell
  ├── app/services_seed.py                # Business-Logic
  ├── app/routers/api_seed.py             # REST-API
  └── app/routers/api_generate.py         # Erweiterung

Phase 3: Frontend (parallel moeglich)
  ├── store/seedStore.ts
  ├── components/SeedEditor.tsx
  ├── components/SeedImportDialog.tsx
  ├── components/SeedSetManager.tsx
  └── components/GenerationPanel.seed.tsx

Phase 4: REFACTOR
  ├── Code-Review
  ├── Coverage-Check
  └── Integration-Tests
```

---

## QUALITY GATE KRITERIEN

| Kriterium | Zielwert |
|-----------|----------|
| Backend-Test-Coverage fuer seed_generation.py | >= 90% |
| Backend-Test-Coverage fuer seed_model.py | >= 90% |
| Backend-Test-Coverage fuer gap_fill.py | >= 90% |
| Backend-Test-Coverage fuer api_seed.py | >= 80% |
| Frontend-Test-Coverage fuer seedStore.ts | >= 80% |
| Frontend-Test-Coverage fuer SeedEditor.tsx | >= 80% |
| Property-Tests Iterationen | >= 20 pro Test |
| Alle REQ-6009 Akzeptanzkriterien abgedeckt | Ja |
| Kein Seed stillschweigend entfernt | Ja (nur mit Warnung) |
| Alte Generation bei Lueckenschluss unveraendert | Ja (Immutable History) |

---

## KONFLIKTE UND ENTSCHEIDUNGEN

| Frage | Entscheidung | Begründung |
|-------|-------------|------------|
| Seed-Wert "beliebig" als None oder ""? | `None` (Python) / `null` (JSON) | Klare Unterscheidung zu leerem String; entspricht REQ "leere Zelle = beliebig" |
| Regelwidrige Seeds: default keep oder exclude? | **Warnung + Nutzer entscheidet** | REQ: "Der Nutzer entscheidet: trotzdem behalten oder ausschliessen" |
| Origin-Feld: String oder Enum? | String "seed" / "supplemented" | Einfacher, Export-freundlich, entspricht REQ |
| Lueckenschluss: neue Generation oder Update? | **Neue Generation** | REQ: "erzeugt eine neue Generierung = alte + Ergaenzung. Die alte bleibt unveraendert." |
| CSV-Trennzeichen: Komma oder semikolon? | Auto-Erkennung (Komma zuerst, dann Semikolon) | Europa-Standard + international |

---

## QUELLBEZUGE

- REQ-6009: `userstorys und basisinfos/requirements_v1.1.md` Zeile 3180-3207
- REQ-6008 Coverage: `tests/test_req6008_coverage_calc.py` (Pattern-Vorlage)
- REQ-6001 Constraints: `src/core/rules/rule_engine.py`
- IPOG Pairwise: `src/combinatorics/ipo.py`
- Generation API: `src/app/routers/api_generate.py`
- Test-Infrastruktur: `tests/conftest.py`