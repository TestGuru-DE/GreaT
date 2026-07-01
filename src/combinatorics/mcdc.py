"""
MC/DC (Modified Condition/Decision Coverage) Kombinatorik
REQ-3044

MC/DC ist ein Testabdeckungskriterium aus DO-178C (Avionik) und ISO 26262 (Automotive).
Es stellt sicher, dass jede Bedingung (Kategorie/Wert) unabhängig das Ergebnis beeinflussen kann.

Algorithmus:
1. Baseline-Testfall: erster Wert jeder Kategorie
2. Für jede Kategorie K:
   - Für jeden Wert v ∈ K (außer dem Baseline-Wert):
     - Erzeuge Variante: Baseline mit K=v (alle anderen wie Baseline)
3. Duplikate entfernen
4. Constraint-aware: ungültige Kombinationen durch RuleEngine vermeiden

Für n Kategorien mit je 2 Werten: exakt n+1 Testfälle.
Für Kategorien mit >2 Werten: entsprechend mehr Variationen.

Referenzen:
- DO-178C: Software Considerations in Airborne Systems and Equipment Certification
- ISO 26262: Road vehicles — Functional safety
"""

from typing import Dict, List, Optional


def generate(categories: Dict[str, List[str]], rule_engine=None) -> List[Dict[str, str]]:
    """
    Modified Condition/Decision Coverage (MC/DC) nach DO-178C / ISO 26262.
    
    Erzeugt einen Baseline-Testfall + Variationen für jeden Wert jeder Kategorie.
    Jeder Wert erscheint in mindestens einem Pärchen mit sonst identischer Belegung.
    
    Das MC/DC-Kriterium verlangt:
    - Jede Bedingung (Kategorie) muss unabhängig das Ergebnis beeinflussen
    - Es existiert ein Testpaar das sich NUR in dieser Bedingung unterscheidet
    
    Args:
        categories: Dict[str, List[str]] – Kategorien mit Werten
        rule_engine: Optional[RuleEngine] – Regeln zur Constraint-Prüfung (REQ-3040)
    
    Returns:
        Liste von Testfällen (Dict[str, str])
    
    Beispiel:
        >>> cats = {"Auth": ["On", "Off"], "HTTPS": ["True", "False"]}
        >>> generate(cats)
        [
            {"Auth": "On", "HTTPS": "True"},      # Baseline
            {"Auth": "Off", "HTTPS": "True"},     # Auth-Variation
            {"Auth": "On", "HTTPS": "False"},     # HTTPS-Variation
        ]
    
    Komplexität:
        O(n * m) wobei n = Anzahl Kategorien, m = max. Werte pro Kategorie
        
    Constraint-Awareness (REQ-3040):
        - Ungültige Baseline → alternative Baseline suchen
        - Ungültige Variation → alternatives Paar suchen
        - Dependencies werden automatisch angewendet
    """
    if not categories:
        return []
    
    keys = list(categories.keys())
    
    # Schritt 1: Baseline-Testfall (erster Wert jeder Kategorie)
    baseline = {k: categories[k][0] for k in keys}
    
    # REQ-3040: Wenn RuleEngine gegeben, Baseline validieren
    if rule_engine is not None:
        if not rule_engine.is_combination_valid(baseline):
            # Baseline ungültig → alternative Baseline suchen
            baseline = _find_valid_baseline(categories, keys, rule_engine)
            if baseline is None:
                # Keine gültige Baseline → versuche irgendwelche gültigen Kombinationen
                return _generate_any_valid(categories, keys, rule_engine)
        baseline = rule_engine.apply_dependency_rules(baseline)
    
    testcases = [baseline]
    seen = {_tc_to_key(baseline)}
    
    # Schritt 2: Für jede Kategorie, für jeden Wert (außer Baseline-Wert): Variation erzeugen
    for cat in keys:
        baseline_value = baseline[cat]
        values = categories[cat]
        
        for val in values:
            if val == baseline_value:
                continue  # Baseline-Wert überspringen
            
            # Variation: Baseline mit cat=val
            variant = dict(baseline)
            variant[cat] = val
            
            # REQ-3040: Constraint-Check
            if rule_engine is not None:
                if not rule_engine.is_combination_valid(variant):
                    # Variant ungültig → versuche alternatives Paar zu finden
                    variant = _find_alternative_pair(categories, keys, cat, val, baseline, rule_engine)
                    if variant is None:
                        continue  # Keine gültige Variation für diesen Wert → überspringen
                variant = rule_engine.apply_dependency_rules(variant)
            
            # Duplikatprüfung
            key = _tc_to_key(variant)
            if key not in seen:
                testcases.append(variant)
                seen.add(key)
    
    return testcases


def _tc_to_key(tc: Dict[str, str]) -> tuple:
    """
    Konvertiert Testfall zu hashbarem Tupel für Duplikatprüfung.
    
    Args:
        tc: Testfall als Dict
        
    Returns:
        Tupel von sortierten (key, value) Paaren
    """
    return tuple(sorted(tc.items()))


def _find_valid_baseline(categories: Dict[str, List[str]], keys: List[str], rule_engine) -> Optional[Dict[str, str]]:
    """
    Sucht eine gültige Baseline, wenn die Standard-Baseline (erste Werte) ungültig ist.
    Probiert systematisch verschiedene Kombinationen.
    
    REQ-3040: Constraint-aware Baseline-Suche
    
    Args:
        categories: Kategorien-Dictionary
        keys: Sortierte Liste der Kategorienamen
        rule_engine: RuleEngine für Validierung
        
    Returns:
        Gültige Baseline oder None wenn keine gefunden
    """
    from itertools import product
    
    # Strategie: Probiere alle Kombinationen (limitiert auf erste 100 für Performance)
    for i, combo in enumerate(product(*[categories[k] for k in keys])):
        if i >= 100:  # Performance-Limit
            break
        candidate = {k: v for k, v in zip(keys, combo)}
        if rule_engine.is_combination_valid(candidate):
            return candidate
    
    return None


def _find_alternative_pair(
    categories: Dict[str, List[str]],
    keys: List[str],
    target_cat: str,
    target_val: str,
    baseline: Dict[str, str],
    rule_engine
) -> Optional[Dict[str, str]]:
    """
    Sucht ein alternatives Paar wenn die Standard-Variation ungültig ist.
    
    REQ-3040: Wenn baseline + target_cat=target_val verboten ist,
    suche gültige Kombination die target_val enthält.
    
    Strategie:
    1. Versuche Variation mit target_cat=target_val und einer anderen Kategorie variiert
    2. Versuche alle Kombinationen mit target_cat=target_val
    
    Args:
        categories: Kategorien-Dictionary
        keys: Sortierte Liste der Kategorienamen
        target_cat: Kategorie die variiert werden soll
        target_val: Zielwert für target_cat
        baseline: Original-Baseline
        rule_engine: RuleEngine für Validierung
        
    Returns:
        Gültige Variation oder None wenn keine gefunden
    """
    # Strategie 1: Variiere andere Kategorien systematisch (eine nach der anderen)
    for other_cat in keys:
        if other_cat == target_cat:
            continue
        
        for other_val in categories[other_cat]:
            candidate = dict(baseline)
            candidate[target_cat] = target_val
            candidate[other_cat] = other_val
            
            if rule_engine.is_combination_valid(candidate):
                return candidate
    
    # Strategie 2: Probiere alle Kombinationen mit target_cat=target_val
    from itertools import product
    
    other_keys = [k for k in keys if k != target_cat]
    for combo in product(*[categories[k] for k in other_keys]):
        candidate = {k: v for k, v in zip(other_keys, combo)}
        candidate[target_cat] = target_val
        
        if rule_engine.is_combination_valid(candidate):
            return candidate
    
    return None


def _generate_any_valid(categories: Dict[str, List[str]], keys: List[str], rule_engine) -> List[Dict[str, str]]:
    """
    Fallback wenn keine Standard-MC/DC-Generierung möglich ist.
    Sammelt einfach alle gültigen Kombinationen (limitiert).
    
    REQ-3040: Wird nur aufgerufen wenn keine gültige Baseline gefunden wurde.
    
    Args:
        categories: Kategorien-Dictionary
        keys: Sortierte Liste der Kategorienamen
        rule_engine: RuleEngine für Validierung
        
    Returns:
        Liste von gültigen Testfällen (limitiert auf 100)
    """
    from itertools import product
    
    valid = []
    seen = set()
    
    for i, combo in enumerate(product(*[categories[k] for k in keys])):
        if i >= 100:  # Performance-Limit
            break
        
        candidate = {k: v for k, v in zip(keys, combo)}
        if rule_engine.is_combination_valid(candidate):
            candidate = rule_engine.apply_dependency_rules(candidate)
            key = _tc_to_key(candidate)
            if key not in seen:
                valid.append(candidate)
                seen.add(key)
    
    return valid
