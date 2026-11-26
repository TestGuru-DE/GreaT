"""
REQ-6008: Abdeckungsanzeige als Matrix/Heatmap.

Berechnet t-wise Coverage (1-wise, 2-wise, 3-wise) und Heatmap-Daten
unter Beruecksichtigung von Regeln/Constraints und Ergebnis-Kategorien.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Dict, List, Optional, Tuple


# Obergrenze fuer die Abdeckungsberechnung (t >= 3)
MAX_COVERAGE_TUPLES = 5_000_000


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
    excluded_tuples: list = field(default_factory=list)  # BUG K-11: wirklich unmoegliche Tupel


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
    hierarchy=None,
    feasibility=None,
) -> CoverageResult:
    """
    Berechnet die t-wise Abdeckung einer Testfallmenge.

    REQ-6016: Optional hierarchy-Parameter fuer hierarchische Klassen.
    Paare mit Unter-Kategorien werden nur in Kombination mit dem
    Eltern-Wert als "moeglich" gezahlt.

    Args:
        testcases: Liste von {category_name: value_name}
        categories: {category_name: [value1, value2, ...]}
        t: Strength (1, 2, 3, ...)
        rule_engine: Optional RuleEngine-Instanz
        result_category_names: Liste von Ergebnis-Kategorienamen (werden ignoriert)
        hierarchy: Optional HierarchyDescriptor fuer REQ-6016

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

    # REQ-6008 / BUG K-04: Groessenpruefung ueber die echte Anzahl der t-Tupel
    # (Summe ueber Kategorie-Tripel), nicht das Produkt aller Werteanzahlen.
    if t >= 3:
        from .budget import count_t_tuples
        max_tuples = count_t_tuples(active_cats, t)
        if max_tuples > MAX_COVERAGE_TUPLES:
            raise ValueError(
                f"{t}-wise Abbruch: {max_tuples:,} moegliche Tupel ueberschreiten "
                f"das Limit von {MAX_COVERAGE_TUPLES:,}. Reduziere Kategorien oder Werte."
            )

    # Alle moeglichen t-wise Tupel generieren
    all_possible, excluded = _get_all_tuples(
        cat_names, active_cats, t, rule_engine, hierarchy, feasibility
    )

    # Abgedeckte Tupel ermitteln
    covered_set = _get_covered_tuples(testcases, cat_names, active_cats, t)

    covered = len(covered_set & all_possible)
    possible = len(all_possible)
    excluded_count = len(excluded)

    # Unabgedeckte Tupel (nur die, die moeglich sind)
    uncovered = sorted(all_possible - covered_set, key=sorted)

    percentage = round((covered / possible) * 100, 2) if possible > 0 else 0.0

    return CoverageResult(
        t=t,
        covered=covered,
        possible=possible,
        percentage=percentage,
        excluded_by_rules=excluded_count,
        uncovered_tuples=uncovered,
        excluded_tuples=sorted(excluded, key=sorted),
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
    hierarchy=None,
    feasibility=None,
) -> HeatmapResult:
    """
    Berechnet eine Heatmap-Matrix fuer zwei Kategorien.

    REQ-6016: Optional hierarchy-Parameter fuer hierarchische Klassen.
    Zellen mit Unter-Kategorien werden als "excluded" markiert, wenn
    der Eltern-Wert nicht aktiv ist.

    Args:
        cat_a: Name der Zeilen-Kategorie
        cat_b: Name der Spalten-Kategorie
        testcases: Liste von {category_name: value_name}
        categories: {category_name: [value1, value2, ...]}
        rule_engine: Optional RuleEngine-Instanz
        hierarchy: Optional HierarchyDescriptor fuer REQ-6016

    Returns:
        HeatmapResult mit rows, cols, cells, uncovered_tuples
    """
    if cat_a not in categories:
        raise ValueError(f"Unbekannte Kategorie: {cat_a}")
    if cat_b not in categories:
        raise ValueError(f"Unbekannte Kategorie: {cat_b}")

    rows = list(categories[cat_a])
    cols = list(categories[cat_b])

    # Leistung: Paare einmal zaehlen statt je Zelle alle Testfaelle zu durchlaufen
    from collections import Counter
    counts = Counter((tc.get(cat_a), tc.get(cat_b)) for tc in testcases)
    checker = _checker(categories, rule_engine, feasibility)

    cells = {}
    uncovered = []

    for row_val in rows:
        for col_val in cols:
            count = counts.get((row_val, col_val), 0)

            partial_tc = {cat_a: row_val, cat_b: col_val}

            # REQ-6016: Hierarchie-Check
            hierarchy_excluded = False
            if hierarchy is not None:
                hierarchy_excluded = _is_hierarchy_excluded(
                    partial_tc, cat_a, cat_b, hierarchy
                )

            if hierarchy_excluded:
                status = "excluded"
            elif checker is not None and not checker.is_feasible(partial_tc):  # BUG K-06
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
    hierarchy=None,
    feasibility=None,
) -> Tuple[set, set]:
    """
    Generiert alle moeglichen t-wise Tupel und trennt sie in
    "moeglich" (nicht durch Regeln ausgeschlossen) und "excluded".

    REQ-6016: Bei Hierarchie werden Tupel ausgeschlossen, bei denen
    eine Unter-Kategorie einen Wert ungleich "-" hat, waehrend der
    Eltern-Wert nicht aktiv ist.

    Returns:
        (possible_set, excluded_set)
    """
    all_tuples = _generate_all_tuples(cat_names, active_cats, t)

    # REQ-6016: Hierarchie-Filter anwenden
    if hierarchy is not None:
        all_tuples = _filter_hierarchy_tuples(all_tuples, hierarchy)

    checker = _checker(active_cats, rule_engine, feasibility)
    if checker is None:
        return all_tuples, set()

    possible = set()
    excluded = set()

    for tup in all_tuples:
        # BUG K-06: moeglich nur, wenn ein vollstaendiger gueltiger Testfall das Tupel
        # enthaelt (auch ueber verkettete Constraints unmoegliche Tupel werden erkannt)
        if checker.is_feasible(dict(tup)):
            possible.add(tup)
        else:
            excluded.add(tup)

    return possible, excluded


def _checker(categories, rule_engine, feasibility=None):
    """FeasibilityChecker fuer die Kategorien (oder None ohne Regeln)."""
    if feasibility is not None:
        return feasibility
    if rule_engine is None:
        return None
    from .feasibility import FeasibilityChecker
    return FeasibilityChecker(categories, rule_engine)


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


def _filter_hierarchy_tuples(
    tuples: set,
    hierarchy,
) -> set:
    """
    REQ-6016: Filtert Tupel, die gegen Hierarchie-Constraints verstoßen.

    Ein Tupel ist ungültig, wenn es eine Kind-Kategorie C mit Wert W enthält,
    wobei W != "-" (N/A), aber der Eltern-Wert P nicht im Tupel enthalten ist
    oder ein anderer Wert als P hat.

    Args:
        tuples: Set von frozenset((cat, val), ...) Tupeln
        hierarchy: HierarchyDescriptor

    Returns:
        Gefiltertes Set mit nur gültigen Tupeln
    """
    if not hierarchy.parent_value_id:
        return tuples

    result = set()

    for tup in tuples:
        # Tupel als Dict umwandeln für einfache Abfrage
        tc_dict = dict(tup)

        valid = True
        for child_cat, parent_val in hierarchy.parent_value_id.items():
            if child_cat not in tc_dict:
                # Kind-Kategorie nicht im Tupel — OK
                continue

            child_val = tc_dict[child_cat]
            parent_cat = hierarchy.get_parent_category(child_cat)

            if parent_cat is None:
                continue

            if parent_cat in tc_dict:
                parent_val_in_tc = tc_dict[parent_cat]
                if parent_val_in_tc == parent_val:
                    # Eltern aktiv → Kind darf NICHT "-" sein
                    if child_val == "-":
                        valid = False
                        break
                else:
                    # Eltern nicht aktiv → Kind MUSS "-" sein
                    if child_val != "-":
                        valid = False
                        break
            else:
                # Eltern-Kategorie nicht im Tupel (z.B. bei t-wise < n)
                # Kind darf nur "-" sein (konservativ: ausschließen)
                if child_val != "-":
                    valid = False
                    break

        if valid:
            result.add(tup)

    return result


def _is_hierarchy_excluded(
    partial_tc: Dict[str, str],
    cat_a: str,
    cat_b: str,
    hierarchy,
) -> bool:
    """
    REQ-6016: Prueft ob ein 2-Tupel (cat_a, cat_b) durch Hierarchie
    ausgeschlossen ist.

    Args:
        partial_tc: {cat_a: val_a, cat_b: val_b}
        cat_a: Erste Kategorie
        cat_b: Zweite Kategorie
        hierarchy: HierarchyDescriptor

    Returns:
        True wenn Paar durch Hierarchie ausgeschlossen
    """
    if not hierarchy.parent_value_id:
        return False

    val_a = partial_tc.get(cat_a)
    val_b = partial_tc.get(cat_b)

    # Fall 1: cat_a ist Kind, cat_b ist Eltern
    if cat_a in hierarchy.parent_value_id:
        parent_val = hierarchy.parent_value_id[cat_a]
        parent_cat = hierarchy.get_parent_category(cat_a)
        if parent_cat == cat_b:
            if val_b != parent_val and val_a != "-":
                return True
            if val_b == parent_val and val_a == "-":
                return True

    # Fall 2: cat_b ist Kind, cat_a ist Eltern
    if cat_b in hierarchy.parent_value_id:
        parent_val = hierarchy.parent_value_id[cat_b]
        parent_cat = hierarchy.get_parent_category(cat_b)
        if parent_cat == cat_a:
            if val_a != parent_val and val_b != "-":
                return True
            if val_a == parent_val and val_b == "-":
                return True

    return False


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