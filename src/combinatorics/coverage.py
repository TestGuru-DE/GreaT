"""
REQ-6008: Abdeckungsanzeige als Matrix/Heatmap.

Berechnet t-wise Coverage (1-wise, 2-wise, 3-wise) und Heatmap-Daten
unter Beruecksichtigung von Regeln/Constraints und Ergebnis-Kategorien.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CoverageResult:
    """Ergebnis der t-wise Abdeckungsanalyse."""
    t: int
    covered: int
    possible: int
    percentage: float
    excluded_by_rules: int
    uncovered_tuples: list = field(default_factory=list)


@dataclass
class CellData:
    """Einzelne Zelle in der Heatmap."""
    count: int
    status: str
    symbol: str


@dataclass
class HeatmapResult:
    """Ergebnis der Heatmap-Berechnung fuer zwei Kategorien."""
    rows: list
    cols: list
    cells: dict = field(default_factory=dict)
    uncovered_tuples: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Status / Symbol Mapping
# ---------------------------------------------------------------------------

_STATUS_SYMBOL = {
    "covered": "\u2713",
    "uncovered": "\u2717",
    "excluded": "\u2298",
}


# ---------------------------------------------------------------------------
# calculate_coverage
# ---------------------------------------------------------------------------


def calculate_coverage(
    testcases: List[Dict[str, str]],
    categories: Dict[str, List[str]],
    t: int,
    rule_engine=None,
    result_category_names: Optional[List[str]] = None,
) -> CoverageResult:
    """
    Berechnet die t-wise Abdeckung einer Testfallmenge.

    Args:
        testcases: Liste von {category_name: value_name}
        categories: {category_name: [value1, value2, ...]}
        t: Strength (1, 2, 3, ...)
        rule_engine: Optional RuleEngine-Instanz
        result_category_names: Liste von Ergebnis-Kategorienamen (werden ignoriert)

    Returns:
        CoverageResult mit covered, possible, percentage, excluded_by_rules, uncovered_tuples
    """
    result_names = set(result_category_names or [])

    # Kategorien filtern: Ergebnis-Kategorien entfernen
    active_cats = {
        name: vals
        for name, vals in categories.items()
        if name not in result_names
    }

    if not active_cats:
        return CoverageResult(
            t=t, covered=0, possible=0, percentage=0.0,
            excluded_by_rules=0, uncovered_tuples=[],
        )

    cat_names = sorted(active_cats.keys())

    # Wenn t > Anzahl der Kategorien:
    # - n < 2: keine t-wise Tupel moeglich (Paare benoetigen >=2 Kategorien)
    # - n >= 2: kartesisches Produkt aller Kategorien (t wird auf n reduziert)
    if t > len(cat_names):
        if len(cat_names) < 2:
            return CoverageResult(
                t=t, covered=0, possible=0, percentage=0.0,
                excluded_by_rules=0, uncovered_tuples=[],
            )
        t = len(cat_names)

    # REQ-6008: Groessenpruefung fuer 3-wise (Abbruch >5 Mio Tripel)
    if t >= 3:
        from math import comb
        # Schatze maximale Anzahl moeglicher Tupel
        max_tuples = comb(len(cat_names), t)
        for vals in active_cats.values():
            max_tuples *= len(vals)
        if max_tuples > 5_000_000:
            raise ValueError(
                f"3-wise Abbruch: {max_tuples:,} moegliche Tripel ueberschreiten "
                f"das Limit von 5.000.000. Reduziere Kategorien oder Werte."
            )

    # Alle moeglichen t-wise Tupel generieren
    all_possible, excluded = _get_all_tuples(
        cat_names, active_cats, t, rule_engine
    )

    # Abgedeckte Tupel ermitteln
    covered_set = _get_covered_tuples(testcases, cat_names, active_cats, t)

    covered = len(covered_set & all_possible)
    possible = len(all_possible)
    excluded_count = len(excluded)

    # Unabgedeckte Tupel (nur die, die moeglich sind)
    uncovered = sorted(all_possible - covered_set)

    percentage = round((covered / possible) * 100, 2) if possible > 0 else 0.0

    return CoverageResult(
        t=t,
        covered=covered,
        possible=possible,
        percentage=percentage,
        excluded_by_rules=excluded_count,
        uncovered_tuples=uncovered,
    )


# ---------------------------------------------------------------------------
# compute_heatmap
# ---------------------------------------------------------------------------


def compute_heatmap(
    cat_a: str,
    cat_b: str,
    testcases: List[Dict[str, str]],
    categories: Dict[str, List[str]],
    rule_engine=None,
) -> HeatmapResult:
    """
    Berechnet eine Heatmap-Matrix fuer zwei Kategorien.

    Args:
        cat_a: Name der Zeilen-Kategorie
        cat_b: Name der Spalten-Kategorie
        testcases: Liste von {category_name: value_name}
        categories: {category_name: [value1, value2, ...]}
        rule_engine: Optional RuleEngine-Instanz

    Returns:
        HeatmapResult mit rows, cols, cells, uncovered_tuples
    """
    if cat_a not in categories:
        raise ValueError(f"Unbekannte Kategorie: {cat_a}")
    if cat_b not in categories:
        raise ValueError(f"Unbekannte Kategorie: {cat_b}")

    rows = list(categories[cat_a])
    cols = list(categories[cat_b])

    cells = {}
    uncovered = []

    for row_val in rows:
        for col_val in cols:
            count = sum(
                1
                for tc in testcases
                if tc.get(cat_a) == row_val and tc.get(cat_b) == col_val
            )

            partial_tc = {cat_a: row_val, cat_b: col_val}

            if rule_engine is not None and not rule_engine.is_combination_valid(partial_tc):
                status = "excluded"
            elif count > 0:
                status = "covered"
            else:
                status = "uncovered"
                uncovered.append((row_val, col_val))

            cells[(row_val, col_val)] = CellData(
                count=count,
                status=status,
                symbol=_STATUS_SYMBOL[status],
            )

    return HeatmapResult(
        rows=rows,
        cols=cols,
        cells=cells,
        uncovered_tuples=uncovered,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_all_tuples(
    cat_names: List[str],
    active_cats: Dict[str, List[str]],
    t: int,
    rule_engine=None,
) -> Tuple[set, set]:
    """
    Generiert alle moeglichen t-wise Tupel und trennt sie in
    "moeglich" (nicht durch Regeln ausgeschlossen) und "excluded".

    Returns:
        (possible_set, excluded_set)
    """
    all_tuples = _generate_all_tuples(cat_names, active_cats, t)

    if rule_engine is None:
        return all_tuples, set()

    possible = set()
    excluded = set()

    for tup in all_tuples:
        # Partial testcase fuer is_combination_valid bauen
        partial_tc = {cat: val for cat, val in tup}
        if rule_engine.is_combination_valid(partial_tc):
            possible.add(tup)
        else:
            excluded.add(tup)

    return possible, excluded


def _generate_all_tuples(
    cat_names: List[str],
    active_cats: Dict[str, List[str]],
    t: int,
) -> set:
    """
    Generiert alle moeglichen t-wise Tupel als frozenset von (cat, val) Paaren.
    """
    result = set()

    if t == 1:
        # 1-wise: jeder Wert jeder Kategorie
        for cat_name in cat_names:
            for val in active_cats[cat_name]:
                result.add(frozenset([(cat_name, val)]))
    else:
        # t-wise: alle Kombinationen von t Kategorien, dann kartesisches Produkt
        for cat_combo in combinations(cat_names, t):
            value_lists = [active_cats[c] for c in cat_combo]
            for vals in product(*value_lists):
                tup = frozenset(zip(cat_combo, vals))
                result.add(tup)

    return result


def _get_covered_tuples(
    testcases: List[Dict[str, str]],
    cat_names: List[str],
    active_cats: Dict[str, List[str]],
    t: int,
) -> set:
    """
    Ermittelt welche t-wise Tupel durch die Testfaelle abgedeckt sind.
    """
    covered = set()

    if not testcases:
        return covered

    for tc in testcases:
        # Nur Werte aus aktiven Kategorien nehmen
        tc_filtered = {
            cat: tc[cat]
            for cat in cat_names
            if cat in tc and tc[cat] in active_cats[cat]
        }

        if t == 1:
            # 1-wise: jeder Wert einzeln
            for cat, val in tc_filtered.items():
                covered.add(frozenset([(cat, val)]))
        else:
            # t-wise: alle t-Kombinationen aus den gesetzten Kategorien
            tc_cats = sorted(tc_filtered.keys())
            if len(tc_cats) >= t:
                for cat_combo in combinations(tc_cats, t):
                    vals = tuple(tc_filtered[c] for c in cat_combo)
                    tup = frozenset(zip(cat_combo, vals))
                    covered.add(tup)

    return covered