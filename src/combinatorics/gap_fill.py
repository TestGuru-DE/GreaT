"""
REQ-6009: Lueckenschluss fuer bestehende Generierungen.

Erzeugt eine NEUE Generierung = alte Testfaelle + Ergaenzung.
Die alte Generation bleibt unveraendert (Immutable History).
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from combinatorics.coverage import calculate_coverage

logger = logging.getLogger("great.combinatorics.gap_fill")


def gap_fill(
    existing_testcases: List[Dict[str, str]],
    categories: Dict[str, List[str]],
    strategy: str = "pairwise",
    t_strength: int = 2,
    rule_engine=None,
    deadline: Optional[float] = None,
    result_category_names: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Schliesst Luecken einer bestehenden Generierung.

    Args:
        existing_testcases: Bestehende Testfaelle (ohne origin-Feld)
        categories: {category_name: [value1, value2, ...]}
        strategy: Strategie fuer Ergaenzung (default "pairwise")
        t_strength: Strength fuer t_wise (default 2)
        rule_engine: Optional RuleEngine-Instanz
        deadline: Optional Unix-Timestamp fuer Timeout
        result_category_names: Liste von Ergebnis-Kategorienamen

    Returns:
        (new_testcases, warnings)
        - new_testcases: Alle TCs mit origin="seed" (alt) oder "supplemented" (neu)
        - warnings: Liste von Warnungen (z.B. unmögliche Tupel)
    """
    warnings: List[str] = []

    # Aktive Kategorien (ohne Ergebnis-Kategorien)
    active_cats = {
        name: vals
        for name, vals in categories.items()
        if name not in (result_category_names or [])
    }

    if not active_cats:
        return [
            {**tc, "origin": "seed"}
            for tc in existing_testcases
        ], warnings

    # Markiere bestehende TCs als "seed"
    seed_tcs: List[Dict[str, str]] = []
    for tc in existing_testcases:
        new_tc = dict(tc)
        new_tc["origin"] = "seed"
        seed_tcs.append(new_tc)

    # Berechne aktuelle Abdeckung
    seed_assignments = [
        {k: v for k, v in tc.items() if k != "origin"}
        for tc in seed_tcs
    ]

    coverage_before = calculate_coverage(
        seed_assignments,
        active_cats,
        t=t_strength,
        rule_engine=rule_engine,
    )

    # Unmoegliche Tupel melden (auch bei 100% Abdeckung)
    if coverage_before.excluded_by_rules > 0:
        warnings.append(
            f"{coverage_before.excluded_by_rules} Tupel(en) durch Regeln ausgeschlossen "
            f"(konnen nicht abgedeckt werden)."
        )

    # Wenn 100% Abdeckung: nur Seeds zurueckgeben
    if coverage_before.percentage >= 100.0:
        return seed_tcs, warnings

    # Unabgedeckte Tupel ergaenzen
    supplemented = _supplement_gaps(
        seed_assignments,
        active_cats,
        strategy,
        t_strength,
        rule_engine,
        deadline,
    )

    all_tcs = seed_tcs + supplemented
    return all_tcs, warnings


def _supplement_gaps(
    seed_assignments: List[Dict[str, str]],
    active_cats: Dict[str, List[str]],
    strategy: str,
    t_strength: int,
    rule_engine=None,
    deadline: Optional[float] = None,
) -> List[Dict[str, str]]:
    """
    Generiert nur die Testfaelle, die noetig sind, um die fehlende
    Abdeckung zu ergaenzen.
    """
    from combinatorics import all_combinations, each_choice, ipo, linear_expansion, t_wise

    # Normale Generierung durchfuehren
    if strategy == "pairwise":
        normal = ipo.generate(active_cats, rule_engine=rule_engine, deadline=deadline)
    elif strategy == "t_wise":
        normal = t_wise.generate(
            active_cats, t=t_strength, rule_engine=rule_engine
        )
    elif strategy == "each":
        normal = each_choice.generate(active_cats, rule_engine=rule_engine)
    elif strategy == "linear":
        normal = linear_expansion.generate(active_cats, rule_engine=rule_engine)
    elif strategy == "all":
        normal = all_combinations.generate(active_cats)
    else:
        normal = ipo.generate(active_cats, rule_engine=rule_engine, deadline=deadline)

    # Nur TCs nehmen, die neue Abdeckung bringen
    supplemented: List[Dict[str, str]] = []
    for tc in normal:
        tc_clean = {k: v for k, v in tc.items() if k != "origin"}
        if not _tc_covered_by_seeds(tc_clean, seed_assignments):
            tc["origin"] = "supplemented"
            supplemented.append(tc)

    return supplemented


def _tc_covered_by_seeds(
    tc: Dict[str, str],
    seed_assignments: List[Dict[str, str]],
) -> bool:
    """
    Prueft ob ein Testfall bereits durch einen Seed abgedeckt ist.
    """
    for seed in seed_assignments:
        if all(seed.get(k) == v for k, v in tc.items()):
            return True
    return False