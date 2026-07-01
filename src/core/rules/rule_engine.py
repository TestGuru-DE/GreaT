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
    """

    def __init__(self, rules: list) -> None:
        self._combine_rules: List[CombineRule] = [r for r in rules if isinstance(r, CombineRule)]
        self._forbidden_rules: List[ForbiddenRule] = [r for r in rules if isinstance(r, ForbiddenRule)]
        self._dependency_rules: List[DependencyRule] = [r for r in rules if isinstance(r, DependencyRule)]

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
