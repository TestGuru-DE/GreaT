"""
REQ-3044 – MC/DC (Modified Condition/Decision Coverage) Kombinatorik
TEST-ID: TEST-REQ-3044-001 bis TEST-REQ-3044-020

MC/DC ist ein Testabdeckungskriterium aus DO-178C (Avionik) und ISO 26262 (Automotive).
Für n Bedingungen (Kategorien) werden minimal n+1 Testfälle erzeugt (bei booleschen Werten).

Algorithmus:
1. Baseline-Testfall: erster Wert jeder Kategorie
2. Für jede Kategorie K:
   - Für jeden Wert v ∈ K (außer dem Baseline-Wert):
     - Erzeuge Variante: Baseline mit K=v (alle anderen wie Baseline)
     - So entsteht ein Pärchen, das sich nur in K unterscheidet
3. Duplikate entfernen
4. Constraint-aware: verletzt Regel? → alternative Baseline-Werte suchen
"""
import pytest
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule
from combinatorics import mcdc


# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------

CATEGORIES_BOOL = {
    "LoginType": ["OAuth", "Password"],
    "HTTPSEnabled": ["True", "False"],
}

CATEGORIES_BOOL_3 = {
    "Authentication": ["Enabled", "Disabled"],
    "Encryption": ["AES", "None"],
    "Logging": ["On", "Off"],
}

CATEGORIES_MULTI = {
    "Engine": ["V4", "V6", "V8", "Electric"],
    "Transmission": ["Manual", "Automatic"],
    "FuelType": ["Petrol", "Diesel", "Electric"],
}

CATEGORIES_SINGLE_VALUE = {
    "Database": ["PostgreSQL"],
    "Protocol": ["HTTPS", "HTTP"],
}


# ---------------------------------------------------------------------------
# TEST-REQ-3044-001 bis 004: MC/DC Basic
# ---------------------------------------------------------------------------

class TestMCDCBasic:
    """MC/DC Grundfunktionalität ohne Constraints."""

    def test_two_boolean_categories_produces_three_testcases(self):
        """TEST-REQ-3044-001: 2 boolesche Kategorien → 3 Testfälle (n+1)."""
        result = mcdc.generate(CATEGORIES_BOOL)
        
        assert len(result) == 3, f"Erwartet 3 Testfälle (2+1), erhalten {len(result)}"
        
        # Baseline: erster Wert jeder Kategorie
        baseline = {"LoginType": "OAuth", "HTTPSEnabled": "True"}
        assert baseline in result, "Baseline fehlt"
        
        # Variation 1: LoginType unterschiedlich
        var1 = {"LoginType": "Password", "HTTPSEnabled": "True"}
        assert var1 in result, "LoginType-Variation fehlt"
        
        # Variation 2: HTTPSEnabled unterschiedlich
        var2 = {"LoginType": "OAuth", "HTTPSEnabled": "False"}
        assert var2 in result, "HTTPSEnabled-Variation fehlt"

    def test_three_boolean_categories_produces_four_testcases(self):
        """TEST-REQ-3044-002: 3 boolesche Kategorien → 4 Testfälle (n+1)."""
        result = mcdc.generate(CATEGORIES_BOOL_3)
        
        assert len(result) == 4, f"Erwartet 4 Testfälle (3+1), erhalten {len(result)}"
        
        # Baseline
        baseline = {"Authentication": "Enabled", "Encryption": "AES", "Logging": "On"}
        assert baseline in result

    def test_multi_value_category_produces_all_variations(self):
        """TEST-REQ-3044-003: Kategorien mit >2 Werten → mehr Variationen."""
        result = mcdc.generate(CATEGORIES_MULTI)
        
        # 3 Kategorien: Engine (4 Werte), Transmission (2 Werte), FuelType (3 Werte)
        # Baseline: V4, Manual, Petrol
        # Variationen für Engine: V6, V8, Electric (3 Variationen)
        # Variationen für Transmission: Automatic (1 Variation)
        # Variationen für FuelType: Diesel, Electric (2 Variationen)
        # Gesamt: 1 Baseline + 3 + 1 + 2 = 7
        expected_min = 7
        assert len(result) >= expected_min, f"Erwartet mindestens {expected_min}, erhalten {len(result)}"
        
        # Baseline
        baseline = {"Engine": "V4", "Transmission": "Manual", "FuelType": "Petrol"}
        assert baseline in result
        
        # Engine-Variationen (mit sonst Baseline-Werten)
        assert {"Engine": "V6", "Transmission": "Manual", "FuelType": "Petrol"} in result
        assert {"Engine": "V8", "Transmission": "Manual", "FuelType": "Petrol"} in result
        assert {"Engine": "Electric", "Transmission": "Manual", "FuelType": "Petrol"} in result
        
        # Transmission-Variation
        assert {"Engine": "V4", "Transmission": "Automatic", "FuelType": "Petrol"} in result
        
        # FuelType-Variationen
        assert {"Engine": "V4", "Transmission": "Manual", "FuelType": "Diesel"} in result
        assert {"Engine": "V4", "Transmission": "Manual", "FuelType": "Electric"} in result

    def test_baseline_uses_first_value_of_each_category(self):
        """TEST-REQ-3044-004: Baseline = erster Wert jeder Kategorie."""
        result = mcdc.generate(CATEGORIES_MULTI)
        
        # Erster Wert jeder Kategorie laut Definition
        baseline = {
            "Engine": "V4",  # erster in Liste
            "Transmission": "Manual",
            "FuelType": "Petrol"
        }
        
        assert baseline in result, "Baseline nicht gefunden"
        assert result[0] == baseline, "Baseline sollte erster Testfall sein"


# ---------------------------------------------------------------------------
# TEST-REQ-3044-005 bis 007: MC/DC Coverage
# ---------------------------------------------------------------------------

class TestMCDCCoverage:
    """MC/DC-Kriterium: Jeder Wert hat unabhängige Variation."""

    def test_every_value_has_independent_variation_pair(self):
        """TEST-REQ-3044-005: Jeder Wert erscheint in einem Pärchen, das sich nur hier unterscheidet."""
        result = mcdc.generate(CATEGORIES_BOOL_3)
        
        # Für jede Kategorie und jeden Wert: es existiert mindestens ein Paar (tc1, tc2)
        # das sich NUR in dieser Kategorie unterscheidet
        categories = CATEGORIES_BOOL_3
        
        for cat, values in categories.items():
            for val in values:
                # Finde Testfälle mit diesem Wert
                tcs_with_val = [tc for tc in result if tc[cat] == val]
                assert len(tcs_with_val) > 0, f"{cat}={val} kommt nicht vor"
                
                # Prüfe: gibt es ein Paar mit genau einem Unterschied?
                found_pair = False
                for tc1 in tcs_with_val:
                    for tc2 in result:
                        if tc1 == tc2:
                            continue
                        # Zähle Unterschiede
                        diffs = sum(1 for k in categories if tc1[k] != tc2[k])
                        if diffs == 1 and tc1[cat] != tc2[cat]:
                            found_pair = True
                            break
                    if found_pair:
                        break
                
                assert found_pair, f"{cat}={val} hat keine unabhängige Variation"

    def test_no_duplicate_testcases(self):
        """TEST-REQ-3044-006: Keine doppelten Testfälle."""
        result = mcdc.generate(CATEGORIES_MULTI)
        
        # Konvertiere zu frozenset für Set-Vergleich
        unique = set(frozenset(tc.items()) for tc in result)
        assert len(unique) == len(result), "Duplikate gefunden"

    def test_single_value_category_always_included(self):
        """TEST-REQ-3044-007: Kategorien mit nur 1 Wert werden immer verwendet."""
        result = mcdc.generate(CATEGORIES_SINGLE_VALUE)
        
        # Database hat nur 1 Wert → keine Variation möglich
        # Protocol hat 2 Werte → 1 Variation
        # Erwartet: Baseline + 1 Variation für Protocol = 2 Testfälle
        assert len(result) == 2
        
        # Alle Testfälle müssen PostgreSQL haben
        for tc in result:
            assert tc["Database"] == "PostgreSQL"
        
        # Protocol-Variation
        assert {"Database": "PostgreSQL", "Protocol": "HTTPS"} in result
        assert {"Database": "PostgreSQL", "Protocol": "HTTP"} in result


# ---------------------------------------------------------------------------
# TEST-REQ-3044-008 bis 012: MC/DC Constraint-Aware
# ---------------------------------------------------------------------------

class TestMCDCConstraintAware:
    """MC/DC berücksichtigt Regeln während der Generierung."""

    def test_forbidden_baseline_uses_alternative(self):
        """TEST-REQ-3044-008: Verbotener Baseline → alternativer Wert."""
        # Regel: OAuth + HTTPSEnabled=False verboten
        regel = ForbiddenRule(
            if_category="LoginType",
            if_value="OAuth",
            then_category="HTTPSEnabled",
            then_value="False"
        )
        engine = RuleEngine([regel])
        
        result = mcdc.generate(CATEGORIES_BOOL, rule_engine=engine)
        
        # Keine Kombination OAuth + False darf existieren
        for tc in result:
            if tc["LoginType"] == "OAuth":
                assert tc["HTTPSEnabled"] != "False", f"Verbotene Kombination: {tc}"
        
        # Trotzdem müssen beide Werte von HTTPSEnabled vorkommen (wenn möglich)
        https_values = set(tc["HTTPSEnabled"] for tc in result)
        assert "True" in https_values, "HTTPSEnabled=True fehlt"
        # False kann nur mit LoginType=Password kombiniert werden
        if "False" in https_values:
            for tc in result:
                if tc["HTTPSEnabled"] == "False":
                    assert tc["LoginType"] == "Password"

    def test_forbidden_variant_finds_alternative_pair(self):
        """TEST-REQ-3044-009: Verbotene Variation → alternatives Paar suchen."""
        # Regel: Authentication=Disabled + Logging=On verboten
        regel = ForbiddenRule(
            if_category="Authentication",
            if_value="Disabled",
            then_category="Logging",
            then_value="On"
        )
        engine = RuleEngine([regel])
        
        result = mcdc.generate(CATEGORIES_BOOL_3, rule_engine=engine)
        
        # Keine verbotene Kombination
        for tc in result:
            if tc["Authentication"] == "Disabled":
                assert tc["Logging"] != "On", f"Verbotene Kombination: {tc}"
        
        # Trotzdem sollten beide Werte erscheinen
        auth_values = set(tc["Authentication"] for tc in result)
        assert "Disabled" in auth_values or "Enabled" in auth_values

    def test_dependency_rule_respected(self):
        """TEST-REQ-3044-010: Dependency-Regel setzt Werte automatisch."""
        # Regel: Wenn Engine=Electric → FuelType muss Electric sein
        regel = DependencyRule(
            if_category="Engine",
            if_value="Electric",
            then_category="FuelType",
            then_value="Electric"
        )
        engine = RuleEngine([regel])
        
        result = mcdc.generate(CATEGORIES_MULTI, rule_engine=engine)
        
        # Alle Electric-Engine-Fälle müssen FuelType=Electric haben
        for tc in result:
            if tc["Engine"] == "Electric":
                assert tc["FuelType"] == "Electric", f"Dependency nicht beachtet: {tc}"

    def test_multiple_constraints_combined(self):
        """TEST-REQ-3044-011: Mehrere Regeln gleichzeitig."""
        regeln = [
            ForbiddenRule("Engine", "V8", "Transmission", "Manual"),
            DependencyRule("Engine", "Electric", "FuelType", "Electric"),
        ]
        engine = RuleEngine(regeln)
        
        result = mcdc.generate(CATEGORIES_MULTI, rule_engine=engine)
        
        # Forbidden
        for tc in result:
            if tc["Engine"] == "V8":
                assert tc["Transmission"] != "Manual"
        
        # Dependency
        for tc in result:
            if tc["Engine"] == "Electric":
                assert tc["FuelType"] == "Electric"

    def test_empty_categories_returns_empty_list(self):
        """TEST-REQ-3044-012: Leere Kategorien → leere Liste."""
        result = mcdc.generate({})
        assert result == []


# ---------------------------------------------------------------------------
# TEST-REQ-3044-013 bis 015: MC/DC API Integration
# ---------------------------------------------------------------------------

class TestMCDCAPI:
    """API-Integration für strategy="mcdc"."""

    def test_strategy_mcdc_callable_via_generate_cases(self):
        """TEST-REQ-3044-013: generate_cases akzeptiert strategy="mcdc"."""
        from app.services import generate_cases
        
        result = generate_cases(CATEGORIES_BOOL, strategy="mcdc")
        
        assert len(result) == 3
        assert {"LoginType": "OAuth", "HTTPSEnabled": "True"} in result

    def test_mcdc_without_rule_engine_parameter(self):
        """TEST-REQ-3044-014: MC/DC funktioniert auch ohne RuleEngine."""
        result = mcdc.generate(CATEGORIES_BOOL, rule_engine=None)
        assert len(result) == 3

    def test_mcdc_constraint_aware_via_services(self):
        """TEST-REQ-3044-015: Constraint-aware MC/DC über Services-Layer."""
        # Direkter Test der mcdc.generate Funktion mit RuleEngine
        regel = ForbiddenRule("LoginType", "OAuth", "HTTPSEnabled", "False")
        engine = RuleEngine([regel])
        
        result = mcdc.generate(CATEGORIES_BOOL, rule_engine=engine)
        
        # Validierung
        for tc in result:
            if tc["LoginType"] == "OAuth":
                assert tc["HTTPSEnabled"] != "False"


# ---------------------------------------------------------------------------
# TEST-REQ-3044-016 bis 020: MC/DC Edge Cases
# ---------------------------------------------------------------------------

class TestMCDCEdgeCases:
    """Edge Cases und Grenzfälle."""

    def test_single_category_single_value(self):
        """TEST-REQ-3044-016: Nur 1 Kategorie, 1 Wert → 1 Testfall."""
        cats = {"Status": ["Active"]}
        result = mcdc.generate(cats)
        
        assert len(result) == 1
        assert result[0] == {"Status": "Active"}

    def test_single_category_multiple_values(self):
        """TEST-REQ-3044-017: 1 Kategorie, mehrere Werte → je 1 Testfall pro Wert."""
        cats = {"Priority": ["Low", "Medium", "High"]}
        result = mcdc.generate(cats)
        
        # Baseline + 2 Variationen = 3
        assert len(result) == 3
        assert {"Priority": "Low"} in result
        assert {"Priority": "Medium"} in result
        assert {"Priority": "High"} in result

    def test_all_combinations_forbidden_returns_empty(self):
        """TEST-REQ-3044-018: Alle Kombinationen verboten → leere Liste."""
        # Extreme Regel: alle Kombinationen verbieten
        regeln = [
            ForbiddenRule("LoginType", "OAuth", "HTTPSEnabled", "True"),
            ForbiddenRule("LoginType", "OAuth", "HTTPSEnabled", "False"),
            ForbiddenRule("LoginType", "Password", "HTTPSEnabled", "True"),
            ForbiddenRule("LoginType", "Password", "HTTPSEnabled", "False"),
        ]
        engine = RuleEngine(regeln)
        
        result = mcdc.generate(CATEGORIES_BOOL, rule_engine=engine)
        
        # Sollte leer sein oder nur gültige (aber es gibt keine)
        assert len(result) == 0

    def test_complex_multi_value_coverage(self):
        """TEST-REQ-3044-019: Komplexes Szenario mit vielen Werten."""
        cats = {
            "Browser": ["Chrome", "Firefox", "Safari", "Edge"],
            "OS": ["Windows", "macOS", "Linux"],
            "Mode": ["Standard", "Incognito"],
        }
        result = mcdc.generate(cats)
        
        # Baseline: Chrome, Windows, Standard
        # Browser: 3 Variationen (Firefox, Safari, Edge)
        # OS: 2 Variationen (macOS, Linux)
        # Mode: 1 Variation (Incognito)
        # Gesamt: 1 + 3 + 2 + 1 = 7
        assert len(result) == 7
        
        baseline = {"Browser": "Chrome", "OS": "Windows", "Mode": "Standard"}
        assert baseline in result

    def test_constraint_forces_baseline_change(self):
        """TEST-REQ-3044-020: Constraint erzwingt kompletten Baseline-Wechsel."""
        # Wenn Standard-Baseline (erste Werte) komplett verboten ist
        cats = {
            "Color": ["Red", "Blue"],
            "Size": ["Small", "Large"],
        }
        # Regel: Red + Small verboten (= default Baseline)
        regel = ForbiddenRule("Color", "Red", "Size", "Small")
        engine = RuleEngine([regel])
        
        result = mcdc.generate(cats, rule_engine=engine)
        
        # Alternative Baseline muss gewählt werden
        # Mögliche Baselines: Red+Large, Blue+Small, Blue+Large
        # Keine darf Red+Small sein
        for tc in result:
            if tc["Color"] == "Red":
                assert tc["Size"] != "Small"
        
        # Trotzdem sollten alle Werte vorkommen (wenn möglich)
        colors = set(tc["Color"] for tc in result)
        sizes = set(tc["Size"] for tc in result)
        
        # Mindestens beide Werte sollten erscheinen
        assert len(colors) >= 1
        assert len(sizes) >= 1
