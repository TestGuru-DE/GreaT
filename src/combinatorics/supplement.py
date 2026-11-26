"""Gezielte Ergaenzung fehlender Abdeckung (REQ-6009, BUG K-10).

Statt eine komplette Normalgenerierung zu erzeugen und nur Duplikate der Seeds
wegzulassen, werden ausschliesslich Testfaelle fuer noch nicht abgedeckte, aber
erreichbare t-Tupel gebildet (Greedy-Verfahren nach dem AETG-Prinzip):

1. Starte mit einem nicht abgedeckten Tupel.
2. Belege jede weitere Kategorie mit dem Wert, der die meisten weiteren Luecken
   schliesst und einen gueltigen Testfall zulaesst (Machbarkeitspruefung).
3. Wiederhole, bis alle erreichbaren Tupel abgedeckt sind.
"""
from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Optional

from .budget import checkpoint
from .coverage import calculate_coverage

# Strategie -> Abdeckungsstaerke der Ergaenzung (BUG K-11: t_wise nutzt t_strength)
SUPPLEMENT_STRATEGIES = ("each", "linear", "risk_based", "pairwise", "mcdc", "t_wise", "all")


def strength_for(strategy: str, t_strength: int, n_categories: int) -> int:
    """Abdeckungsstaerke fuer eine Ergaenzungsstrategie; ValueError bei unbekannter Strategie.

    Strategien mit Ziel "jeder Wert einmal" ergaenzen 1-wise, Paar-Strategien 2-wise.
    """
    if strategy in ("each", "linear", "risk_based"):
        return 1
    if strategy in ("pairwise", "orthogonal", "mcdc"):
        return 2
    if strategy == "t_wise":
        return max(1, int(t_strength))
    if strategy == "all":
        return max(1, n_categories)
    raise ValueError(
        f"Unbekannte Strategie fuer die Ergaenzung: {strategy!r}. "
        f"Erlaubt: {', '.join(SUPPLEMENT_STRATEGIES)}"
    )


def supplement_coverage(
    existing: List[Dict[str, str]],
    categories: Dict[str, List[str]],
    t: int,
    rule_engine=None,
) -> List[Dict[str, str]]:
    """Neue Testfaelle, die alle erreichbaren, noch fehlenden t-Tupel abdecken."""
    if not categories:
        return []
    checker = None
    if rule_engine is not None:
        from .feasibility import FeasibilityChecker
        checker = FeasibilityChecker(categories, rule_engine)
    t = min(t, len(categories))
    coverage = calculate_coverage(existing, categories, t, rule_engine, feasibility=checker)
    uncovered = set(coverage.uncovered_tuples)
    cat_names = sorted(categories)
    new_cases: List[Dict[str, str]] = []

    def tuples_of(tc: Dict[str, str]):
        items = [(c, tc[c]) for c in cat_names if c in tc]
        return (frozenset(combo) for combo in combinations(items, t))

    while uncovered:
        checkpoint()
        start = min(uncovered, key=sorted)  # deterministisch
        partial = dict(start)
        for cat in cat_names:
            if cat in partial:
                continue
            best_val, best_gain = None, -1
            others = [(c, partial[c]) for c in cat_names if c in partial]
            for val in categories[cat]:
                candidate = {**partial, cat: val}
                if checker is not None and not checker.is_feasible(candidate):
                    continue
                gain = sum(1 for combo in combinations(others, t - 1)
                           if frozenset(combo + ((cat, val),)) in uncovered) if t > 1 else \
                    int(frozenset([(cat, val)]) in uncovered)
                if gain > best_gain:
                    best_val, best_gain = val, gain
            if best_val is None:  # nur bei erschoepftem Suchbudget denkbar
                break
            partial[cat] = best_val
        if len(partial) < len(cat_names):
            uncovered.discard(start)
            continue
        newly = {tup for tup in tuples_of(partial) if tup in uncovered}
        if not newly:
            uncovered.discard(start)
            continue
        uncovered -= newly
        new_cases.append(partial)
    return new_cases
