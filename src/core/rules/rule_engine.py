"""
Rule Engine – G.R.E.A.T.
REQ-0700 (Verboten), REQ-0701 (Abhängig), REQ-0702 (Kombinierbar)

Reihenfolge der Regelanwendung: Combine → Forbidden → Dependency
(Combine filtert zuerst, dann Forbidden, dann Dependency überschreibt Werte)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


Testfall = Dict[str, str]


# ---------------------------------------------------------------------------
# Regeltypen
# ---------------------------------------------------------------------------

@dataclass
class ForbiddenRule:
    """
    REQ-0700: Zwei Äquivalenzklassen können nicht zusammen in einem Testfall erscheinen.
    Wenn if_category == if_value UND then_category == then_value → Testfall entfernen.
    """
    if_category: str
    if_value: str
    then_category: str
    then_value: str

    def matches(self, tc: Testfall) -> bool:
        return (tc.get(self.if_category) == self.if_value and
                tc.get(self.then_category) == self.then_value)


@dataclass
class DependencyRule:
    """
    REQ-0701: Wenn if_category == if_value, muss then_category = then_value sein.
    Setzt den Wert – filtert nicht.
    """
    if_category: str
    if_value: str
    then_category: str
    then_value: str

    def apply(self, tc: Testfall) -> Testfall:
        if tc.get(self.if_category) == self.if_value:
            tc = dict(tc)
            tc[self.then_category] = self.then_value
        return tc


@dataclass
class CombineRule:
    """
    REQ-0702: Wenn if_category == if_value, darf then_category nur Werte
    aus allowed_values enthalten. Testfälle mit anderen Werten werden entfernt.
    """
    if_category: str
    if_value: str
    then_category: str
    allowed_values: List[str] = field(default_factory=list)

    def should_remove(self, tc: Testfall) -> bool:
        if tc.get(self.if_category) != self.if_value:
            return False
        return tc.get(self.then_category) not in self.allowed_values


# ---------------------------------------------------------------------------
# Rule Engine
# ---------------------------------------------------------------------------

class RuleEngine:
    """
    Wendet alle registrierten Regeln auf eine Liste von Testfällen an.
    Reihenfolge: CombineRule → ForbiddenRule → DependencyRule
    
    REQ-3040: Constraint-aware Generierung – is_combination_valid() prüft
    partielle Testfälle während der Generierung.
    """

    def __init__(self, rules: list) -> None:
        self._combine_rules: List[CombineRule] = [r for r in rules if isinstance(r, CombineRule)]
        self._forbidden_rules: List[ForbiddenRule] = [r for r in rules if isinstance(r, ForbiddenRule)]
        self._dependency_rules: List[DependencyRule] = [r for r in rules if isinstance(r, DependencyRule)]

    def is_combination_valid(self, partial_testcase: Testfall) -> bool:
        """
        REQ-3040: Prüft ob eine (partielle) Wertekombination gegen Regeln verstößt.
        
        Wird von Kombinatorik-Strategien während der Generierung aufgerufen.
        Reihenfolge: CombineRule → ForbiddenRule (DependencyRule wird später angewendet).
        
        Args:
            partial_testcase: Kann vollständig oder partiell sein (nur einige Kategorien gesetzt)
        
        Returns:
            False wenn Kombination gegen Regeln verstößt, True sonst
        """
        # 1. CombineRules: Prüfen ob Wert außerhalb erlaubter Liste
        for regel in self._combine_rules:
            if partial_testcase.get(regel.if_category) == regel.if_value:
                then_value = partial_testcase.get(regel.then_category)
                # Wenn then_category noch nicht gesetzt ist, können wir nicht prüfen
                if then_value is not None and then_value not in regel.allowed_values:
                    return False
        
        # 2. ForbiddenRules: Prüfen ob verbotene Kombination vorliegt
        for regel in self._forbidden_rules:
            # Nur prüfen wenn beide Kategorien bereits gesetzt sind
            if_val = partial_testcase.get(regel.if_category)
            then_val = partial_testcase.get(regel.then_category)
            if if_val is not None and then_val is not None:
                if if_val == regel.if_value and then_val == regel.then_value:
                    return False
        
        # 3. DependencyRules ignorieren wir hier – die werden später beim finalisieren angewendet
        # (Dependencies setzen Werte, verbieten sie nicht)
        
        return True

    def apply_dependency_rules(self, testfall: Testfall) -> Testfall:
        """
        REQ-3040: Wendet nur Dependency-Regeln auf einen Testfall an.
        Wird von Strategien nach der Generierung eines Testfalls aufgerufen.
        
        Args:
            testfall: Vollständiger Testfall
        
        Returns:
            Testfall mit angewendeten Dependencies
        """
        result = dict(testfall)
        for regel in self._dependency_rules:
            if result.get(regel.if_category) == regel.if_value:
                result[regel.then_category] = regel.then_value
        return result

    def apply(self, testfaelle: List[Testfall]) -> List[Testfall]:
        result = list(testfaelle)

        # 1. CombineRules: Testfälle mit nicht-erlaubten Kombinationen entfernen
        for regel in self._combine_rules:
            result = [tc for tc in result if not regel.should_remove(tc)]

        # 2. ForbiddenRules: Verbotene Kombinationen entfernen
        for regel in self._forbidden_rules:
            result = [tc for tc in result if not regel.matches(tc)]

        # 3. DependencyRules: Werte setzen
        for regel in self._dependency_rules:
            result = [regel.apply(tc) for tc in result]

        return result
