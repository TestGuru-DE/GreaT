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

def generate(categories: dict) -> list[dict]:
    """All Combinations: Kreuzprodukt aller Werte."""
    if not categories:
        return []
    keys = list(categories.keys())
    values = [categories[k] for k in keys]
    combos = itertools.product(*values)
    testcases = [{k: v for k, v in zip(keys, c)} for c in combos]
    return deduplicate_testcases(testcases)
