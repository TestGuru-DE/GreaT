import itertools


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


def _finalize_if_valid(rule_engine, candidate: dict):
    """Wendet Dependencies an und verwirft danach ungültige Kombinationen."""
    finalized = rule_engine.apply_dependency_rules(candidate)
    if not rule_engine.is_combination_valid(finalized):
        return None
    return finalized


def _find_valid_testcase_for_value(categories: dict, keys: list[str], rule_engine, target_key: str, target_value: str):
    """Findet deterministisch den ersten final gültigen Testfall für einen Zielwert."""
    for combo in itertools.product(*[categories[k] for k in keys]):
        raw_candidate = {k: v for k, v in zip(keys, combo)}
        candidate = _finalize_if_valid(rule_engine, raw_candidate)
        if candidate is None:
            continue
        if candidate.get(target_key) == target_value:
            return candidate
    return None


def generate(categories: dict, rule_engine=None) -> list[dict]:
    """
    Each Choice nach ISTQB v4: jeder Wert jeder Kategorie mindestens einmal.

    REQ-3040: Optional rule_engine für constraint-aware Generierung.
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

    covered_values = {k: set() for k in keys}
    testcases = []
    max_len = max(len(v) for v in categories.values())

    for i in range(max_len * 2):
        raw_tc = {}

        # Wähle Werte: priorisiere noch nicht abgedeckte Werte
        for k in keys:
            vals = categories[k]
            uncovered = [v for v in vals if v not in covered_values[k]]
            if uncovered:
                raw_tc[k] = uncovered[i % len(uncovered)]
            else:
                raw_tc[k] = vals[i % len(vals)]

        tc = _finalize_if_valid(rule_engine, raw_tc)

        if tc is None:
            valid_found = False

            # Strategie: Variiere jede Kategorie einzeln
            for k_vary in keys:
                vals_vary = categories[k_vary]
                original_val = raw_tc[k_vary]
                for alt_val in vals_vary:
                    if alt_val == original_val:
                        continue
                    candidate_raw = dict(raw_tc)
                    candidate_raw[k_vary] = alt_val
                    candidate = _finalize_if_valid(rule_engine, candidate_raw)
                    if candidate is not None:
                        tc = candidate
                        valid_found = True
                        break
                if valid_found:
                    break

            if not valid_found:
                for combo in itertools.product(*[categories[k] for k in keys]):
                    candidate_raw = {k: v for k, v in zip(keys, combo)}
                    candidate = _finalize_if_valid(rule_engine, candidate_raw)
                    if candidate is not None:
                        tc = candidate
                        valid_found = True
                        break

            if not valid_found:
                continue

        for k in keys:
            covered_values[k].add(tc[k])

        testcases.append(tc)

        if all(len(covered_values[k]) == len(categories[k]) for k in keys):
            break

    # Finale Coverage-Ergänzung: fehlende, aber final regelkonforme Werte gezielt nachziehen
    for k in keys:
        for value in categories[k]:
            if value in covered_values[k]:
                continue
            candidate = _find_valid_testcase_for_value(categories, keys, rule_engine, k, value)
            if candidate is None:
                continue
            testcases.append(candidate)
            for key in keys:
                covered_values[key].add(candidate[key])

    return deduplicate_testcases(testcases)
