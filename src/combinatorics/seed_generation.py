"""
REQ-6009: Seed-basierte Generierung.

Seeds als Startpunkt, nur fehlende Abdeckung ergaenzen.
Unvollstaendige Seeds (None = beliebig) werden passend aufgefuellt.
Seeds gegen Regeln: Warnung + Nutzerentscheidung (nicht stillschweigend entfernen).
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, Tuple

from combinatorics.coverage import calculate_coverage
from combinatorics.supplement import strength_for, supplement_coverage

logger = logging.getLogger("great.combinatorics.seed")


# ---------------------------------------------------------------------------
# Seed validation helpers
# ---------------------------------------------------------------------------

def validate_seeds(
    seeds: List[Dict[str, Optional[str]]],
    categories: Dict[str, List[str]],
    rule_engine=None,
) -> Tuple[List[Dict[str, Optional[str]]], List[str]]:
    """
    Validiert Seeds gegen Kategorien und Regeln.

    Args:
        seeds: Liste von {category_name: value_name | None}
        categories: {category_name: [value1, value2, ...]}
        rule_engine: Optional RuleEngine-Instanz

    Returns:
        (valid_seeds, warnings)
        - valid_seeds: Seeds mit leeren Strings zu None konvertiert,
          fehlende Kategorien als None ergaenzt
        - warnings: Liste von Warnungen (unbekannte Werte, Regelverstoesse, etc.)
    """
    warnings: List[str] = []
    normalized: List[Dict[str, Optional[str]]] = []

    # Duplikat-Prüfung
    seen: set = set()
    duplicate_count = 0

    for i, seed in enumerate(seeds):
        row_num = i + 1
        normalized_seed: Dict[str, Optional[str]] = {}

        # Leere Kategorien als None ergaenzen
        for cat_name in categories:
            val = seed.get(cat_name)
            # Leerer String -> None (beliebig)
            if val == "":
                val = None
            normalized_seed[cat_name] = val

        # Unbekannte Kategorien melden
        unknown_cats = [k for k in seed if k not in categories]
        for uc in unknown_cats:
            warnings.append(
                f"Seed {row_num}: Unbekannte Kategorie '{uc}' ignoriert."
            )

        # Unbekannte Werte melden (aber nicht entfernen)
        for cat_name, val in normalized_seed.items():
            if val is not None and val not in categories[cat_name]:
                warnings.append(
                    f"Seed {row_num}: Wert '{val}' nicht in Kategorie '{cat_name}'."
                )

        # Duplikat-Prüfung
        seed_key = tuple(
            sorted((k, v) for k, v in normalized_seed.items())
        )
        if seed_key in seen:
            duplicate_count += 1
            continue
        seen.add(seed_key)

        normalized.append(normalized_seed)

    if duplicate_count > 0:
        warnings.append(
            f"{duplicate_count} duplizierte Seed(s) entfernt."
        )

    # Regel-Prüfung (nur Warnung, nicht entfernen)
    if rule_engine is not None:
        for i, seed in enumerate(normalized):
            # Nur gueltige Werte pruefen (None = beliebig, noch nicht aufgefuellt)
            partial_tc = {k: v for k, v in seed.items() if v is not None}
            if not rule_engine.is_combination_valid(partial_tc):
                warnings.append(
                    f"Seed {i + 1}: Verstoßt gegen Regel/Constraint "
                    f"({', '.join(f'{k}={v}' for k, v in partial_tc.items())}). "
                    "Nutzer muss entscheiden: trotzdem behalten oder ausschließen."
                )

    return normalized, warnings


# ---------------------------------------------------------------------------
# Fill partial seeds
# ---------------------------------------------------------------------------

def fill_partial_seeds(
    seeds: List[Dict[str, Optional[str]]],
    categories: Dict[str, List[str]],
    rule_engine=None,
) -> Tuple[List[Dict[str, str]], List[Dict[str, List[str]]]]:
    """
    Fuegt unvollstaendige Seeds auf (None -> konkreter Wert).

    Strategie: Fuer jeden None-Wert, waelle den Wert, der die maximale
    Paarabdeckung bringt. Bei Regeln: waelle einen Wert, der keine
    Regel verletzt.

    Args:
        seeds: Normalisierte Seeds (alle Kategorien vorhanden, None = beliebig)
        categories: {category_name: [value1, value2, ...]}
        rule_engine: Optional RuleEngine-Instanz

    Returns:
        (filled_seeds, filled_fields_list)
        - filled_seeds: Alle None durch konkrete Werte ersetzt
        - filled_fields_list: Pro Seed Liste der Kategorien, die aufgefuellt wurden
    """
    filled_seeds: List[Dict[str, str]] = []
    filled_fields_list: List[Dict[str, List[str]]] = []

    for seed in seeds:
        filled_fields: List[str] = []
        filled_seed: Dict[str, str] = {}

        for cat_name in categories:
            val = seed[cat_name]
            if val is not None:
                filled_seed[cat_name] = val
            else:
                filled_fields.append(cat_name)
                # Waelle Wert, der keine Regel verletzt und maximale Abdeckung bringt
                filled_seed[cat_name] = _choose_fill_value(
                    cat_name, filled_seed, categories, rule_engine
                )

        # Dependency-Regeln anwenden
        if rule_engine is not None:
            filled_seed = rule_engine.apply_dependency_rules(filled_seed)

        filled_seeds.append(filled_seed)
        filled_fields_list.append({cat_name: filled_fields for cat_name in ["filled_fields"]})

    return filled_seeds, filled_fields_list


def _choose_fill_value(
    cat_name: str,
    partial_seed: Dict[str, str],
    categories: Dict[str, List[str]],
    rule_engine=None,
) -> str:
    """
    Waelle einen Wert fuer eine None-Zelle, der:
    1. Keine Regel verletzt
    2. Maximale Paarabdeckung bringt (mit bereits gesetzten Werten)
    """
    candidates = list(categories[cat_name])

    # Test each candidate against rules
    valid_candidates = []
    for val in candidates:
        test_tc = dict(partial_seed)
        test_tc[cat_name] = val
        if rule_engine is None or rule_engine.is_combination_valid(test_tc):
            valid_candidates.append(val)

    if not valid_candidates:
        # Fallback: erster Wert (wird im Report als Warnung markiert)
        logger.warning(
            "Kein gueltiger Wert fuer Kategorie '%s' gefunden. "
            "Erster Wert wird verwendet.",
            cat_name,
        )
        return candidates[0]

    # Among valid candidates, pick the one that covers the most uncovered pairs
    # with already-set categories
    best_val = valid_candidates[0]
    best_score = 0

    for val in valid_candidates:
        score = 0
        test_tc = dict(partial_seed)
        test_tc[cat_name] = val
        for other_cat, other_val in test_tc.items():
            if other_cat != cat_name and other_val is not None:
                score += 1
        if score > best_score:
            best_score = score
            best_val = val

    return best_val


# ---------------------------------------------------------------------------
# Main seed generation
# ---------------------------------------------------------------------------

def seed_generation(
    seeds: List[Dict[str, str]],
    categories: Dict[str, List[str]],
    strategy: str,
    t_strength: int = 2,
    rule_engine=None,
    deadline: Optional[float] = None,
    result_category_names: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, str]], List[Dict[str, List[str]]]]:
    """
    Generiert Testfaelle aus Seeds + Ergaenzung fuer fehlende Abdeckung.

    Args:
        seeds: Vollstaendige Seeds (alle None bereits aufgefuellt)
        categories: {category_name: [value1, value2, ...]}
        strategy: "pairwise" | "t_wise" | "each" | "linear" | "all"
        t_strength: Strength fuer t_wise (default 2)
        rule_engine: Optional RuleEngine-Instanz
        deadline: Optional Unix-Timestamp fuer Timeout
        result_category_names: Liste von Ergebnis-Kategorienamen

    Returns:
        (testcases, filled_fields_list)
        - testcases: Liste von {category: value, origin: "seed"|"supplemented"}
        - filled_fields_list: Pro Seed, welche Felder aufgefuellt wurden
    """
    # Wenn keine Seeds: normale Generierung
    if not seeds:
        return _generate_normal(
            categories, strategy, t_strength, rule_engine, deadline
        ), []

    # Mark Seeds mit origin="seed"
    seed_tcs: List[Dict[str, str]] = []
    for seed in seeds:
        tc = dict(seed)
        tc["origin"] = "seed"
        seed_tcs.append(tc)

    # Berechne aktuelle Abdeckung der Seeds
    active_cats = {
        name: vals
        for name, vals in categories.items()
        if name not in (result_category_names or [])
    }

    if not active_cats:
        return seed_tcs, []

    # Seeds ohne origin-Feld fuer Coverage-Berechnung
    seed_assignments = [
        {k: v for k, v in tc.items() if k != "origin"}
        for tc in seed_tcs
    ]

    # BUG K-10/K-11: nur fehlende, erreichbare Tupel der gewaehlten Staerke ergaenzen
    t = strength_for(strategy, t_strength, len(active_cats))
    supplemented = supplement_coverage(seed_assignments, active_cats, t, rule_engine)
    for tc in supplemented:
        tc["origin"] = "supplemented"
    return seed_tcs + supplemented, []


def _generate_normal(
    categories: Dict[str, List[str]],
    strategy: str,
    t_strength: int,
    rule_engine=None,
    deadline: Optional[float] = None,
) -> List[Dict[str, str]]:
    """Normale Generierung ohne Seeds."""
    from combinatorics import all_combinations, each_choice, ipo, linear_expansion, t_wise

    result: List[Dict[str, str]] = []

    if strategy == "pairwise":
        result = ipo.generate(categories, rule_engine=rule_engine, deadline=deadline)
    elif strategy == "t_wise":
        result = t_wise.generate(
            categories, t=t_strength, rule_engine=rule_engine
        )
    elif strategy == "each":
        result = each_choice.generate(categories, rule_engine=rule_engine)
    elif strategy == "linear":
        result = linear_expansion.generate(categories, rule_engine=rule_engine)
    elif strategy == "all":
        result = all_combinations.generate(categories)
    else:
        result = ipo.generate(categories, rule_engine=rule_engine, deadline=deadline)

    # Markieren als "generated" (nicht seed/supplemented)
    for tc in result:
        tc["origin"] = "generated"

    return result
