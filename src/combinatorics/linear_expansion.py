"""
Lineare Expansion ? REQ-0803
ISTQB: Ein Basisfall (alle ersten Werte) + je ein Testfall pro abweichendem Wert.
Genau ein Wert weicht vom Standard ab, alle anderen Werte sind Standardwerte.

REQ-3040: Constraint-aware Generierung optional via rule_engine.
"""
import itertools
from typing import Dict, List, Optional


def _deduplicate(testcases: list[dict]) -> list[dict]:
    """Entfernt Duplikate aus Testfall-Liste (BUG-4 Fix)."""
    seen = set()
    result = []
    for tc in testcases:
        key = tuple(sorted(tc.items()))
        if key not in seen:
            seen.add(key)
            result.append(tc)
    return result


def _finalize_if_valid(rule_engine, candidate: Dict[str, str]):
    """Wendet Dependencies an und verwirft danach ung?ltige Kombinationen."""
    finalized = rule_engine.apply_dependency_rules(candidate)
    if not rule_engine.is_combination_valid(finalized):
        return None
    return finalized


def _find_valid_testcase_for_value(
    categories: Dict[str, List[str]],
    keys: List[str],
    rule_engine,
    target_key: str,
    target_value: str,
):
    """Findet deterministisch den ersten final g?ltigen Testfall f?r einen Zielwert."""
    for combo in itertools.product(*[categories[k] for k in keys]):
        raw_candidate = {k: v for k, v in zip(keys, combo)}
        candidate = _finalize_if_valid(rule_engine, raw_candidate)
        if candidate is None:
            continue
        if candidate.get(target_key) == target_value:
            return candidate
    return None


def generate(categories: Dict[str, List[str]], rule_engine=None) -> List[Dict[str, str]]:
    """
    Erzeugt Testf?lle nach dem Prinzip der linearen Expansion.

    Algorithmus:
    1. Basisfall: erster Wert jeder Kategorie
    2. F?r jede Kategorie, f?r jeden nicht-ersten Wert:
       Basisfall kopieren, diesen einen Wert ersetzen ? neuer Testfall

    Anzahl Testf?lle: 1 + Summe(len(Werte_i) - 1 f?r alle Kategorien i)
    
    REQ-3040: Mit rule_engine werden ung?ltige Testf?lle ?bersprungen und
    Dependencies angewendet.
    
    Args:
        categories: Dict[str, List[str]] ? Kategorien mit Werten
        rule_engine: Optional[RuleEngine] ? Regeln zur Constraint-Pr?fung
    
    Returns:
        Liste von Testf?llen (Dict[str, str])
    """
    if not categories:
        return []

    keys = list(categories.keys())
    basis: Dict[str, str] = {k: categories[k][0] for k in keys}
    
    # REQ-3040: Basisfall auf G?ltigkeit pr?fen
    if rule_engine is not None:
        basis = _finalize_if_valid(rule_engine, basis)
        if basis is None:
            # Versuche einen g?ltigen Basisfall zu finden
            basis = _find_valid_base(categories, keys, rule_engine)
            if basis is None:
                # Kein g?ltiger Basisfall m?glich
                return []
    
    result: List[Dict[str, str]] = [dict(basis)]

    for key in keys:
        werte = categories[key]
        for wert in werte[1:]:  # alle au?er dem ersten (Standard-)Wert
            tc = dict(basis)
            tc[key] = wert
            
            # REQ-3040: Constraint-Check
            if rule_engine is not None:
                tc = _finalize_if_valid(rule_engine, tc)
                if tc is None:
                    # ?berspringe ung?ltige Kombination
                    continue
            
            result.append(tc)

    if rule_engine is not None:
        covered_values = {k: {tc[k] for tc in result if k in tc} for k in keys}
        for key in keys:
            for value in categories[key]:
                if value in covered_values[key]:
                    continue
                candidate = _find_valid_testcase_for_value(categories, keys, rule_engine, key, value)
                if candidate is None:
                    continue
                result.append(candidate)
                for covered_key in keys:
                    covered_values[covered_key].add(candidate[covered_key])

    return _deduplicate(result)


def _find_valid_base(categories: Dict[str, List[str]], keys: List[str], rule_engine) -> Optional[Dict[str, str]]:
    """
    REQ-3040: Sucht einen g?ltigen Basisfall wenn der Standard-Basisfall (alle ersten Werte) ung?ltig ist.
    
    Versucht systematisch Alternativen durch Variation jeweils eines Wertes.
    """
    basis = {k: categories[k][0] for k in keys}
    
    # Versuche jeden Wert jeder Kategorie als Alternative
    for key in keys:
        for val in categories[key][1:]:
            candidate = dict(basis)
            candidate[key] = val
            candidate = _finalize_if_valid(rule_engine, candidate)
            if candidate is not None:
                return candidate
    
    # Kein g?ltiger Basisfall gefunden
    return None
