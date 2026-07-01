# REQ-0700 – Regeltyp Verboten (Forbidden)
# REQ-0701 – Regeltyp Abhängig (Dependency)
# REQ-0702 – Regeltyp Kombinierbar (Combine)
# TEST-ID: TEST-RULE-001 bis TEST-RULE-003
#
# Die Geschäftsregel-Engine filtert/verändert Testfälle anhand von Regeln.

from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule, CombineRule


# ---------------------------------------------------------------------------
# Hilfsdaten
# ---------------------------------------------------------------------------

TESTFAELLE = [
    {"Versandart": "Normal",    "Gewicht": "Klein",  "Inland": "True"},
    {"Versandart": "Express",   "Gewicht": "Groß",   "Inland": "True"},
    {"Versandart": "Overnight", "Gewicht": "Klein",  "Inland": "False"},
    {"Versandart": "Normal",    "Gewicht": "Groß",   "Inland": "True"},
    {"Versandart": "Overnight", "Gewicht": "Groß",   "Inland": "True"},
]


# ---------------------------------------------------------------------------
# ForbiddenRule – REQ-0700
# ---------------------------------------------------------------------------

class TestForbiddenRule:

    def test_verboten_entfernt_testfall(self):
        """Wenn IF-Wert und THEN-Wert zusammen auftreten, wird der Testfall entfernt."""
        regel = ForbiddenRule(if_category="Versandart", if_value="Overnight",
                              then_category="Inland", then_value="True")
        engine = RuleEngine(rules=[regel])
        result = engine.apply(list(TESTFAELLE))
        for tc in result:
            assert not (tc["Versandart"] == "Overnight" and tc["Inland"] == "True"), \
                f"Verbotene Kombination im Ergebnis: {tc}"

    def test_verboten_behaelt_erlaubte_faelle(self):
        """Testfälle, die die Bedingung nicht erfüllen, bleiben erhalten."""
        regel = ForbiddenRule(if_category="Versandart", if_value="Overnight",
                              then_category="Inland", then_value="True")
        engine = RuleEngine(rules=[regel])
        result = engine.apply(list(TESTFAELLE))
        # Overnight + False bleibt
        assert {"Versandart": "Overnight", "Gewicht": "Klein", "Inland": "False"} in result

    def test_verboten_leer_wenn_alle_verboten(self):
        """Wenn alle Testfälle verboten sind, wird eine leere Liste zurückgegeben."""
        faelle = [{"A": "x", "B": "y"}, {"A": "x", "B": "y"}]
        regel = ForbiddenRule(if_category="A", if_value="x", then_category="B", then_value="y")
        engine = RuleEngine(rules=[regel])
        assert engine.apply(faelle) == []

    def test_verboten_ohne_match_unveraendert(self):
        """Ohne Treffer bleibt die Liste unverändert."""
        regel = ForbiddenRule(if_category="Versandart", if_value="NICHTEXISTENT",
                              then_category="Inland", then_value="True")
        engine = RuleEngine(rules=[regel])
        result = engine.apply(list(TESTFAELLE))
        assert len(result) == len(TESTFAELLE)


# ---------------------------------------------------------------------------
# DependencyRule – REQ-0701
# ---------------------------------------------------------------------------

class TestDependencyRule:

    def test_dependency_setzt_wert(self):
        """Wenn IF zutrifft, wird THEN-Wert gesetzt."""
        regel = DependencyRule(if_category="Versandart", if_value="Overnight",
                               then_category="Inland", then_value="False")
        engine = RuleEngine(rules=[regel])
        result = engine.apply(list(TESTFAELLE))
        for tc in result:
            if tc["Versandart"] == "Overnight":
                assert tc["Inland"] == "False", f"Dependency nicht angewendet: {tc}"

    def test_dependency_belaesst_nicht_betroffene(self):
        """Nicht betroffene Testfälle werden nicht verändert."""
        regel = DependencyRule(if_category="Versandart", if_value="Overnight",
                               then_category="Inland", then_value="False")
        engine = RuleEngine(rules=[regel])
        result = engine.apply(list(TESTFAELLE))
        normal_faelle = [tc for tc in result if tc["Versandart"] == "Normal"]
        assert any(tc["Inland"] == "True" for tc in normal_faelle)


# ---------------------------------------------------------------------------
# CombineRule – REQ-0702
# ---------------------------------------------------------------------------

class TestCombineRule:

    def test_combine_nur_erlaubte_zielwerte(self):
        """Testfälle mit IF-Wert, aber nicht erlaubten THEN-Werten werden entfernt."""
        # Overnight darf nur mit Klein kombiniert werden
        regel = CombineRule(if_category="Versandart", if_value="Overnight",
                            then_category="Gewicht", allowed_values=["Klein"])
        engine = RuleEngine(rules=[regel])
        result = engine.apply(list(TESTFAELLE))
        for tc in result:
            if tc["Versandart"] == "Overnight":
                assert tc["Gewicht"] == "Klein", f"Nicht-erlaubter Wert im Ergebnis: {tc}"

    def test_combine_mehrere_erlaubte_werte(self):
        """Mehrere erlaubte Werte: alle bleiben, nicht erlaubte werden entfernt."""
        faelle = [
            {"A": "x", "B": "b1"},
            {"A": "x", "B": "b2"},
            {"A": "x", "B": "b3"},
            {"A": "y", "B": "b1"},
        ]
        regel = CombineRule(if_category="A", if_value="x",
                            then_category="B", allowed_values=["b1", "b2"])
        engine = RuleEngine(rules=[regel])
        result = engine.apply(faelle)
        assert {"A": "x", "B": "b1"} in result
        assert {"A": "x", "B": "b2"} in result
        assert {"A": "x", "B": "b3"} not in result
        assert {"A": "y", "B": "b1"} in result  # unberührt

    def test_combine_ohne_match_unveraendert(self):
        """Ohne Treffer bleibt die Liste unverändert."""
        regel = CombineRule(if_category="A", if_value="NICHTEXISTENT",
                            then_category="B", allowed_values=["b1"])
        faelle = [{"A": "x", "B": "b2"}]
        engine = RuleEngine(rules=[regel])
        assert engine.apply(faelle) == faelle


# ---------------------------------------------------------------------------
# RuleEngine – Mehrere Regeln kombiniert
# ---------------------------------------------------------------------------

class TestRuleEngine:

    def test_mehrere_regeln_werden_sequenziell_angewendet(self):
        """Mehrere Regeln werden in der Reihenfolge combine → forbidden → dependency angewendet."""
        faelle = [
            {"A": "x", "B": "b1", "C": "c1"},
            {"A": "x", "B": "b2", "C": "c1"},
            {"A": "y", "B": "b1", "C": "c2"},
        ]
        r1 = ForbiddenRule(if_category="A", if_value="x", then_category="B", then_value="b2")
        r2 = DependencyRule(if_category="A", if_value="y", then_category="C", then_value="c1")
        engine = RuleEngine(rules=[r1, r2])
        result = engine.apply(faelle)
        # r1 entfernt A=x, B=b2
        assert {"A": "x", "B": "b2", "C": "c1"} not in result
        # r2 setzt C=c1 für A=y
        y_faelle = [tc for tc in result if tc["A"] == "y"]
        assert all(tc["C"] == "c1" for tc in y_faelle)

    def test_leere_regelliste_unveraendert(self):
        """Ohne Regeln wird die Eingabe unverändert zurückgegeben."""
        engine = RuleEngine(rules=[])
        assert engine.apply(list(TESTFAELLE)) == TESTFAELLE
