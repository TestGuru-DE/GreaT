# REQ-0805: Risikogewichtete Testfall-Generierung
#
# Algorithmus:
#   Input:  {Kategoriename: [(Wert, risk_weight), ...], ...}
#   Output: Testfall-Liste als [{Kategoriename: Wert, ...}, ...]
#
# Prinzip:
#   1. Jeder Wert wird entsprechend seinem risk_weight in den Pool expandiert
#      (risk_weight=3 → dreifache Häufigkeit im Pool)
#   2. Round-Robin über den expandierten Pool (wie each_choice)
#   3. Jeder Wert erscheint mindestens einmal (Each-Choice-Basisabdeckung)
#
# Formale Eigenschaft:
#   Sei W_i der Pool eines Werts mit risk_weight r_i:
#   P(W_i in TC_j) ≈ r_i / Σr_k – proportional zur Risikogewichtung.
from __future__ import annotations
from .budget import checkpoint  # BUG B-03


def generate(categories: dict[str, list[tuple[str, int]]], rule_engine=None) -> list[dict[str, str]]:
    """Risikogewichtete Testfall-Generierung nach REQ-0805.

    Args:
        categories: {Kategoriename: [(Wert, risk_weight), ...]}
                    risk_weight >= 1; höhere Werte → häufigeres Erscheinen.
        rule_engine: Optional; BUG K-07: Regeln/Constraints werden beim Erzeugen
                     beachtet, statt regelwidrige Testfaelle nachtraeglich zu verwerfen.

    Returns:
        Liste von Testfällen: [{Kategoriename: Wert, ...}]
        Alle (erreichbaren) Werte erscheinen mindestens einmal.
    """
    if not categories:
        return []

    # Expandierten Pool je Kategorie aufbauen
    expanded: dict[str, list[str]] = {}
    for cat_name, weighted_values in categories.items():
        checkpoint()  # BUG B-03: Zeitbudget
        pool: list[str] = []
        for value, weight in weighted_values:
            checkpoint()  # BUG B-03: Zeitbudget
            pool.extend([value] * max(1, weight))
        expanded[cat_name] = pool

    # Anzahl Testfälle = Maximum der Pool-Längen
    max_len = max(len(pool) for pool in expanded.values())

    testcases: list[dict[str, str]] = []
    for i in range(max_len):
        checkpoint()  # BUG B-03: Zeitbudget
        tc: dict[str, str] = {}
        for cat_name, pool in expanded.items():
            checkpoint()  # BUG B-03: Zeitbudget
            tc[cat_name] = pool[i % len(pool)]
        testcases.append(tc)

    if rule_engine is None:
        return testcases
    return _make_rule_compliant(testcases, categories, rule_engine)


def _make_rule_compliant(testcases, categories, rule_engine) -> list[dict[str, str]]:
    """BUG K-07: Regelwidrige Testfaelle reparieren und fehlende Werte ergaenzen.

    Je Testfall bleiben moeglichst viele Wunschwerte erhalten (Kategorien in
    Pool-Reihenfolge); Werte, die keinen gueltigen Testfall zulassen, werden
    durch den naechsten gewichteten Wert ersetzt.
    """
    from .feasibility import FeasibilityChecker

    plain = {cat: [v for v, _ in vals] for cat, vals in categories.items()}
    by_weight = {cat: [v for v, _ in sorted(vals, key=lambda vw: -vw[1])] for cat, vals in categories.items()}
    checker = FeasibilityChecker(plain, rule_engine)
    if not checker.is_satisfiable():
        return []

    result: list[dict[str, str]] = []
    seen: set = set()

    def add(tc):
        key = tuple(sorted(tc.items()))
        if key not in seen:
            seen.add(key)
            result.append(tc)

    for wish in testcases:
        checkpoint()
        partial: dict[str, str] = {}
        for cat, val in wish.items():
            if checker.is_feasible({**partial, cat: val}):
                partial[cat] = val
        completed = checker.complete(partial, by_weight)
        if completed is not None:
            add(completed)

    # Jeden erreichbaren Wert mindestens einmal (Each-Choice-Basisabdeckung)
    for cat, values in plain.items():
        for val in values:
            checkpoint()
            if any(tc.get(cat) == val for tc in result):
                continue
            completed = checker.complete({cat: val}, by_weight)
            if completed is not None:
                add(completed)
    return result


def compute_testcase_risk(testcase: dict[str, str], category_risk_map: dict[str, list[tuple[str, int]]]) -> float:
    """REQ-3034: Summiert den Risiko-Score eines Testfalls kategorie-gescoped.

    Fuer jede Kategorie im Testfall wird der zugewiesene Wert in der jeweiligen
    Kategorie-Werteliste (NICHT global/flach) nachgeschlagen und dessen risk_weight
    aufsummiert. Fehlt der Wert oder die Kategorie in category_risk_map, zaehlt er
    als 0 (kein KeyError). Es wird KEIN max(1, weight)-Floor angewendet (das ist
    Coverage-Semantik aus generate()/REQ-0805, nicht Risiko-Semantik).
    """
    total = 0.0
    for cat_name, value in testcase.items():
        checkpoint()  # BUG B-03: Zeitbudget
        weighted_values = category_risk_map.get(cat_name)
        if not weighted_values:
            continue
        for candidate_value, weight in weighted_values:
            checkpoint()  # BUG B-03: Zeitbudget
            if candidate_value == value:
                total += weight
                break
    return total


def sort_by_risk_descending(
    testcases: list[dict[str, str]], category_risk_map: dict[str, list[tuple[str, int]]]
) -> list[dict[str, str]]:
    """REQ-3034: Sortiert Testfaelle absteigend nach kumuliertem Risiko-Score.

    Eigenstaendige, von generate() getrennte Sortierfunktion. Deterministischer
    Tie-Break bei Punktgleichheit: urspruenglicher Listenindex aufsteigend
    (explizit im Sortierschluessel, nicht nur implizite Stabilitaet).
    Muss VOR sort_testcases_error_last() aufgerufen werden, damit dessen
    Fehlerwert-Vorrang (REQ-3018) die finale Reihenfolge dominiert.
    """
    indexed = list(enumerate(testcases))
    indexed.sort(key=lambda pair: (-compute_testcase_risk(pair[1], category_risk_map), pair[0]))
    return [tc for _, tc in indexed]
