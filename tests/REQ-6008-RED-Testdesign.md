# RED-Testdesign: REQ-6008 — Abdeckungsanzeige als Matrix/Heatmap

## Uebersicht

| Bereich | Testdatei | Typ |
|---|---|---|
| Backend Unit | `tests/test_req6008_coverage_calc.py` | Unit-Tests, `combinatorics.coverage` |
| Backend API | `tests/test_req6008_coverage_api.py` | API-Integration, `/api/generations/{gid}/coverage` |
| Frontend | `frontend/src/components/__tests__/CoverageHeatmap.test.tsx` | Vitest, React |
| Frontend | `frontend/src/components/__tests__/CoverageOverviewMatrix.test.tsx` | Vitest, React |
| Performance | `tests/test_req6008_coverage_performance.py` | Lasttest |

---

## 1. Backend Unit-Tests: `tests/test_req6008_coverage_calc.py`

**Zielmodul:** `src/combinatorics/coverage.py` (neu)

**Signatur der zu testenden Funktionen:**
```python
def calculate_coverage(
    testcases: list[dict[str, str]],
    categories: dict[str, list[str]],
    t: int = 2,
    rule_engine: RuleEngine | None = None,
    result_category_names: list[str] | None = None,
) -> CoverageResult:
    ...

@dataclass
class CoverageResult:
    t: int
    covered: int          # Anzahl abgedeckter Tupel
    possible: int         # Anzahl moeglicher (gueltiger) Tupel
    excluded_by_rules: int  # Anzahl durch Regeln/Constraints ausgeschlossener Tupel
    percentage: float     # covered / possible * 100, 0.0 wenn possible == 0
    uncovered_tuples: list[tuple]  # Liste nicht abgedeckter, aber moeglicher Tupel
```

---

### 1.1 Mock-Daten (in der Testdatei als Module-Konstanten)

```python
# Einfaches 2x2 Modell — alle Paare abdeckbar
CATS_2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
}
# 2-wise moeglich: (a1,b1), (a1,b2), (a2,b1), (a2,b2) = 4
# Vollstaendige Abdeckung mit 4 Testfaellen:
TC_2X2_FULL = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
    {"A": "a2", "B": "b2"},
]

# 2x2 Modell mit einem fehlenden Paar
TC_2X2_MISSING_ONE = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
    # (a2, b2) fehlt
]

# 3-Kategorien-Modell 2x2x2
CATS_2X2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
    "C": ["c1", "c2"],
}
# 2-wise moeglich: C(3,2)=3 Paare * 2*2 = 12 Tupel
# 3-wise moeglich: 2*2*2 = 8 Tripel
TC_2X2X2_FULL = [
    {"A": "a1", "B": "b1", "C": "c1"},
    {"A": "a1", "B": "b1", "C": "c2"},
    {"A": "a1", "B": "b2", "C": "c1"},
    {"A": "a1", "B": "b2", "C": "c2"},
    {"A": "a2", "B": "b1", "C": "c1"},
    {"A": "a2", "B": "b1", "C": "c2"},
    {"A": "a2", "B": "b2", "C": "c1"},
    {"A": "a2", "B": "b2", "C": "c2"},
]

# Modell mit Ergebnis-Kategorie
CATS_WITH_RESULT = {
    "Browser": ["Chrome", "Firefox"],
    "OS": ["Windows", "Linux"],
    "Result": ["Pass", "Fail"],   # is_result=True
}

# Modell mit Fehlerwerten
CATS_WITH_ERROR = {
    "Browser": ["Chrome", "Firefox", "<Fehlerwert>"],
    "OS": ["Windows", "Linux"],
}
```

---

### 1.2 Testklassen und Tests

#### Klasse `TestCoverage1Wise`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.2.1 | `test_1wise_full_coverage` | `CATS_2X2`, `TC_2X2_FULL`, t=1 | `covered=4, possible=4, percentage=100.0` (a1,a2,b1,b2) |
| 1.2.2 | `test_1wise_partial_coverage` | `CATS_2X2`, nur `[{"A":"a1","B":"b1"}]`, t=1 | `covered=2, possible=4, percentage=50.0` (a1,b1 abgedeckt) |
| 1.2.3 | `test_1wise_zero_coverage` | `CATS_2X2`, `[]`, t=1 | `covered=0, possible=4, percentage=0.0` |
| 1.2.4 | `test_1wise_empty_categories` | `{}`, `[]`, t=1 | `covered=0, possible=0, percentage=0.0` |
| 1.2.5 | `test_1wise_single_category` | `{"A":["a1","a2"]}`, `[{"A":"a1"}]`, t=1 | `covered=1, possible=2, percentage=50.0` |

#### Klasse `TestCoverage2Wise`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.2.6 | `test_2wise_full_coverage_2x2` | `CATS_2X2`, `TC_2X2_FULL`, t=2 | `covered=4, possible=4, percentage=100.0` |
| 1.2.7 | `test_2wise_missing_one_pair` | `CATS_2X2`, `TC_2X2_MISSING_ONE`, t=2 | `covered=3, possible=4, percentage=75.0`; `uncovered_tuples=[(("A","B"),"a2","b2")]` |
| 1.2.8 | `test_2wise_three_categories` | `CATS_2X2X2`, `TC_2X2X2_FULL`, t=2 | `covered=12, possible=12, percentage=100.0` |
| 1.2.9 | `test_2wise_partial_three_categories` | `CATS_2X2X2`, nur erste 4 TCs, t=2 | Konkreter covered-Wert (manuell berechnen: welche Paare sind in den 4 TCs enthalten) |

**Manuelle Berechnung fuer 1.2.9:**
- TC1: (a1,b1), (a1,c1), (b1,c1)
- TC2: (a1,b1), (a1,c2), (b1,c2)
- TC3: (a1,b2), (a1,c1), (b2,c1)
- TC4: (a1,b2), (a1,c2), (b2,c2)
- Unique A-B: (a1,b1), (a1,b2) → 2 von 4
- Unique A-C: (a1,c1), (a1,c2) → 2 von 4
- Unique B-C: (b1,c1), (b1,c2), (b2,c1), (b2,c2) → 4 von 4
- **covered=8, possible=12, percentage=66.67**

#### Klasse `TestCoverage3Wise`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.2.10 | `test_3wise_full_coverage` | `CATS_2X2X2`, `TC_2X2X2_FULL`, t=3 | `covered=8, possible=8, percentage=100.0` |
| 1.2.11 | `test_3wise_partial` | `CATS_2X2X2`, nur erste 4 TCs, t=3 | covered=4, possible=8, percentage=50.0 |
| 1.2.12 | `test_3wise_two_categories_only` | `CATS_2X2`, t=3 | `covered=4, possible=4, percentage=100.0` (t>=n → kartesisch) |

#### Klasse `TestCoverageWithRules`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.2.13 | `test_forbidden_pair_excluded_from_possible` | `CATS_2X2`, `TC_2X2_FULL` minus (a2,b2), RuleEngine mit `ForbiddenRule("A","a2","B","b2")`, t=2 | `covered=3, possible=3, percentage=100.0, excluded_by_rules=1`. Das Paar (a2,b2) ist ausgeschlossen und zaehlt nicht zum Nenner. |
| 1.2.14 | `test_forbidden_pair_uncovered_vs_excluded` | `CATS_2X2`, `TC_2X2_MISSING_ONE` (fehlend: a2,b2), RuleEngine mit `ForbiddenRule("A","a2","B","b2")`, t=2 | `covered=3, possible=3, percentage=100.0, excluded_by_rules=1`. Das fehlende Paar war ohnehin verboten. |
| 1.2.15 | `test_combine_rule_excludes_pairs` | `CATS_2X2`, `TC_2X2_FULL`, `CombineRule("A","a1","B",["b1"])` (a1 darf nur mit b1), t=2 | `covered=3, possible=3, percentage=100.0, excluded_by_rules=1`. (a1,b2) ausgeschlossen. |
| 1.2.16 | `test_dependency_rule_no_exclusion` | `CATS_2X2`, `TC_2X2_FULL`, `DependencyRule("A","a1","B","b1")`, t=2 | `covered=4, possible=4, percentage=100.0, excluded_by_rules=0`. Dependency-Regeln schliessen Tupel nicht aus. |
| 1.2.17 | `test_multiple_forbidden_rules` | `CATS_2X2`, `TC_2X2_FULL` minus (a1,b1) und (a2,b2), zwei ForbiddenRules, t=2 | `covered=2, possible=2, percentage=100.0, excluded_by_rules=2` |

#### Klasse `TestCoverageResultCategories`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.2.18 | `test_result_category_ignored_in_coverage` | `CATS_WITH_RESULT`, alle 8 Kombinationen, `result_category_names=["Result"]`, t=2 | Nur Paare zwischen Browser und OS zaehlen: `covered=4, possible=4, percentage=100.0`. Result-Kategorie wird ignoriert. |
| 1.2.19 | `test_result_category_ignored_1wise` | `CATS_WITH_RESULT`, alle 8, `result_category_names=["Result"]`, t=1 | Nur Browser+OS Werte zaehlen: `covered=4, possible=4, percentage=100.0` (Chrome,Firefox,Windows,Linux) |

#### Klasse `TestCoverageErrorValues`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.2.20 | `test_error_values_counted_in_coverage` | `CATS_WITH_ERROR`, TCs mit "<Fehlerwert>", t=2 | Fehlerwerte werden mitgezahlt: Paar (Fehlerwert, Windows) zaehlt als abgedeckt |
| 1.2.21 | `test_error_value_full_coverage` | `CATS_WITH_ERROR`, alle 6 Paare (3*2), t=2 | `covered=6, possible=6, percentage=100.0` |

#### Klasse `TestCoverageEdgeCases`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.2.22 | `test_empty_testcases` | `CATS_2X2`, `[]`, t=2 | `covered=0, possible=4, percentage=0.0` |
| 1.2.23 | `test_empty_categories` | `{}`, `[]`, t=2 | `covered=0, possible=0, percentage=0.0` |
| 1.2.24 | `test_single_value_per_category` | `{"A":["a1"],"B":["b1"]}`, `[{"A":"a1","B":"b1"}]`, t=2 | `covered=1, possible=1, percentage=100.0` |
| 1.2.25 | `test_uncovered_tuples_sorted` | `CATS_2X2`, `TC_2X2_MISSING_ONE`, t=2 | `uncovered_tuples` ist sortiert (alphabetisch nach Kategorien, dann Werten) |
| 1.2.26 | `test_percentage_rounding` | `CATS_2X2`, `[{"A":"a1","B":"b1"}]`, t=2 | `percentage=25.0` (1/4) |
| 1.2.27 | `test_one_third_coverage` | Modell 3x3=9 Paare, nur 3 abgedeckt, t=2 | `percentage=33.33` (auf 2 Dezimalstellen gerundet) |

---

### 1.3 Heatmap-spezifische Unit-Tests

**Zusaetzliche Funktion:** `compute_heatmap(cat_a, cat_b, testcases, rule_engine)`

```python
def compute_heatmap(
    cat_a: str,
    cat_b: str,
    testcases: list[dict[str, str]],
    categories: dict[str, list[str]],
    rule_engine: RuleEngine | None = None,
) -> HeatmapData:
    ...

@dataclass
class HeatmapData:
    rows: list[str]           # Werte von cat_a
    cols: list[str]           # Werte von cat_b
    cells: dict[tuple[str,str], CellData]

@dataclass
class CellData:
    count: int                # Anzahl Testfaelle mit diesem Paar
    status: str               # "covered" | "uncovered" | "excluded"
    testcase_ids: list[int]   # IDs der zugehoerigen Testfaelle (optional, -1 wenn rein rechnerisch)
```

#### Klasse `TestHeatmapCalculation`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 1.3.1 | `test_heatmap_basic_2x2` | `CATS_2X2`, `TC_2X2_FULL`, cat_a="A", cat_b="B" | `rows=["a1","a2"]`, `cols=["b1","b2"]`, alle 4 Zellen `count>=1, status="covered"` |
| 1.3.2 | `test_heatmap_uncovered_cell` | `CATS_2X2`, `TC_2X2_MISSING_ONE`, cat_a="A", cat_b="B" | Zelle (a2,b2): `count=0, status="uncovered"` |
| 1.3.3 | `test_heatmap_excluded_cell` | `CATS_2X2`, `TC_2X2_FULL` minus (a2,b2), `ForbiddenRule("A","a2","B","b2")` | Zelle (a2,b2): `count=0, status="excluded"` (Symbol ⊘) |
| 1.3.4 | `test_heatmap_cell_count_multiple` | `CATS_2X2`, 3x `[{"A":"a1","B":"b1"}]` + andere | Zelle (a1,b1): `count=3` |
| 1.3.5 | `test_heatmap_asymmetric_categories` | `{"A":["a1","a2","a3"], "B":["b1"]}`, alle 3 TCs | `rows=["a1","a2","a3"]`, `cols=["b1"]`, 3 Zellen covered |
| 1.3.6 | `test_heatmap_unknown_category` | `CATS_2X2`, cat_a="X" (nicht vorhanden) | Raises `ValueError` |

---

## 2. Backend API-Tests: `tests/test_req6008_coverage_api.py`

**Endpoint:** `GET /api/generations/{gid}/coverage`

**Response-Schema:**
```json
{
    "generation_id": 1,
    "coverage_1wise": {"covered": 4, "possible": 4, "percentage": 100.0, "excluded_by_rules": 0},
    "coverage_2wise": {"covered": 4, "possible": 4, "percentage": 100.0, "excluded_by_rules": 0},
    "coverage_3wise": {"covered": 8, "possible": 8, "percentage": 100.0, "excluded_by_rules": 0},
    "heatmap": {
        "categories": ["Browser", "OS"],
        "pairs": [
            {
                "cat_a": "Browser",
                "cat_b": "OS",
                "coverage_pct": 100.0,
                "covered": 4,
                "possible": 4
            }
        ]
    },
    "uncovered_tuples_2wise": [],
    "cached": false
}
```

#### Klasse `TestCoverageAPI`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 2.1 | `test_coverage_endpoint_returns_200` | Projekt + Kategorien + Werte + Generierung (pairwise) | `200`, Response hat `coverage_2wise` |
| 2.2 | `test_coverage_endpoint_404` | Nicht-existentes gid | `404` |
| 2.3 | `test_coverage_2wise_values_correct` | 2x2 Modell, pairwise-Generierung, alle 4 TCs | `coverage_2wise.covered=4, .possible=4, .percentage=100.0` |
| 2.4 | `test_coverage_with_forbidden_rule` | Projekt mit ForbiddenRule, Generierung | `excluded_by_rules > 0`, `possible` reduziert |
| 2.5 | `test_coverage_result_category_excluded` | Projekt mit `is_result=True` Kategorie | Result-Kategorie nicht in Coverage-Berechnung |
| 2.6 | `test_coverage_uncached_first_call` | Generierung ohne `coverage_meta` | `cached=false`, `coverage_meta` wird gespeichert |
| 2.7 | `test_coverage_cached_second_call` | Zweiter Aufruf nach 2.6 | `cached=true` |
| 2.8 | `test_heatmap_pair_in_response` | 3 Kategorien | `heatmap.pairs` hat C(3,2)=3 Eintraege |
| 2.9 | `test_uncovered_tuples_in_response` | Generierung mit Luecken | `uncovered_tuples_2wise` nicht leer, sortiert |
| 2.10 | `test_coverage_generation_list_includes_2wise_pct` | `GET /api/projects/{pid}/generations` | Jede Generation hat Feld `coverage_2wise_pct` |
| 2.11 | `test_coverage_3wise_on_request` | `GET /api/generations/{gid}/coverage?t=3` | `coverage_3wise` im Response |
| 2.12 | `test_coverage_3wise_size_limit` | >5 Mio Tripel moeglich | `400` oder Warnung im Response, kein Timeout |

---

## 3. Frontend Vitest-Tests: `frontend/src/components/__tests__/CoverageHeatmap.test.tsx`

**Komponente:** `<CoverageHeatmap generationId={...} catA="..." catB="..." />`

**Mock-API:**
```typescript
vi.mock("../../api/client", () => ({
  coverageApi: {
    getCoverage: vi.fn(),
    getHeatmap: vi.fn(),
    getUncoveredTuples: vi.fn(),
  },
}));
```

#### Klasse `CoverageHeatmap`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 3.1 | `renders_heatmap_grid` | Mock: 2x2, alle covered | 4 Zellen sichtbar, grid-Layout |
| 3.2 | `shows_cell_count` | Mock: Zelle (a1,b1) count=3 | Zelle zeigt "3" |
| 3.3 | `shows_uncovered_symbol` | Mock: Zelle (a2,b2) status="uncovered" | Zelle zeigt "✕" |
| 3.4 | `shows_excluded_symbol` | Mock: Zelle (a1,b2) status="excluded" | Zelle zeigt "⊘" |
| 3.5 | `color_intensity_by_count` | Mock: Zellen mit count 1, 3, 5 | CSS-Klassen oder inline-Styles unterscheiden Intensitaet |
| 3.6 | `click_cell_filters_testcases` | Klick auf Zelle (a1,b1) | dispatch/filter-Aktion mit korrekten Parametern |
| 3.7 | `click_uncovered_shows_hint` | Klick auf ✕-Zelle | "Mit REQ-6009 Luecken schliessen" sichtbar |
| 3.8 | `legend_visible` | Render | Legende mit Symbolen und Erklarungen sichtbar |
| 3.9 | `colorblind_safe_palette` | Render | Farbwerte sind farbenblind-tauglich (z.B. Okabe-Ito, Viridis) |
| 3.10 | `category_selectors` | 3+ Kategorien | Dropdowns fuer catA und catB, catA != catB enforced |
| 3.11 | `switches_categories_on_select` | Wechsel catA/catB | Heatmap neu geladen, Achsen getauscht |

---

## 4. Frontend Vitest-Tests: `frontend/src/components/__tests__/CoverageOverviewMatrix.test.tsx`

**Komponente:** `<CoverageOverviewMatrix generationId={...} />`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 4.1 | `renders_tiles_for_all_pairs` | 4 Kategorien | C(4,2)=6 Kacheln |
| 4.2 | `tile_shows_coverage_percentage` | Mock: Paar A-B 75% | Kachel zeigt "75%" |
| 4.3 | `tile_color_by_coverage` | 100%, 75%, 50%, 25% | Unterschiedliche Farbtone |
| 4.4 | `click_tile_opens_heatmap` | Klick auf Kachel A-B | `<CoverageHeatmap catA="A" catB="B">` gerendert |
| 4.5 | `uncovered_tuples_button` | Luecken vorhanden | Button "Nicht abgedeckte Tupel" sichtbar |
| 4.6 | `csv_export_button` | Render | Button "CSV-Export" sichtbar |
| 4.7 | `csv_export_download` | Klick CSV-Export | Download-Trigger mit korrektem Content |

---

## 5. Performance-Tests: `tests/test_req6008_coverage_performance.py`

| # | Testname | Setup | Expectation |
|---|----------|-------|-------------|
| 5.1 | `test_2wise_30x10x1000_under_3s` | 30 Kategorien, 10 Werte je, 1000 Testfaelle | `calculate_coverage(..., t=2)` in < 3s |
| 5.2 | `test_2wise_with_rules_under_3s` | 30x10, 1000 TCs, 5 ForbiddenRules | < 3s |
| 5.3 | `test_3wise_size_check_aborts` | 30x10 → >5 Mio Tripel moeglich | Abbruch mit Warnung, keine Exception |
| 5.4 | `test_heatmap_30x30_pair_under_1s` | compute_heatmap fuer ein Paar aus 30x10 | < 1s |

**Test-Setup fuer 5.1:**
```python
def _generate_large_model(num_cats=30, vals_per_cat=10, num_testcases=1000):
    rng = random.Random(42)
    categories = {}
    for i in range(num_cats):
        cat_name = f"Cat{i}"
        categories[cat_name] = [f"v{j}" for j in range(vals_per_cat)]
    
    testcases = []
    for _ in range(num_testcases):
        tc = {}
        for cat_name, vals in categories.items():
            tc[cat_name] = rng.choice(vals)
        testcases.append(tc)
    
    return categories, testcases
```

---

## 6. Edge Cases (zusammengefasst)

| # | Szenario | Erwartetes Verhalten |
|---|----------|---------------------|
| E1 | Keine Kategorien | `possible=0, percentage=0.0` |
| E2 | Keine Testfaelle | `covered=0, percentage=0.0` |
| E3 | Alle Paare durch Regeln ausgeschlossen | `covered=0, possible=0, excluded=N, percentage=0.0` |
| E4 | 1 Kategorie | 2-wise degeneriert zu 1-wise (alle "Paare" mit sich selbst) |
| E5 | t > Anzahl Kategorien | Kartesisches Produkt als Basis |
| E6 | Ergebnis-Kategorie als einzige Kategorie | Ignoriert → `possible=0` |
| E7 | Dependency-Regeln aendern Werte nach Generierung | Coverage basiert auf *finalen* Werten nach Dependency-Anwendung |
| E8 | Leere Werte in Testfaellen (Result-Kategorien) | Leere Werte in ignorierten Kategorien werden nicht als Tupel zaehlt |
| E9 | Duplizierte Testfaelle | Jeder TC zaehlt einzeln fuer Zell-Count, Tupel-Coverage ist boolesch (abgedeckt oder nicht) |
| E10 | 3-wise bei sehr groessem Modell (>5 Mio) | Abbruch mit Hinweis, kein Crash |

---

## 7. Testausfuehrungsreihenfolge (RED-GREEN)

```
Phase 1: Backend Unit-Tests (RED)
  ├─ test_req6008_coverage_calc.py — alle Tests FAIL (Modul existiert nicht)
  └─ Implementierung → GREEN

Phase 2: Backend API (RED)
  ├─ test_req6008_coverage_api.py — alle Tests FAIL (Endpoint existiert nicht)
  └─ Implementierung → GREEN

Phase 3: Frontend Vitest (RED)
  ├─ CoverageHeatmap.test.tsx — FAIL (Komponente existiert nicht)
  ├─ CoverageOverviewMatrix.test.tsx — FAIL
  └─ Implementierung → GREEN

Phase 4: Performance (RED)
  ├─ test_req6008_coverage_performance.py — FAIL oder Timeout
  └─ Optimierung → GREEN (< 3s)

Phase 5: Integration & Regression
  ├─ Alle existierenden Tests noch GREEN?
  └─ coverage_meta-Storage in Generation-Modell
```

---

## 8. Anhaengigkeit zu anderen REQs

| REQ | Beziehung |
|-----|-----------|
| REQ-6001 | Constraints/ForbiddenRules beeinflussen "moeglich"-Zaehler |
| REQ-4016 | `is_result=True` Kategorien werden ignoriert |
| REQ-3018 | Fehlerwerte werden mitgezählt |
| REQ-6009 | "Luecken schliessen"-Hinweis in Heatmap-Zellen |
| REQ-3039 | T-Wise-Generierung liefert Input fuer Coverage |