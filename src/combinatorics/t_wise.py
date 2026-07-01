"""
REQ-3039: T-Wise Kombinatorik (parametrisiertes N-wise Testing)

Generiert Testfälle nach N-wise Coverage:
- t=1: Each Choice (jeder Wert mindestens einmal)
- t=2: Pairwise (alle 2-Tupel abgedeckt)
- t=3: Triple-wise (alle 3-Tupel abgedeckt)
- t >= len(categories): Kartesisches Produkt

Constraint-aware über RuleEngine: ungültige Tuples werden aus Coverage-Ziel entfernt.
"""
from itertools import combinations, product
from typing import Dict, List, Optional, Set, Tuple


def generate(categories: Dict[str, List[str]], t: int = 2, rule_engine=None) -> List[Dict[str, str]]:
    """
    Generiert Testfälle nach T-Wise Coverage.
    
    Args:
        categories: Dict[str, List[str]] – Kategorien mit Werten
        t: int – Coverage-Stärke (t=1: each, t=2: pairwise, t=3: triple-wise, ...)
        rule_engine: Optional[RuleEngine] – Regeln zur Constraint-Prüfung
    
    Returns:
        Liste von Testfällen (Dict[str, str])
    
    Raises:
        ValueError: wenn t < 1
    """
    if t < 1:
        raise ValueError(f"t muss >= 1 sein, bekam: {t}")
    
    if not categories or any(len(v) == 0 for v in categories.values()):
        return []
    
    cat_names = list(categories.keys())
    n_cats = len(cat_names)
    
    # Sonderfall: t=1 → Each Choice
    if t == 1:
        return _generate_each_choice(categories, cat_names, rule_engine)
    
    # Sonderfall: t >= n → Kartesisches Produkt
    if t >= n_cats:
        return _generate_cartesian(categories, cat_names, rule_engine)
    
    # Hauptfall: t-wise Coverage mit Greedy
    return _generate_t_wise_greedy(categories, cat_names, t, rule_engine)


def _generate_each_choice(
    categories: Dict[str, List[str]], 
    cat_names: List[str], 
    rule_engine
) -> List[Dict[str, str]]:
    """Generiert Each Choice Coverage (t=1)."""
    # Jeder Wert jeder Kategorie muss mindestens einmal vorkommen
    covered_values = {cat: set() for cat in cat_names}
    testcases = []
    max_len = max(len(v) for v in categories.values())
    
    # Greedy: Baue Testfälle bis alle Werte abgedeckt
    for i in range(max_len * 2):  # Safety-Factor für Constraints
        tc = {}
        
        # Wähle für jede Kategorie einen noch nicht abgedeckten Wert (wenn möglich)
        for cat in cat_names:
            vals = categories[cat]
            uncovered = [v for v in vals if v not in covered_values[cat]]
            if uncovered:
                tc[cat] = uncovered[i % len(uncovered)]
            else:
                tc[cat] = vals[i % len(vals)]
        
        # Constraint-Check
        if rule_engine is not None:
            if not rule_engine.is_combination_valid(tc):
                # Versuche alternatives Assignment
                tc = _find_valid_alternative(tc, categories, cat_names, rule_engine)
                if tc is None:
                    continue
            tc = rule_engine.apply_dependency_rules(tc)
        
        # Markiere abgedeckte Werte
        for cat in cat_names:
            covered_values[cat].add(tc[cat])
        
        testcases.append(tc)
        
        # Abbruch: alle Werte abgedeckt
        if all(len(covered_values[cat]) == len(categories[cat]) for cat in cat_names):
            break
    
    return testcases


def _generate_cartesian(
    categories: Dict[str, List[str]], 
    cat_names: List[str], 
    rule_engine
) -> List[Dict[str, str]]:
    """Generiert kartesisches Produkt (t >= n)."""
    testcases = []
    
    for values in product(*[categories[cat] for cat in cat_names]):
        tc = {cat: val for cat, val in zip(cat_names, values)}
        
        # Constraint-Check
        if rule_engine is not None:
            if not rule_engine.is_combination_valid(tc):
                continue
            tc = rule_engine.apply_dependency_rules(tc)
        
        testcases.append(tc)
    
    return testcases


def _generate_t_wise_greedy(
    categories: Dict[str, List[str]], 
    cat_names: List[str], 
    t: int, 
    rule_engine
) -> List[Dict[str, str]]:
    """Generiert T-Wise Coverage mit Greedy-Algorithmus."""
    
    # 1. Baue Coverage-Ziel: alle gültigen t-Tupel
    uncovered_tuples = _build_coverage_goal(categories, cat_names, t, rule_engine)
    
    if not uncovered_tuples:
        return []
    
    testcases = []
    
    # 2. Greedy: Wähle Testfälle, die maximale Coverage bringen
    max_iterations = len(uncovered_tuples) * 2  # Safety-Limit
    iteration = 0
    
    while uncovered_tuples and iteration < max_iterations:
        iteration += 1
        
        # Finde besten Testfall (maximaler Coverage-Gewinn)
        best_tc = _find_best_testcase(
            categories, cat_names, t, uncovered_tuples, rule_engine
        )
        
        if best_tc is None:
            # Keine gültigen Testfälle mehr möglich
            break
        
        testcases.append(best_tc)
        
        # Entferne abgedeckte Tuples
        covered = _extract_covered_tuples(best_tc, cat_names, t)
        uncovered_tuples -= covered
    
    return testcases


def _build_coverage_goal(
    categories: Dict[str, List[str]], 
    cat_names: List[str], 
    t: int, 
    rule_engine
) -> Set[Tuple]:
    """
    Baut Coverage-Ziel: alle gültigen t-Tupel.
    
    Returns:
        Set von Tuples: (cat1, cat2, ..., catT, val1, val2, ..., valT)
    """
    goal = set()
    
    # Für jede Kombination von t Kategorien
    for cat_subset in combinations(cat_names, t):
        # Für jede Wert-Kombination dieser Kategorien
        value_lists = [categories[cat] for cat in cat_subset]
        
        for value_tuple in product(*value_lists):
            # Constraint-Check
            if rule_engine is not None:
                partial = {cat: val for cat, val in zip(cat_subset, value_tuple)}
                if not rule_engine.is_combination_valid(partial):
                    continue
            
            # Tuple speichern: (Kategorien..., Werte...)
            tuple_key = cat_subset + value_tuple
            goal.add(tuple_key)
    
    return goal


def _extract_covered_tuples(
    testcase: Dict[str, str], 
    cat_names: List[str], 
    t: int
) -> Set[Tuple]:
    """Extrahiert alle t-Tupel, die von diesem Testfall abgedeckt werden."""
    covered = set()
    
    for cat_subset in combinations(cat_names, t):
        # Baue Tuple aus Testfall
        value_tuple = tuple(testcase[cat] for cat in cat_subset)
        tuple_key = cat_subset + value_tuple
        covered.add(tuple_key)
    
    return covered


def _find_best_testcase(
    categories: Dict[str, List[str]], 
    cat_names: List[str], 
    t: int, 
    uncovered_tuples: Set[Tuple], 
    rule_engine
) -> Optional[Dict[str, str]]:
    """
    Findet den Testfall mit maximalem Coverage-Gewinn.
    
    Strategie: Greedy – durchlaufe alle möglichen Assignments,
    wähle den mit den meisten noch unabgedeckten Tuples.
    """
    best_tc = None
    best_gain = -1
    
    # Generiere Kandidaten (sample für Performance)
    # Bei großen Categories: nutze Heuristik
    if _is_large_space(categories):
        candidates = _generate_candidate_sample(categories, cat_names, rule_engine, sample_size=1000)
    else:
        # Kleine Categories: alle Kombinationen
        candidates = list(product(*[categories[cat] for cat in cat_names]))
        candidates = [
            {cat: val for cat, val in zip(cat_names, vals)}
            for vals in candidates
        ]
        if rule_engine is not None:
            candidates = [
                tc for tc in candidates
                if rule_engine.is_combination_valid(tc)
            ]
    
    for tc in candidates:
        if rule_engine is not None:
            tc = rule_engine.apply_dependency_rules(tc)
        
        # Zähle Coverage-Gewinn
        covered = _extract_covered_tuples(tc, cat_names, t)
        gain = len(covered & uncovered_tuples)
        
        if gain > best_gain:
            best_gain = gain
            best_tc = tc
    
    return best_tc


def _is_large_space(categories: Dict[str, List[str]]) -> bool:
    """Prüft ob Suchraum zu groß für vollständige Enumeration ist."""
    size = 1
    for vals in categories.values():
        size *= len(vals)
        if size > 10000:
            return True
    return False


def _generate_candidate_sample(
    categories: Dict[str, List[str]], 
    cat_names: List[str], 
    rule_engine, 
    sample_size: int
) -> List[Dict[str, str]]:
    """Generiert Sample von Kandidaten für große Suchräume."""
    import random
    
    candidates = []
    max_attempts = sample_size * 5
    attempt = 0
    
    while len(candidates) < sample_size and attempt < max_attempts:
        attempt += 1
        
        # Random Assignment
        tc = {cat: random.choice(categories[cat]) for cat in cat_names}
        
        # Constraint-Check
        if rule_engine is not None:
            if not rule_engine.is_combination_valid(tc):
                continue
        
        candidates.append(tc)
    
    return candidates


def _find_valid_alternative(
    tc: Dict[str, str], 
    categories: Dict[str, List[str]], 
    cat_names: List[str], 
    rule_engine
) -> Optional[Dict[str, str]]:
    """Sucht gültige Alternative für ungültigen Testfall."""
    # Variiere jede Kategorie einzeln
    for cat_vary in cat_names:
        original_val = tc[cat_vary]
        for alt_val in categories[cat_vary]:
            if alt_val == original_val:
                continue
            
            tc_new = dict(tc)
            tc_new[cat_vary] = alt_val
            
            if rule_engine.is_combination_valid(tc_new):
                return tc_new
    
    # Keine gültige Alternative gefunden
    return None
