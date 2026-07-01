from itertools import product
from typing import Dict, List, Tuple, Set, Optional

def _all_pairs(categories: Dict[str, List[str]], rule_engine=None) -> Set[Tuple[str, str, str, str]]:
    """
    REQ-3040: Erzeugt alle Paare, optional gefiltert durch Regeln.
    Wenn rule_engine gegeben ist, werden nur gültige Paare zurückgegeben.
    """
    keys = list(categories.keys())
    universe: Set[Tuple[str, str, str, str]] = set()
    for i, k1 in enumerate(keys):
        for j, k2 in enumerate(keys):
            if i >= j:
                continue
            for a in categories[k1]:
                for b in categories[k2]:
                    # REQ-3040: Prüfe ob dieses Paar gültig ist
                    if rule_engine is not None:
                        partial = {k1: a, k2: b}
                        if not rule_engine.is_combination_valid(partial):
                            continue  # Ungültiges Paar überspringen
                    universe.add((k1, k2, a, b))
    return universe

def _pairs_covered_by_assignment(assignment: Dict[str, str]) -> Set[Tuple[str, str, str, str]]:
    keys = list(assignment.keys())
    covered=set()
    for i, k1 in enumerate(keys):
        for j, k2 in enumerate(keys):
            if i >= j:
                continue
            covered.add((k1, k2, assignment[k1], assignment[k2]))
    return covered

def generate(categories: Dict[str, List[str]], rule_engine=None) -> List[Dict[str, str]]:
    """
    Pairwise/Orthogonal-ähnliche Erzeugung über eine einfache Greedy-Heuristik.
    Deckt alle 2er-Kombinationen zwischen Kategorien ab.
    
    REQ-3040: Mit rule_engine werden nur gültige Paare abgedeckt und
    ungültige Testfälle übersprungen.
    
    Args:
        categories: Dict[str, List[str]] – Kategorien mit Werten
        rule_engine: Optional[RuleEngine] – Regeln zur Constraint-Prüfung
    
    Returns:
        Liste von Testfällen (Dict[str, str])
    """
    if not categories or any(len(v)==0 for v in categories.values()):
        return []
    keys = list(categories.keys())
    if len(keys) == 1:
        result = [{keys[0]: v} for v in categories[keys[0]]]
        # REQ-3040: Dependencies anwenden auch bei einer Kategorie
        if rule_engine is not None:
            result = [rule_engine.apply_dependency_rules(tc) for tc in result]
        return result

    # REQ-3040: Universe enthält nur gültige Paare
    universe = _all_pairs(categories, rule_engine=rule_engine)
    suite: List[Dict[str, str]] = []

    # Seed: erster Wert jeder Kategorie
    seed = {k: categories[k][0] for k in keys}
    
    # REQ-3040: Seed auf Gültigkeit prüfen
    if rule_engine is not None:
        if not rule_engine.is_combination_valid(seed):
            seed = _find_valid_seed(categories, keys, rule_engine)
            if seed is None:
                # Kein gültiger Seed gefunden – versuche mit einzelnen Assignments
                return _generate_fallback(categories, keys, rule_engine)
        seed = rule_engine.apply_dependency_rules(seed)
    
    suite.append(seed)
    covered = _pairs_covered_by_assignment(seed)

    # Alle möglichen Assignments generieren
    all_assignments = list(product(*[categories[k] for k in keys]))
    assignment_dicts: List[Dict[str, str]] = [{k: v for k, v in zip(keys, assg)} for assg in all_assignments]
    
    # REQ-3040: Ungültige Assignments herausfiltern
    if rule_engine is not None:
        valid_assignments = []
        for a in assignment_dicts:
            if rule_engine.is_combination_valid(a):
                a = rule_engine.apply_dependency_rules(a)
                valid_assignments.append(a)
        assignment_dicts = [a for a in valid_assignments if a != seed]
    else:
        assignment_dicts = [a for a in assignment_dicts if a != seed]

    # Greedy: Wähle Assignment mit größtem Coverage-Gewinn
    while covered != universe and assignment_dicts:
        best = None
        best_gain = -1
        for a in assignment_dicts:
            gain = len(_pairs_covered_by_assignment(a) - covered)
            if gain > best_gain:
                best_gain = gain
                best = a
        if best is None or best_gain == 0:
            break
        suite.append(best)
        covered |= _pairs_covered_by_assignment(best)
        assignment_dicts.remove(best)

    # Rest: Füge Assignments hinzu die noch fehlende Paare abdecken
    if covered != universe:
        for a in assignment_dicts:
            if covered == universe:
                break
            new_pairs = _pairs_covered_by_assignment(a) - covered
            if new_pairs:
                suite.append(a)
                covered |= new_pairs
    
    return suite


def _find_valid_seed(categories: Dict[str, List[str]], keys: List[str], rule_engine) -> Optional[Dict[str, str]]:
    """REQ-3040: Sucht einen gültigen Seed-Testfall."""
    # Versuche verschiedene Kombinationen
    for vals in product(*[categories[k] for k in keys]):
        candidate = {k: v for k, v in zip(keys, vals)}
        if rule_engine.is_combination_valid(candidate):
            return candidate
    return None


def _generate_fallback(categories: Dict[str, List[str]], keys: List[str], rule_engine) -> List[Dict[str, str]]:
    """REQ-3040: Fallback wenn kein gültiger Seed gefunden wurde."""
    # Generiere alle möglichen Assignments und filtere gültige
    all_assignments = list(product(*[categories[k] for k in keys]))
    valid = []
    for vals in all_assignments:
        candidate = {k: v for k, v in zip(keys, vals)}
        if rule_engine.is_combination_valid(candidate):
            candidate = rule_engine.apply_dependency_rules(candidate)
            valid.append(candidate)
    
    # Nehme alle gültigen (Pairwise-Optimierung unmöglich wenn fast alles verboten ist)
    return valid[:min(len(valid), 10)]  # Limit auf 10 um Explosion zu vermeiden
