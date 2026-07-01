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


def generate(categories: dict[str, list[tuple[str, int]]]) -> list[dict[str, str]]:
    """Risikogewichtete Testfall-Generierung nach REQ-0805.

    Args:
        categories: {Kategoriename: [(Wert, risk_weight), ...]}
                    risk_weight >= 1; höhere Werte → häufigeres Erscheinen.

    Returns:
        Liste von Testfällen: [{Kategoriename: Wert, ...}]
        Alle Werte erscheinen mindestens einmal (Each-Choice-Basisabdeckung).
    """
    if not categories:
        return []

    # Expandierten Pool je Kategorie aufbauen
    expanded: dict[str, list[str]] = {}
    for cat_name, weighted_values in categories.items():
        pool: list[str] = []
        for value, weight in weighted_values:
            pool.extend([value] * max(1, weight))
        expanded[cat_name] = pool

    # Anzahl Testfälle = Maximum der Pool-Längen
    max_len = max(len(pool) for pool in expanded.values())

    testcases: list[dict[str, str]] = []
    for i in range(max_len):
        tc: dict[str, str] = {}
        for cat_name, pool in expanded.items():
            tc[cat_name] = pool[i % len(pool)]
        testcases.append(tc)

    return testcases
