"""
REQ-6009: Lueckenschluss fuer bestehende Generierungen.

Erzeugt eine NEUE Generierung = alte Testfaelle + Ergaenzung.
Die alte Generation bleibt unveraendert (Immutable History).
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from combinatorics.coverage import calculate_coverage
from combinatorics.supplement import strength_for, supplement_coverage

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

    # BUG K-11: Staerke aus der Strategie (t_wise nutzt t_strength); unbekannte Strategie -> ValueError
    t = strength_for(strategy, t_strength, len(active_cats))
    coverage_before = calculate_coverage(seed_assignments, active_cats, t=t, rule_engine=rule_engine)

    # Unmoegliche Tupel melden (auch bei 100% Abdeckung)
    if coverage_before.excluded_by_rules > 0:
        warnings.append(
            f"{coverage_before.excluded_by_rules} Tupel durch Regeln ausgeschlossen "
            f"(koennen nicht abgedeckt werden)."
        )

    # BUG K-10: nur fehlende, erreichbare Tupel gezielt ergaenzen (keine Neugenerierung)
    supplemented = supplement_coverage(seed_assignments, active_cats, t, rule_engine)
    for tc in supplemented:
        tc["origin"] = "supplemented"
    return seed_tcs + supplemented, warnings
