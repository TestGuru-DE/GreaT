"""Kombinatorik-Hilfsfunktionen."""
from typing import Dict, List


def compute_cartesian_size(categories: Dict[str, List[str]]) -> int:
    """Berechnet die Groesse des kartesischen Produkts aller Kategorien.

    Args:
        categories: Mapping von Kategoriename zu Werteliste.

    Returns:
        Produkt der Laengen aller Wertelisten. 1 wenn categories leer.
    """
    size = 1
    for vals in categories.values():
        size *= len(vals)
    return size