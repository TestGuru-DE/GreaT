"""
Lineare Expansion – REQ-0803
ISTQB: Ein Basisfall (alle ersten Werte) + je ein Testfall pro abweichendem Wert.
Genau ein Wert weicht vom Standard ab, alle anderen Werte sind Standardwerte.
"""
from typing import Dict, List


def generate(categories: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """
    Erzeugt Testfälle nach dem Prinzip der linearen Expansion.

    Algorithmus:
    1. Basisfall: erster Wert jeder Kategorie
    2. Für jede Kategorie, für jeden nicht-ersten Wert:
       Basisfall kopieren, diesen einen Wert ersetzen → neuer Testfall

    Anzahl Testfälle: 1 + Summe(len(Werte_i) - 1 für alle Kategorien i)
    """
    if not categories:
        return []

    keys = list(categories.keys())
    basis: Dict[str, str] = {k: categories[k][0] for k in keys}
    result: List[Dict[str, str]] = [dict(basis)]

    for key in keys:
        werte = categories[key]
        for wert in werte[1:]:  # alle außer dem ersten (Standard-)Wert
            tc = dict(basis)
            tc[key] = wert
            result.append(tc)

    return result
