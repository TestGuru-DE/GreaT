"""
REQ-6001: Dreiwertige Logik (3VL) Evaluator fuer Constraints.

Implementiert die Spezifikation aus documentation/3vl-spec-req6001.md.
- True (T): Bedingung ist definitiv erfuellt
- False (F): Bedingung ist definitiv NICHT erfuellt
- None (U): Unbekannt (Kategorie nicht gesetzt im Teiltestfall)

AK-6: Ein partieller Testfall wird NUR verworfen, wenn er einen Constraint
sicher verletzt. Im Zweifel (unbekannt) wird er vorlaeufig behalten.

AK-8: Widerspruchspruefung beim Speichern.
"""
from __future__ import annotations

import itertools
import logging
import time
from typing import Dict, List, Optional, Tuple

from .ast_parser import COMPARISON_OPS, BOOLEAN_OPS, UNARY_OPS

log = logging.getLogger("great.constraints.evaluator")

# Typ-Alias: 3VL-Ergebnis
ThreeVal = Optional[bool]  # True, False oder None


def evaluate_3vl(
    ast: dict,
    assignment: Dict[int, int],
) -> ThreeVal:
    """
    Evaluiert einen Constraint-Ausdruck mit dreiwertiger Logik.

    Args:
        ast: JSON-AST-Node (condition oder consequence)
        assignment: {category_id: value_id} – aktuelle Wertzuordnung
                     None wenn Kategorie nicht gesetzt

    Returns:
        True  – Bedingung ist sicher erfuellt
        False – Bedingung ist sicher NICHT erfuellt
        None  – Unbekannt (partielle Testfall, Kategorie noch nicht gesetzt)
    """
    if not isinstance(ast, dict):
        return None

    op = ast.get("op")

    # Top-Level Constraint (mit kind/condition/consequence)
    if "kind" in ast:
        return _evaluate_constraint(ast, assignment)

    # Atomare Operatoren
    if op in COMPARISON_OPS:
        return _evaluate_comparison(op, ast, assignment)

    # Boolesche Operatoren
    if op in BOOLEAN_OPS:
        return _evaluate_boolean(op, ast, assignment)

    # Unarer Operator
    if op in UNARY_OPS:
        return _evaluate_unary(ast, assignment)

    return None


def _evaluate_constraint(
    ast: dict,
    assignment: Dict[int, int],
) -> ThreeVal:
    """
    Evaluiert ein komplettes Constraint (forbid oder implies).

    Returns:
        True  – Constraint ist NICHT verletzt (Testfall behalten)
        False – Constraint ist verletzt (Testfall verwerfen)
    """
    kind = ast.get("kind", "forbid")
    condition = ast.get("condition")
    consequence = ast.get("consequence")

    if condition is None:
        return True  # Kein condition -> immer gueltig

    cond_result = evaluate_3vl(condition, assignment)

    if kind == "forbid":
        # NICHT(condition): verwerfen NUR wenn condition=True
        # AK-6: "nur werfen, wenn sicher verletzt"
        if cond_result is True:
            return False  # Verletzt
        return True  # Nicht verletzt oder unbekannt -> behalten

    if kind == "implies":
        # WENN(condition) DANN(consequence)
        # Verwerfen NUR wenn condition=True AND consequence=False
        if cond_result is False:
            return True  # Antezedens nicht erfuellt -> Regel irrelevant
        if cond_result is None:
            return True  # Unbekannt -> behalten (AK-6)
        # cond_result is True -> consequence pruefen
        if consequence is None:
            return True  # Keine consequence -> implizit erfuellt
        cons_result = evaluate_3vl(consequence, assignment)
        if cons_result is False:
            return False  # Condition erfuellt, aber consequence nicht -> verletzt
        return True  # Consequence erfuellt oder unbekannt -> behalten

    return True


def _evaluate_comparison(
    op: str,
    ast: dict,
    assignment: Dict[int, int],
) -> ThreeVal:
    """
    Evaluiert einen atomaren Vergleich (eq, ne, in, not_in) mit 3VL.
    """
    category_id = ast.get("category_id")
    if category_id is None:
        return None

    # Wert aus assignment lesen (None wenn Kategorie nicht gesetzt)
    assigned_value = assignment.get(category_id)

    if op == "eq":
        value_id = ast.get("value_id")
        if assigned_value is None:
            return None  # Unbekannt
        return assigned_value == value_id

    if op == "ne":
        value_id = ast.get("value_id")
        if assigned_value is None:
            return None  # Unbekannt
        return assigned_value != value_id

    if op == "in":
        value_ids = ast.get("value_ids", [])
        if assigned_value is None:
            return None  # Unbekannt
        return assigned_value in value_ids

    if op == "not_in":
        value_ids = ast.get("value_ids", [])
        if assigned_value is None:
            return None  # Unbekannt
        return assigned_value not in value_ids

    return None


def _evaluate_boolean(
    op: str,
    ast: dict,
    assignment: Dict[int, int],
) -> ThreeVal:
    """
    Evaluiert boolesche Operatoren (and, or) mit 3VL und Kurzschluss.
    """
    args = ast.get("args", [])
    if not args:
        return None

    if op == "and":
        # Multi-Arg AND: F wenn IRGENDEIN Argument F; T wenn ALLE T; sonst U
        for arg in args:
            result = evaluate_3vl(arg, assignment)
            if result is False:
                return False  # Kurzschluss: eins falsch -> ganzes AND falsch
        # Kein False gefunden -> pruefe ob alle True
        for arg in args:
            result = evaluate_3vl(arg, assignment)
            if result is None:
                return None  # Mindestens eins unbekannt
        return True  # Alle True

    if op == "or":
        # Multi-Arg OR: T wenn IRGENDEIN Argument T; F wenn ALLE F; sonst U
        for arg in args:
            result = evaluate_3vl(arg, assignment)
            if result is True:
                return True  # Kurzschluss: eins wahr -> ganzes OR wahr
        # Kein True gefunden -> pruefe ob alle False
        for arg in args:
            result = evaluate_3vl(arg, assignment)
            if result is None:
                return None  # Mindestens eins unbekannt
        return False  # Alle False

    return None


def _evaluate_unary(
    ast: dict,
    assignment: Dict[int, int],
) -> ThreeVal:
    """
    Evaluiert den unaren Operator 'not' mit 3VL.
    """
    arg = ast.get("arg")
    if arg is None:
        return None

    result = evaluate_3vl(arg, assignment)
    if result is None:
        return None  # not(None) = None
    return not result


# ---------------------------------------------------------------------------
# Hoherer-Level: Constraint-Pruefung fuer Regel-Engine
# ---------------------------------------------------------------------------


def check_constraint(
    constraint: dict,
    assignment: Dict[int, int],
) -> bool:
    """
    Prueft ob ein Constraint von einem (partiellen) Testfall verletzt wird.

    Args:
        constraint: Komplettes Constraint-Objekt (mit kind, condition, consequence)
        assignment: {category_id: value_id}

    Returns:
        True  – Constraint NICHT verletzt (Testfall behalten)
        False – Constraint verletzt (Testfall verwerfen)
    """
    return evaluate_3vl(constraint, assignment) is not False


def check_all_constraints(
    constraints: List[dict],
    assignment: Dict[int, int],
) -> bool:
    """
    Prueft alle Constraints gegen einen (partiellen) Testfall.

    Args:
        constraints: Liste von Constraint-Objekten
        assignment: {category_id: value_id}

    Returns:
        True  – Keine Constraint verletzt (Testfall behalten)
        False – Mindestens eine Constraint verletzt (Testfall verwerfen)
    """
    for constraint in constraints:
        if not check_constraint(constraint, assignment):
            return False
    return True


# ---------------------------------------------------------------------------
# REQ-6001 AK-8: Widerspruchspruefung beim Speichern
# ---------------------------------------------------------------------------

# Maximale Anzahl Kombinationen fuer vollstaendige Pruefung
_MAX_FULL_CHECK = 100
# Timeout fuer grossere Modelle (Sekunden)
_CHECK_TIMEOUT = 30


def check_unsatisfiable(
    categories: Dict[int, dict],
    new_constraint: dict,
    existing_constraints: List[dict],
) -> Tuple[bool, List[str]]:
    """
    REQ-6001 AK-8: Prueft, ob das Hinzufuegen eines neuen Constraints
    das Modell unerfuellbar macht oder Werte vollstaendig unerreichbar.

    Args:
        categories: {category_id: {"name": str, "values": {value_id: value_name}}}
        new_constraint: Neues Constraint-AST (mit kind, condition, consequence)
        existing_constraints: Liste bereits bestehender Constraint-ASTs

    Returns:
        (is_unsatisfiable, warnings)
        - is_unsatisfiable: True wenn KEIN gueltiger Testfall mehr moeglich
        - warnings: Liste von Warnstrings (leer wenn alles OK)
    """
    if not categories:
        return False, []

    # Alle Constraints zusammen (bestehend + neu)
    all_constraints = list(existing_constraints) + [new_constraint]

    # Kategorien sortieren fuer deterministische Iteration
    cat_ids = sorted(categories.keys())

    # Werteliste pro Kategorie
    cat_values: List[List[int]] = []
    for cid in cat_ids:
        cat_info = categories[cid]
        values = cat_info.get("values", {})
        if not values:
            # Kategorie ohne Werte -> Modell ist bereits leer
            return False, []
        cat_values.append(sorted(values.keys()))

    total_combinations = 1
    for vals in cat_values:
        total_combinations *= len(vals)

    # Fuer grossere Modelle: Stichprobe + Timeout
    use_sampling = total_combinations > _MAX_FULL_CHECK

    if use_sampling:
        return _check_with_sampling(
            categories, cat_ids, cat_values, all_constraints, total_combinations
        )

    # Vollstaendige Pruefung fuer kleine Modelle
    return _check_full(categories, cat_ids, cat_values, all_constraints)


def _check_full(
    categories: Dict[int, dict],
    cat_ids: List[int],
    cat_values: List[List[int]],
    all_constraints: List[dict],
) -> Tuple[bool, List[str]]:
    """Vollstaendige Pruefung aller Kombinationen.

    Warnung nur wenn:
    - Das Modell komplett unerfuellbar ist (KEIN gueltiger Testfall)
    - Eine Kategorie komplett unerreichbar wird (ALLE Werte einer Kategorie blockiert)

    Einzelne unerreichbare Werte werden NICHT gewarnt (zu laut).
    """
    warnings: List[str] = []

    # Track welche Werte in mindestens einem gueltigen Testfall vorkommen
    reachable_values: Dict[int, set] = {cid: set() for cid in cat_ids}
    valid_count = 0

    for combo in itertools.product(*cat_values):
        assignment = dict(zip(cat_ids, combo))

        if check_all_constraints(all_constraints, assignment):
            valid_count += 1
            for cid, vid in zip(cat_ids, combo):
                reachable_values[cid].add(vid)

    if valid_count == 0:
        # Modell komplett unerfuellbar – alle Kategorien sind betroffen
        warnings.append(
            "Dieses Constraint macht das Modell unerfuellbar: "
            "Keine Wertekombination erfuellt alle Regeln."
        )
        # Liste der betroffenen Kategorien/Werte
        for cid in cat_ids:
            cat_info = categories[cid]
            cat_name = cat_info["name"]
            all_vids = sorted(cat_info["values"].keys())
            unreachable_names = [cat_info["values"][vid] for vid in all_vids]
            warnings.append(
                f"Alle Werte in Kategorie '{cat_name}' sind unerreichbar: "
                + ", ".join(unreachable_names)
            )
        return True, warnings

    # Pruefen ob KATEGORIEN komplett unerreichbar wurden (alle Werte blockiert)
    for cid in cat_ids:
        cat_info = categories[cid]
        all_vids = set(cat_info["values"].keys())
        unreachable = all_vids - reachable_values[cid]

        if unreachable == all_vids:
            # ALLE Werte dieser Kategorie sind blockiert -> Kategorie unerreichbar
            cat_name = cat_info["name"]
            unreachable_names = [
                cat_info["values"][vid] for vid in sorted(unreachable)
            ]
            warnings.append(
                f"Alle Werte in Kategorie '{cat_name}' sind unerreichbar: "
                + ", ".join(unreachable_names)
            )
            return True, warnings

        # Einzelne unerreichbare Werte: keine Warnung (zu laut)
        # Der Nutzer kann das im Constraint-Editor selbst sehen

    return False, warnings


def _check_with_sampling(
    categories: Dict[int, dict],
    cat_ids: List[int],
    cat_values: List[List[int]],
    all_constraints: List[dict],
    total_combinations: int,
) -> Tuple[bool, List[str]]:
    """Stichproben-Pruefung fuer grossere Modelle (>100 Kombinationen).

    Nimmt eine Stichprobe von max 1000 Kombinationen und prueft diese.
    Warnung nur wenn Kategorie komplett unerreichbar oder Modell unerfuellbar.
    """
    warnings: List[str] = []

    # Stichprobengroesse (max 1000, mindestens 100)
    sample_size = min(max(100, total_combinations // 10), 1000)

    # BUG K-01: Echte Zufallsstichprobe (fester Seed, deterministisch) statt Aufzaehlung
    # des gesamten Kombinationsraums. Vorher wurde itertools.product komplett
    # durchlaufen (z. B. 10^12 bei 12 x 10) und der Server blockierte dauerhaft.
    import random
    rng = random.Random(6001)

    start_time = time.monotonic()
    reachable_values: Dict[int, set] = {cid: set() for cid in cat_ids}
    valid_count = 0
    checked = 0

    for _ in range(sample_size):
        elapsed = time.monotonic() - start_time
        if elapsed > _CHECK_TIMEOUT:
            warnings.append(
                f"Widerspruchspruefung abgebrochen (Timeout nach {int(elapsed)}s). "
                f"Geprueft: {checked} von {total_combinations} Kombinationen (Stichprobe)."
            )
            break

        combo = tuple(rng.choice(values) for values in cat_values)
        assignment = dict(zip(cat_ids, combo))
        if check_all_constraints(all_constraints, assignment):
            valid_count += 1
            for cid, vid in zip(cat_ids, combo):
                reachable_values[cid].add(vid)
        checked += 1

    if valid_count == 0 and checked < total_combinations:
        # Keine gueltige Kombination in Stichprobe -> Warnung mit Hinweis
        warnings.append(
            f"Keine gueltige Kombination in Stichprobe ({checked} von "
            f"{total_combinations} Kombinationen geprueft). "
            "Das Modell koennte unerfuellbar sein."
        )
        return True, warnings

    if valid_count == 0:
        warnings.append(
            "Dieses Constraint macht das Modell wahrscheinlich unerfuellbar "
            "(Stichprobe: keine gueltige Kombination gefunden)."
        )
        return True, warnings

    # Kategorien komplett unerreichbar? (nur wenn in Stichprobe sichtbar)
    for cid in cat_ids:
        cat_info = categories[cid]
        all_vids = set(cat_info["values"].keys())
        unreachable = all_vids - reachable_values[cid]

        if unreachable == all_vids:
            cat_name = cat_info["name"]
            unreachable_names = [
                cat_info["values"][vid] for vid in sorted(unreachable)
            ]
            warnings.append(
                f"Alle Werte in Kategorie '{cat_name}' sind in der Stichprobe "
                "nicht erreichbar gewesen: " + ", ".join(unreachable_names)
            )
            return True, warnings

    return False, warnings