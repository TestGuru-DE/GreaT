"""
Lineare Expansion – REQ-0803
ISTQB: Ein Basisfall (alle ersten Werte) + je ein Testfall pro abweichendem Wert.
Genau ein Wert weicht vom Standard ab, alle anderen Werte sind Standardwerte.

REQ-3040: Constraint-aware Generierung optional via rule_engine.
"""
from typing import Dict, List, Optional


def generate(categories: Dict[str, List[str]], rule_engine=None) -> List[Dict[str, str]]:
    """
    Erzeugt Testfälle nach dem Prinzip der linearen Expansion.

    Algorithmus:
    1. Basisfall: erster Wert jeder Kategorie
    2. Für jede Kategorie, für jeden nicht-ersten Wert:
       Basisfall kopieren, diesen einen Wert ersetzen → neuer Testfall

    Anzahl Testfälle: 1 + Summe(len(Werte_i) - 1 für alle Kategorien i)
    
    REQ-3040: Mit rule_engine werden ungültige Testfälle übersprungen und
    Dependencies angewendet.
    
    Args:
        categories: Dict[str, List[str]] – Kategorien mit Werten
        rule_engine: Optional[RuleEngine] – Regeln zur Constraint-Prüfung
    
    Returns:
        Liste von Testfällen (Dict[str, str])
    """
    if not categories:
        return []

    keys = list(categories.keys())
    basis: Dict[str, str] = {k: categories[k][0] for k in keys}
    
    # REQ-3040: Basisfall auf Gültigkeit prüfen
    if rule_engine is not None:
        if not rule_engine.is_combination_valid(basis):
            # Versuche einen gültigen Basisfall zu finden
            basis = _find_valid_base(categories, keys, rule_engine)
            if basis is None:
                # Kein gültiger Basisfall möglich
                return []
        basis = rule_engine.apply_dependency_rules(basis)
    
    result: List[Dict[str, str]] = [dict(basis)]

    for key in keys:
        werte = categories[key]
        for wert in werte[1:]:  # alle außer dem ersten (Standard-)Wert
            tc = dict(basis)
            tc[key] = wert
            
            # REQ-3040: Constraint-Check
            if rule_engine is not None:
                if not rule_engine.is_combination_valid(tc):
                    # Überspringe ungültige Kombination
                    continue
                tc = rule_engine.apply_dependency_rules(tc)
            
            result.append(tc)

    return result


def _find_valid_base(categories: Dict[str, List[str]], keys: List[str], rule_engine) -> Optional[Dict[str, str]]:
    """
    REQ-3040: Sucht einen gültigen Basisfall wenn der Standard-Basisfall (alle ersten Werte) ungültig ist.
    
    Versucht systematisch Alternativen durch Variation jeweils eines Wertes.
    """
    basis = {k: categories[k][0] for k in keys}
    
    # Versuche jeden Wert jeder Kategorie als Alternative
    for key in keys:
        for val in categories[key][1:]:
            candidate = dict(basis)
            candidate[key] = val
            if rule_engine.is_combination_valid(candidate):
                return candidate
    
    # Kein gültiger Basisfall gefunden
    return None
