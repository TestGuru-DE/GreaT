"""
REQ-6009: Ergebnisbericht fuer Seed-Generierung und Lueckenschluss.

Enthaelt: seeds_count, supplemented_count, coverage_before, coverage_after,
impossible_tuples, total_testcases, strategy, filled_fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from combinatorics.coverage import calculate_coverage


@dataclass
class SeedReport:
    """REQ-6009: Ergebnisbericht fuer Seed-Generierung."""
    seeds_count: int = 0
    supplemented_count: int = 0
    total_testcases: int = 0
    coverage_before: float = 0.0
    coverage_after: float = 0.0
    impossible_tuples: List[tuple] = field(default_factory=list)
    strategy: str = "pairwise"
    t_strength: int = 2
    filled_fields: List[Dict[str, List[str]]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialisiert den Bericht als JSON-faehiges Dict."""
        return {
            "seeds_count": self.seeds_count,
            "supplemented_count": self.supplemented_count,
            "total_testcases": self.total_testcases,
            "coverage_before": self.coverage_before,
            "coverage_after": self.coverage_after,
            "impossible_tuples": [list(t) for t in self.impossible_tuples],
            "strategy": self.strategy,
            "t_strength": self.t_strength,
            "filled_fields": self.filled_fields,
            "warnings": self.warnings,
        }


def create_seed_report(
    testcases: List[Dict[str, str]],
    categories: Dict[str, List[str]],
    strategy: str = "pairwise",
    t_strength: int = 2,
    rule_engine=None,
    result_category_names: Optional[List[str]] = None,
    filled_fields: Optional[List[Dict[str, List[str]]]] = None,
    warnings: Optional[List[str]] = None,
) -> SeedReport:
    """
    Erstellt einen Ergebnisbericht fuer eine Seed-Generierung.

    Args:
        testcases: Alle Testfaelle mit origin-Feld ("seed" | "supplemented" | "generated")
        categories: {category_name: [value1, value2, ...]}
        strategy: Verwendete Strategie
        t_strength: Strength fuer Coverage-Berechnung
        rule_engine: Optional RuleEngine-Instanz
        result_category_names: Liste von Ergebnis-Kategorienamen
        filled_fields: Pro Seed, welche Felder aufgefuellt wurden
        warnings: Liste von Warnungen

    Returns:
        SeedReport mit allen Metriken
    """
    active_cats = {
        name: vals
        for name, vals in categories.items()
        if name not in (result_category_names or [])
    }

    if not active_cats:
        return SeedReport(
            seeds_count=sum(1 for tc in testcases if tc.get("origin") == "seed"),
            supplemented_count=sum(1 for tc in testcases if tc.get("origin") == "supplemented"),
            total_testcases=len(testcases),
            strategy=strategy,
            t_strength=t_strength,
            filled_fields=filled_fields or [],
            warnings=warnings or [],
        )

    # Seeds und supplemented trennen
    seed_tcs = [
        {k: v for k, v in tc.items() if k != "origin"}
        for tc in testcases
        if tc.get("origin") == "seed"
    ]
    all_assignments = [
        {k: v for k, v in tc.items() if k != "origin"}
        for tc in testcases
    ]

    # Coverage vor (nur Seeds)
    coverage_before = calculate_coverage(
        seed_tcs, active_cats, t=t_strength, rule_engine=rule_engine
    )

    # Coverage nach (alle TCs)
    coverage_after = calculate_coverage(
        all_assignments, active_cats, t=t_strength, rule_engine=rule_engine
    )

    return SeedReport(
        seeds_count=len(seed_tcs),
        supplemented_count=sum(
            1 for tc in testcases if tc.get("origin") == "supplemented"
        ),
        total_testcases=len(testcases),
        coverage_before=coverage_before.percentage,
        coverage_after=coverage_after.percentage,
        impossible_tuples=coverage_before.uncovered_tuples,
        strategy=strategy,
        t_strength=t_strength,
        filled_fields=filled_fields or [],
        warnings=warnings or [],
    )


def create_gap_fill_report(
    new_testcases: List[Dict[str, str]],
    old_testcases: List[Dict[str, str]],
    categories: Dict[str, List[str]],
    strategy: str = "pairwise",
    t_strength: int = 2,
    rule_engine=None,
    result_category_names: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> SeedReport:
    """
    Erstellt einen Bericht fuer Lueckenschluss.

    Args:
        new_testcases: Neue Generation (alt + ergaenzt) mit origin-Feld
        old_testcases: Original-Testfaelle (ohne origin-Feld)
        categories: {category_name: [value1, value2, ...]}
        strategy: Verwendete Strategie
        t_strength: Strength fuer Coverage-Berechnung
        rule_engine: Optional RuleEngine-Instanz
        result_category_names: Liste von Ergebnis-Kategorienamen
        warnings: Liste von Warnungen

    Returns:
        SeedReport mit before/after Coverage
    """
    active_cats = {
        name: vals
        for name, vals in categories.items()
        if name not in (result_category_names or [])
    }

    if not active_cats:
        return SeedReport(
            seeds_count=len(old_testcases),
            supplemented_count=len(new_testcases) - len(old_testcases),
            total_testcases=len(new_testcases),
            strategy=strategy,
            t_strength=t_strength,
            warnings=warnings or [],
        )

    # Coverage vor (nur alte TCs)
    coverage_before = calculate_coverage(
        old_testcases, active_cats, t=t_strength, rule_engine=rule_engine
    )

    # Coverage nach (alle neuen TCs, ohne origin-Feld)
    new_assignments = [
        {k: v for k, v in tc.items() if k != "origin"}
        for tc in new_testcases
    ]
    coverage_after = calculate_coverage(
        new_assignments, active_cats, t=t_strength, rule_engine=rule_engine
    )

    supplemented_count = sum(
        1 for tc in new_testcases if tc.get("origin") == "supplemented"
    )

    return SeedReport(
        seeds_count=len(old_testcases),
        supplemented_count=supplemented_count,
        total_testcases=len(new_testcases),
        coverage_before=coverage_before.percentage,
        coverage_after=coverage_after.percentage,
        impossible_tuples=coverage_before.uncovered_tuples,
        strategy=strategy,
        t_strength=t_strength,
        warnings=warnings or [],
    )