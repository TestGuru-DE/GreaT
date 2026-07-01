def deduplicate_testcases(testcases: list[dict]) -> list[dict]:
    """Entfernt Duplikate aus Testfall-Liste (BUG-4 Fix)."""
    seen = set()
    result = []
    for tc in testcases:
        key = tuple(sorted(tc.items()))
        if key not in seen:
            seen.add(key)
            result.append(tc)
    return result

def generate(categories: dict, rule_engine=None) -> list[dict]:
    """
    Each Choice nach ISTQB v4: jeder Wert jeder Kategorie mindestens einmal.
    
    REQ-3040: Optional rule_engine für constraint-aware Generierung.
    Ungültige Kombinationen werden während der Generierung übersprungen,
    aber es wird sichergestellt dass jeder Wert mindestens einmal erscheint.
    
    Args:
        categories: Dict[str, List[str]] – Kategorien mit Werten
        rule_engine: Optional[RuleEngine] – Regeln zur Constraint-Prüfung
    
    Returns:
        Liste von Testfällen (Dict[str, str])
    """
    if not categories:
        return []
    
    keys = list(categories.keys())
    
    # REQ-3040: Wenn keine Regeln, nutze alte Logik (performanter)
    if rule_engine is None:
        max_len = max(len(v) for v in categories.values())
        testcases = []
        for i in range(max_len):
            tc = {}
            for k in keys:
                vals = categories[k]
                tc[k] = vals[i % len(vals)]
            testcases.append(tc)
        return deduplicate_testcases(testcases)
    
    # REQ-3040: Mit Regeln – Coverage-basierter Ansatz
    # Stelle sicher dass jeder Wert jeder Kategorie mindestens einmal erscheint
    covered_values = {k: set() for k in keys}
    testcases = []
    max_len = max(len(v) for v in categories.values())
    
    for i in range(max_len * 2):  # Mehr Iterationen für Constraint-Fälle
        tc = {}
        
        # Wähle Werte: Priorisiere noch nicht abgedeckte Werte
        for k in keys:
            vals = categories[k]
            # Versuche zuerst unabgedeckte Werte
            uncovered = [v for v in vals if v not in covered_values[k]]
            if uncovered:
                tc[k] = uncovered[i % len(uncovered)]
            else:
                tc[k] = vals[i % len(vals)]
        
        # Constraint-Check
        if not rule_engine.is_combination_valid(tc):
            # Versuche alternative Kombinationen durch systematisches Variieren
            valid_found = False
            # Strategie: Variiere jede Kategorie einzeln
            for k_vary in keys:
                vals_vary = categories[k_vary]
                original_val = tc[k_vary]
                for alt_val in vals_vary:
                    if alt_val == original_val:
                        continue
                    tc[k_vary] = alt_val
                    if rule_engine.is_combination_valid(tc):
                        valid_found = True
                        break
                if valid_found:
                    break
                tc[k_vary] = original_val  # Zurücksetzen wenn nicht erfolgreich
            
            if not valid_found:
                # Versuche zufällige Kombinationen
                import itertools
                for combo in itertools.product(*[categories[k] for k in keys]):
                    candidate = {k: v for k, v in zip(keys, combo)}
                    if rule_engine.is_combination_valid(candidate):
                        tc = candidate
                        valid_found = True
                        break
            
            if not valid_found:
                continue  # Überspringen wenn wirklich keine gültige Kombination gefunden
        
        # Dependencies anwenden
        tc = rule_engine.apply_dependency_rules(tc)
        
        # Aktualisiere Coverage
        for k in keys:
            covered_values[k].add(tc[k])
        
        testcases.append(tc)
        
        # Abbruchbedingung: Alle Werte abgedeckt
        if all(len(covered_values[k]) == len(categories[k]) for k in keys):
            break
    
    return deduplicate_testcases(testcases)
