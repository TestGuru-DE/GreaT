"""IPOG-A Algorithmus fuer Pairwise-Generierung.

Innovative Pairwise Optimal Generation (IPOG-A variant):
- Kategorien nach ID sortieren (deterministisch)
- Erste zwei Kategorien: alle Paare als Starttestfaelle
- Jede weitere Kategorie: bestehende Testfaelle mit erstem Wert initialisieren,
  dann unbedeckte Paare mit minimalen neuen Testfaellen abdecken
- rule_engine-Unterstuetzung: is_combination_valid(), apply_dependency_rules()
- deadline-Parameter fuer Timeout-Checks in Schleifen

Referenz: Cohen et al. "Generating efficient software test configurations
by extending pairwise testing with three-way interactions"
"""
from __future__ import annotations

import time
from itertools import product as itertools_product
from typing import Dict, List, Optional, Set, Tuple
from .budget import checkpoint  # BUG B-03


def _check_deadline(deadline: Optional[float]) -> bool:
    """Returns True if deadline has passed (timeout reached)."""
    if deadline is None:
        return False
    return time.time() > deadline


def generate(
    categories: Dict[str, List[str]],
    rule_engine=None,
    deadline: Optional[float] = None,
) -> List[Dict[str, str]]:
    """IPOG-A Pairwise-Generierung.

    Args:
        categories: Mapping von Kategoriename zu Werteliste.
        rule_engine: Optional RuleEngine-Instanz fuer Constraint-Pruefung.
        deadline: Optional Unix-Timestamp (time.time()). Bei Uberschreitung
            wird die Generierung mit den bisher erzeugten Testfaellen abgebrochen.

    Returns:
        Liste von Testfaellen (Dict[str, str]).
    """
    if not categories or any(len(v) == 0 for v in categories.values()):
        return []

    # Kategorien sortiert (deterministische Reihenfolge)
    keys = sorted(categories.keys())
    n = len(keys)

    if n == 1:
        result = [{keys[0]: v} for v in categories[keys[0]]]
        if rule_engine is not None:
            result = [rule_engine.apply_dependency_rules(tc) for tc in result]
        return result

    # --- Phase 1: Initiale Testfaelle aus den ersten beiden Kategorien ---
    k1, k2 = keys[0], keys[1]
    suite: List[Dict[str, str]] = []
    for v1 in categories[k1]:
        checkpoint()  # BUG B-03: Zeitbudget
        for v2 in categories[k2]:
            checkpoint()  # BUG B-03: Zeitbudget
            tc = {k1: v1, k2: v2}
            if rule_engine is not None:
                if not rule_engine.is_combination_valid(tc):
                    continue
                tc = rule_engine.apply_dependency_rules(tc)
            suite.append(tc)

    if _check_deadline(deadline):
        return suite

    # --- Phase 2: Jede weitere Kategorie hinzufügen ---
    for i in range(2, n):
        checkpoint()  # BUG B-03: Zeitbudget
        if _check_deadline(deadline):
            return suite

        new_cat = keys[i]
        new_values = categories[new_cat]

        # 2a: Bestehende Testfaelle mit erstem Wert der neuen Kategorie initialisieren
        first_val = new_values[0]
        for tc in suite:
            checkpoint()  # BUG B-03: Zeitbudget
            tc[new_cat] = first_val
            if rule_engine is not None:
                tc = rule_engine.apply_dependency_rules(tc)

        # 2b: Unbedeckte Paare zwischen new_cat und allen bisherigen Kategorien
        # abdecken mit IPOG-A: fuer jeden neuen Wert, erstelle minimal neue Testfaelle
        suite = _ipo_g_add_category(
            suite, keys[: i + 1], categories, new_cat, new_values, rule_engine, deadline
        )

    return _deduplicate(suite)


def _ipo_g_add_category(
    suite: List[Dict[str, str]],
    active_cats: List[str],
    categories: Dict[str, List[str]],
    new_cat: str,
    new_values: List[str],
    rule_engine,
    deadline: Optional[float],
) -> List[Dict[str, str]]:
    """IPOG-A: Fuegt neue Kategorie hinzu.

    Fuer jeden Wert der neuen Kategorie (außer dem ersten):
      - Finde unbedeckte Paare (existing_cat, existing_val)
      - Fuer JEDES unbedeckte Paar: erstelle neuen Testfall
    """
    existing_cats = [c for c in active_cats if c != new_cat]

    for new_val in new_values:
        checkpoint()  # BUG B-03: Zeitbudget
        if _check_deadline(deadline):
            return suite

        # Finde unbedeckte (ec, ev) Paare fuer new_cat=new_val
        uncovered = _find_uncovered_pairs(suite, existing_cats, categories, new_cat, new_val)

        for ec, ev in uncovered:
            checkpoint()  # BUG B-03: Zeitbudget
            if _check_deadline(deadline):
                return suite

            # Erstelle neuen Testfall
            new_tc = _create_new_testcase(
                suite, active_cats, categories, ec, ev, new_cat, new_val, rule_engine
            )

            if new_tc is not None:
                suite.append(new_tc)

    return suite


def _create_new_testcase(
    suite: List[Dict[str, str]],
    active_cats: List[str],
    categories: Dict[str, List[str]],
    fixed_cat: str,
    fixed_val: str,
    new_cat: str,
    new_val: str,
    rule_engine,
) -> Optional[Dict[str, str]]:
    """Erstellt neuen Testfall durch Kopie und Anpassung."""
    # Finde existierenden Testfall mit fixed_cat=fixed_val als Vorlage
    template = None
    for tc in suite:
        checkpoint()  # BUG B-03: Zeitbudget
        if tc.get(fixed_cat) == fixed_val:
            template = tc
            break

    if template is None:
        # Kein passender Vorlagen-Testfall; erstelle von Grund auf
        template = {}
        for c in active_cats:
            checkpoint()  # BUG B-03: Zeitbudget
            template[c] = categories[c][0]
        template[fixed_cat] = fixed_val

    # Kopiere und passe an
    new_tc = dict(template)
    new_tc[new_cat] = new_val

    # Fuer alle anderen Kategorien: erster Wert (wenn nicht im Template)
    for c in active_cats:
        checkpoint()  # BUG B-03: Zeitbudget
        if c not in new_tc:
            new_tc[c] = categories[c][0]

    if rule_engine is not None:
        if not rule_engine.is_combination_valid(new_tc):
            new_tc = _find_valid_extension(
                active_cats, categories, fixed_cat, fixed_val, new_cat, new_val, rule_engine
            )
            if new_tc is None:
                return None
        new_tc = rule_engine.apply_dependency_rules(new_tc)

    return new_tc


def _find_uncovered_pairs(
    suite: List[Dict[str, str]],
    existing_cats: List[str],
    categories: Dict[str, List[str]],
    new_cat: str,
    new_val: str,
) -> List[Tuple[str, str]]:
    """Finde (existing_cat, existing_val)-Paare, die mit new_cat=new_val
    noch nicht vorkommen."""
    covered: Set[Tuple[str, str]] = set()
    for tc in suite:
        checkpoint()  # BUG B-03: Zeitbudget
        if tc.get(new_cat) == new_val:
            for ec in existing_cats:
                checkpoint()  # BUG B-03: Zeitbudget
                if ec in tc:
                    covered.add((ec, tc[ec]))

    uncovered: List[Tuple[str, str]] = []
    for ec in existing_cats:
        checkpoint()  # BUG B-03: Zeitbudget
        for ev in categories[ec]:
            checkpoint()  # BUG B-03: Zeitbudget
            if (ec, ev) not in covered:
                uncovered.append((ec, ev))

    return uncovered


def _find_valid_extension(
    active_cats: List[str],
    categories: Dict[str, List[str]],
    fixed_cat: str,
    fixed_val: str,
    new_cat: str,
    new_val: str,
    rule_engine,
) -> Optional[Dict[str, str]]:
    """Versucht eine gueltige Erweiterung fuer einen neuen Testfall."""
    other_cats = [c for c in active_cats if c not in (fixed_cat, new_cat)]

    for combo in itertools_product(*[categories[c] for c in other_cats]):
        checkpoint()  # BUG B-03: Zeitbudget
        tc = {fixed_cat: fixed_val, new_cat: new_val}
        for c, v in zip(other_cats, combo):
            checkpoint()  # BUG B-03: Zeitbudget
            tc[c] = v
        if rule_engine.is_combination_valid(tc):
            return tc

    return None


def _deduplicate(testcases: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Entfernt Duplikate aus Testfall-Liste."""
    seen: Set[Tuple] = set()
    result: List[Dict[str, str]] = []
    for tc in testcases:
        checkpoint()  # BUG B-03: Zeitbudget
        key = tuple(sorted(tc.items()))
        if key not in seen:
            seen.add(key)
            result.append(tc)
    return result