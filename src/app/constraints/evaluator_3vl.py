"""
REQ-6001: Dreiwertige Logik (3VL) Evaluator fuer Constraints.

Implementiert die Spezifikation aus documentation/3vl-spec-req6001.md.
- True (T): Bedingung ist definitiv erfuellt
- False (F): Bedingung ist definitiv NICHT erfuellt
- None (U): Unbekannt (Kategorie nicht gesetzt im Teiltestfall)

AK-6: Ein partieller Testfall wird NUR verworfen, wenn er einen Constraint
sicher verletzt. Im Zweifel (unbekannt) wird er vorlaeufig behalten.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .ast_parser import COMPARISON_OPS, BOOLEAN_OPS, UNARY_OPS

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