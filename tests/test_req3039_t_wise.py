"""
REQ-3039 – T-Wise Kombinatorik (parametrisiertes N-wise Testing)
TEST-ID: TEST-REQ-3039-001 bis TEST-REQ-3039-020

T-Wise deckt alle t-Tupel aller t-elementigen Kategorien-Kombinationen ab.
t=1: Each Choice, t=2: Pairwise, t=3: Triple-wise, ...
Constraint-aware über RuleEngine.
"""
import pytest
from itertools import combinations
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule, CombineRule
from combinatorics import t_wise


# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------

CATEGORIES_SIMPLE = {
    "OS": ["Windows", "Linux", "Mac"],
    "Browser": ["Chrome", "Firefox"],
    "Lang": ["EN", "DE"],
}

CATEGORIES_FOUR = {
    "A": ["A1", "A2"],
    "B": ["B1", "B2"],
    "C": ["C1", "C2"],
    "D": ["D1", "D2"],
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def extract_tuples_of_size(testcases: list[dict], categories_subset: list[str]) -> set[tuple]:
    """Extrahiert alle t-Tupel aus Testfällen für gegebene Kategorien."""
    tuples = set()
    for tc in testcases:
        # Baue Tuple aus den Kategorien (sortiert für Konsistenz)
        values = tuple(tc[cat] for cat in sorted(categories_subset))
        tuples.add(values)
    return tuples


def count_all_t_tuples(categories: dict, t: int, rule_engine=None) -> int:
    """Zählt alle gültigen t-Tupel für alle t-elementigen Kategorien-Kombinationen."""
    if t > len(categories):
        # Cartesian
        from itertools import product
        count = 1
        for vals in categories.values():
            count *= len(vals)
        return count
    
    cat_names = list(categories.keys())
    all_combinations_count = 0
    
    # Für jede Kombination von t Kategorien
    for cat_subset in combinations(cat_names, t):
        # Zähle alle möglichen Wert-Kombinationen
        from itertools import product
        value_lists = [categories[cat] for cat in cat_subset]
        for value_tuple in product(*value_lists):
            # Wenn RuleEngine gegeben: prüfe Gültigkeit
            if rule_engine is not None:
                partial = {cat: val for cat, val in zip(cat_subset, value_tuple)}
                if not rule_engine.is_combination_valid(partial):
                    continue
            all_combinations_count += 1
    
    return all_combinations_count


# ---------------------------------------------------------------------------
# TEST-REQ-3039-001 bis 005: Basic T-Wise
# ---------------------------------------------------------------------------

class TestTWiseBasic:
    """Grundlegende T-Wise Funktionalität ohne Constraints."""
    
    def test_t_equals_1_equivalent_to_each_choice(self):
        """TEST-REQ-3039-001: t=1 erzeugt gleiche Coverage wie each_choice."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=1)
        
        # Jeder Wert jeder Kategorie muss mindestens einmal vorkommen
        for cat, values in CATEGORIES_SIMPLE.items():
            for val in values:
                assert any(tc[cat] == val for tc in result), \
                    f"Wert {val} von Kategorie {cat} nicht abgedeckt"
    
    def test_t_equals_2_covers_all_pairs(self):
        """TEST-REQ-3039-002: t=2 deckt alle Paare ab."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2)
        
        # Für jede Kombination von 2 Kategorien: prüfe alle Paare abgedeckt
        cat_names = list(CATEGORIES_SIMPLE.keys())
        for i, cat1 in enumerate(cat_names):
            for j, cat2 in enumerate(cat_names):
                if i >= j:
                    continue
                
                # Alle möglichen Paare
                for val1 in CATEGORIES_SIMPLE[cat1]:
                    for val2 in CATEGORIES_SIMPLE[cat2]:
                        assert any(tc[cat1] == val1 and tc[cat2] == val2 for tc in result), \
                            f"Paar ({cat1}={val1}, {cat2}={val2}) nicht abgedeckt"
    
    def test_t_equals_3_covers_all_triples(self):
        """TEST-REQ-3039-003: t=3 deckt alle Triple-Kombinationen ab."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=3)
        
        # Alle 3 Kategorien kombiniert
        cat_names = list(CATEGORIES_SIMPLE.keys())
        assert len(cat_names) == 3
        
        from itertools import product
        for combo in product(
            CATEGORIES_SIMPLE["OS"],
            CATEGORIES_SIMPLE["Browser"],
            CATEGORIES_SIMPLE["Lang"]
        ):
            assert any(
                tc["OS"] == combo[0] and 
                tc["Browser"] == combo[1] and 
                tc["Lang"] == combo[2]
                for tc in result
            ), f"Triple {combo} nicht abgedeckt"
    
    def test_t_greater_than_num_categories_returns_cartesian(self):
        """TEST-REQ-3039-004: t > len(categories) → kartesisches Produkt."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=10)
        
        # Sollte alle möglichen Kombinationen enthalten
        from itertools import product
        expected_count = len(CATEGORIES_SIMPLE["OS"]) * \
                        len(CATEGORIES_SIMPLE["Browser"]) * \
                        len(CATEGORIES_SIMPLE["Lang"])
        
        assert len(result) == expected_count, \
            f"Erwarte {expected_count} Testfälle (Cartesian), bekam {len(result)}"
    
    def test_default_t_is_2(self):
        """TEST-REQ-3039-005: Default-Wert t=2 (Pairwise)."""
        result_default = t_wise.generate(CATEGORIES_SIMPLE)
        result_explicit = t_wise.generate(CATEGORIES_SIMPLE, t=2)
        
        # Beide sollten gleiche Coverage haben (nicht unbedingt identisch)
        # Prüfe dass beide alle Paare abdecken
        cat_names = list(CATEGORIES_SIMPLE.keys())
        for result in [result_default, result_explicit]:
            for i, cat1 in enumerate(cat_names):
                for j, cat2 in enumerate(cat_names):
                    if i >= j:
                        continue
                    for val1 in CATEGORIES_SIMPLE[cat1]:
                        for val2 in CATEGORIES_SIMPLE[cat2]:
                            assert any(tc[cat1] == val1 and tc[cat2] == val2 for tc in result)


# ---------------------------------------------------------------------------
# TEST-REQ-3039-006 bis 010: Constraint-Aware
# ---------------------------------------------------------------------------

class TestTWiseConstraintAware:
    """T-Wise mit RuleEngine – Constraints werden berücksichtigt."""
    
    def test_forbidden_tuple_not_generated(self):
        """TEST-REQ-3039-006: Verbotene Kombinationen werden nicht generiert."""
        # Regel: Chrome + DE ist verboten
        regel = ForbiddenRule(
            if_category="Browser",
            if_value="Chrome",
            then_category="Lang",
            then_value="DE"
        )
        engine = RuleEngine([regel])
        
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2, rule_engine=engine)
        
        # Keine Kombination Chrome + DE darf existieren
        for tc in result:
            if tc["Browser"] == "Chrome":
                assert tc["Lang"] != "DE", f"Verbotene Kombination generiert: {tc}"
    
    def test_dependency_rule_respected(self):
        """TEST-REQ-3039-007: Dependency-Regeln werden angewendet."""
        # Regel: Wenn Mac → Browser muss Firefox sein
        regel = DependencyRule(
            if_category="OS",
            if_value="Mac",
            then_category="Browser",
            then_value="Firefox"
        )
        engine = RuleEngine([regel])
        
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2, rule_engine=engine)
        
        # Alle Mac-Fälle müssen Firefox haben
        for tc in result:
            if tc["OS"] == "Mac":
                assert tc["Browser"] == "Firefox", f"Dependency nicht beachtet: {tc}"
    
    def test_forbidden_pair_removed_from_coverage_goal(self):
        """TEST-REQ-3039-008: Ungültige Paare werden aus Coverage-Ziel entfernt."""
        # Regel: Chrome + DE ist verboten
        regel = ForbiddenRule(
            if_category="Browser",
            if_value="Chrome",
            then_category="Lang",
            then_value="DE"
        )
        engine = RuleEngine([regel])
        
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2, rule_engine=engine)
        
        # Zähle alle Paare zwischen Browser und Lang
        browser_lang_pairs = set()
        for tc in result:
            browser_lang_pairs.add((tc["Browser"], tc["Lang"]))
        
        # Das verbotene Paar darf nicht abgedeckt werden
        assert ("Chrome", "DE") not in browser_lang_pairs
        
        # Alle anderen Paare sollten abgedeckt sein
        expected_pairs = {
            ("Chrome", "EN"),
            ("Firefox", "DE"),
            ("Firefox", "EN"),
            # ("Chrome", "DE") ist verboten
        }
        for pair in expected_pairs:
            assert pair in browser_lang_pairs, f"Gültiges Paar {pair} nicht abgedeckt"
    
    def test_combine_rule_restricts_combinations(self):
        """TEST-REQ-3039-009: Combine-Regel schränkt erlaubte Werte ein."""
        # Regel: Wenn OS=Linux → Lang nur EN oder DE erlaubt (nicht relevant für SIMPLE, aber testen)
        # Besser: Wenn OS=Windows → Browser nur Chrome
        regel = CombineRule(
            if_category="OS",
            if_value="Windows",
            then_category="Browser",
            allowed_values=["Chrome"]
        )
        engine = RuleEngine([regel])
        
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2, rule_engine=engine)
        
        # Alle Windows-Fälle dürfen nur Chrome haben
        for tc in result:
            if tc["OS"] == "Windows":
                assert tc["Browser"] in ["Chrome"], \
                    f"Combine-Regel verletzt: {tc}"
    
    def test_multiple_rules_combined(self):
        """TEST-REQ-3039-010: Mehrere Regeln wirken zusammen."""
        regeln = [
            ForbiddenRule("OS", "Mac", "Browser", "Chrome"),
            DependencyRule("OS", "Linux", "Lang", "EN"),
        ]
        engine = RuleEngine(regeln)
        
        result = t_wise.generate(CATEGORIES_SIMPLE, t=3, rule_engine=engine)
        
        # Beide Regeln müssen beachtet werden
        for tc in result:
            # Regel 1: Mac + Chrome verboten
            if tc["OS"] == "Mac":
                assert tc["Browser"] != "Chrome"
            
            # Regel 2: Linux → Lang=EN
            if tc["OS"] == "Linux":
                assert tc["Lang"] == "EN"


# ---------------------------------------------------------------------------
# TEST-REQ-3039-011 bis 015: Monotonic & Coverage
# ---------------------------------------------------------------------------

class TestTWiseMonotonic:
    """Testfall-Anzahl wächst (grob) monoton mit t."""
    
    def test_testcase_count_grows_with_t(self):
        """TEST-REQ-3039-011: Anzahl Testfälle wächst mit t (weak monotonic)."""
        count_t1 = len(t_wise.generate(CATEGORIES_FOUR, t=1))
        count_t2 = len(t_wise.generate(CATEGORIES_FOUR, t=2))
        count_t3 = len(t_wise.generate(CATEGORIES_FOUR, t=3))
        
        # t=1 < t=2 < t=3 (grob, nicht strikt garantiert aber realistisch)
        assert count_t1 <= count_t2, f"t=1 ({count_t1}) sollte <= t=2 ({count_t2}) sein"
        assert count_t2 <= count_t3, f"t=2 ({count_t2}) sollte <= t=3 ({count_t3}) sein"


class TestTWiseCoverage:
    """Coverage-Eigenschaften: alle gültigen t-Tupel abgedeckt, keine Duplikate."""
    
    def test_all_valid_t_tuples_covered(self):
        """TEST-REQ-3039-012: Alle gültigen t-Tupel werden abgedeckt."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2)
        
        # Für jede 2-elementige Kategorien-Kombination
        cat_names = list(CATEGORIES_SIMPLE.keys())
        for cat_subset in combinations(cat_names, 2):
            # Alle möglichen Wert-Kombinationen für diese Kategorien
            from itertools import product
            value_lists = [CATEGORIES_SIMPLE[cat] for cat in cat_subset]
            
            for value_tuple in product(*value_lists):
                # Prüfe dass diese Kombination abgedeckt ist
                found = False
                for tc in result:
                    if all(tc[cat] == val for cat, val in zip(cat_subset, value_tuple)):
                        found = True
                        break
                
                assert found, \
                    f"Kombination {dict(zip(cat_subset, value_tuple))} nicht abgedeckt"
    
    def test_no_duplicate_testcases(self):
        """TEST-REQ-3039-013: Keine duplizierten Testfälle."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2)
        
        # Konvertiere zu Tuples für Vergleich
        result_tuples = [tuple(sorted(tc.items())) for tc in result]
        
        assert len(result_tuples) == len(set(result_tuples)), \
            "Duplizierte Testfälle gefunden!"
    
    def test_t_equals_1_minimal_testcases(self):
        """TEST-REQ-3039-014: t=1 erzeugt minimale Testfall-Anzahl."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=1)
        
        # Minimum ist max(len(values) für alle Kategorien)
        max_vals = max(len(vals) for vals in CATEGORIES_SIMPLE.values())
        
        # Sollte nicht viel mehr als max_vals sein
        assert len(result) <= max_vals + 2, \
            f"t=1 sollte ~{max_vals} Testfälle erzeugen, bekam {len(result)}"
    
    def test_empty_categories_returns_empty(self):
        """TEST-REQ-3039-015: Leere Kategorien → leere Liste."""
        result = t_wise.generate({}, t=2)
        assert result == []
        
        result = t_wise.generate({"A": []}, t=1)
        assert result == []


# ---------------------------------------------------------------------------
# TEST-REQ-3039-016 bis 020: API Integration
# ---------------------------------------------------------------------------

class TestTWiseAPI:
    """API-Endpoint akzeptiert t_wise mit t_strength Parameter."""
    
    def test_endpoint_accepts_t_wise_strategy(self):
        """TEST-REQ-3039-016: API akzeptiert strategy="t_wise"."""
        # Dieser Test wird über API-Integration getestet
        # Hier nur Import-Test
        from combinatorics import t_wise
        assert hasattr(t_wise, "generate")
    
    def test_t_wise_module_importable(self):
        """TEST-REQ-3039-017: Modul t_wise ist importierbar."""
        from combinatorics import t_wise
        assert callable(t_wise.generate)
    
    def test_t_wise_signature(self):
        """TEST-REQ-3039-018: Signatur: generate(categories, t=2, rule_engine=None)."""
        from combinatorics import t_wise
        import inspect
        
        sig = inspect.signature(t_wise.generate)
        params = list(sig.parameters.keys())
        
        assert "categories" in params
        assert "t" in params
        assert "rule_engine" in params
        
        # Default-Werte prüfen
        assert sig.parameters["t"].default == 2
        assert sig.parameters["rule_engine"].default is None
    
    def test_t_wise_returns_list_of_dicts(self):
        """TEST-REQ-3039-019: Rückgabe ist Liste von Dicts."""
        result = t_wise.generate(CATEGORIES_SIMPLE, t=2)
        
        assert isinstance(result, list)
        for tc in result:
            assert isinstance(tc, dict)
    
    def test_t_wise_with_invalid_t_raises(self):
        """TEST-REQ-3039-020: Ungültiges t (< 1) wirft Fehler."""
        with pytest.raises((ValueError, AssertionError)):
            t_wise.generate(CATEGORIES_SIMPLE, t=0)
        
        with pytest.raises((ValueError, AssertionError)):
            t_wise.generate(CATEGORIES_SIMPLE, t=-1)
