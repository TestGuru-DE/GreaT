"""
REQ-6001: AST-Parser und Validator fuer logische Constraints.

ADR-020: JSON-AST-Format
- Operatoren: eq, ne, in, not_in, and, or, not
- Atomare Vergleiche: {op, category_id, value_id} oder {op, category_id, value_ids}
- Boolean-Operatoren: {op: and|or, args: [...]} oder {op: not, arg: {...}}
- Top-Level: {kind: forbid|implies, condition: {...}, consequence?: {...}}
- Max Tiefe: 5, Max 20 atomare Vergleiche
"""
from __future__ import annotations

from typing import Dict, List, Tuple


# Operatoren, die atomare Vergleiche sind (leaf nodes)
COMPARISON_OPS = {"eq", "ne", "in", "not_in"}

# Operatoren, die boolesche Verknuepfungen sind (internal nodes)
BOOLEAN_OPS = {"and", "or"}

# Unary Operator
UNARY_OPS = {"not"}

ALL_OPS = COMPARISON_OPS | BOOLEAN_OPS | UNARY_OPS

MAX_DEPTH = 5
MAX_LEAF_NODES = 20


def validate_ast(ast: dict) -> Tuple[bool, List[str]]:
    """
    Strukturelle Validierung eines Constraint-AST.

    Args:
        ast: Top-Level Constraint-Struktur nach ADR-020

    Returns:
        (is_valid, errors) – errors ist eine Liste von Fehlerbeschreibungen
    """
    errors: List[str] = []

    # 1. Top-Level Struktur pruefen
    if not isinstance(ast, dict):
        return False, ["AST muss ein JSON-Objekt sein"]

    kind = ast.get("kind")
    if kind not in ("forbid", "implies"):
        errors.append(f"Ungueltiger kind '{kind}'. Muss 'forbid' oder 'implies' sein")

    condition = ast.get("condition")
    if condition is None:
        errors.append("Fehlendes 'condition'-Feld")
    elif not isinstance(condition, dict):
        errors.append("'condition' muss ein JSON-Objekt sein")

    consequence = ast.get("consequence")

    # kind-spezifische Pruefung
    if kind == "forbid" and consequence is not None:
        errors.append("'forbid' Constraints duerfen kein 'consequence'-Feld haben")

    if kind == "implies" and consequence is None:
        errors.append("'implies' Constraints brauchen ein 'consequence'-Feld")

    if consequence is not None and not isinstance(consequence, dict):
        errors.append("'consequence' muss ein JSON-Objekt sein")

    # 2. Ausdruck-Validierung (condition und consequence)
    if isinstance(condition, dict):
        cond_errors = validate_expression(condition, depth=0)
        errors.extend(cond_errors)

    if isinstance(consequence, dict):
        cons_errors = validate_expression(consequence, depth=0)
        errors.extend(cons_errors)

    return len(errors) == 0, errors


def validate_expression(expr: dict, depth: int = 0) -> List[str]:
    """
    Validiert einen einzelnen Ausdruck (condition oder consequence).

    Args:
        expr: Ausdruck-Node
        depth: Aktuelle Verschachtelungstiefe

    Returns:
        Liste von Fehlerbeschreibungen (leer wenn gueltig)
    """
    errors: List[str] = []

    if not isinstance(expr, dict):
        errors.append(f"Node muss ein JSON-Objekt sein (Tiefe {depth})")
        return errors

    op = expr.get("op")
    if op is None:
        errors.append(f"Fehlendes 'op'-Feld in Node (Tiefe {depth})")
        return errors

    if op not in ALL_OPS:
        errors.append(f"Ungueltiger Operator '{op}'. Gueltig: {', '.join(sorted(ALL_OPS))}")
        return errors

    # Tiefe pruefen
    if depth > MAX_DEPTH:
        errors.append(f"Maximale Verschachtelungstiefe {MAX_DEPTH} ueberschritten (aktuell {depth})")
        return errors

    # Operator-spezifische Validierung
    if op in COMPARISON_OPS:
        errors.extend(_validate_comparison(expr, op, depth))
    elif op in BOOLEAN_OPS:
        errors.extend(_validate_boolean(expr, op, depth))
    elif op == "not":
        errors.extend(_validate_unary(expr, depth))

    return errors


def _validate_comparison(expr: dict, op: str, depth: int) -> List[str]:
    """Validiert einen atomaren Vergleich (eq, ne, in, not_in)."""
    errors: List[str] = []

    category_id = expr.get("category_id")
    if category_id is None:
        errors.append(f"Vergleich '{op}' braucht 'category_id'")
    elif not isinstance(category_id, int) or category_id <= 0:
        errors.append(f"'category_id' muss eine positive Integer-Zahl sein (ist {category_id!r})")

    if op in ("eq", "ne"):
        value_id = expr.get("value_id")
        if value_id is None:
            errors.append(f"Vergleich '{op}' braucht 'value_id'")
        elif not isinstance(value_id, int) or value_id <= 0:
            errors.append(f"'value_id' muss eine positive Integer-Zahl sein (ist {value_id!r})")
    elif op in ("in", "not_in"):
        value_ids = expr.get("value_ids")
        if value_ids is None:
            errors.append(f"Vergleich '{op}' braucht 'value_ids' (Liste)")
        elif not isinstance(value_ids, list) or len(value_ids) == 0:
            errors.append(f"'value_ids' muss eine nicht-leere Liste sein")
        else:
            for i, vid in enumerate(value_ids):
                if not isinstance(vid, int) or vid <= 0:
                    errors.append(f"'value_ids[{i}]' muss positive Integer sein (ist {vid!r})")

    return errors


def _validate_boolean(expr: dict, op: str, depth: int) -> List[str]:
    """Validiert einen booleschen Operator (and, or)."""
    errors: List[str] = []

    args = expr.get("args")
    if args is None:
        errors.append(f"Operator '{op}' braucht 'args' (Liste von Ausdruecken)")
        return errors

    if not isinstance(args, list) or len(args) < 2:
        errors.append(f"Operator '{op}' braucht mindestens 2 Argumente in 'args'")
        return errors

    for i, arg in enumerate(args):
        arg_errors = validate_expression(arg, depth + 1)
        errors.extend(arg_errors)

    return errors


def _validate_unary(expr: dict, depth: int) -> List[str]:
    """Validiert den unaren Operator 'not'."""
    errors: List[str] = []

    arg = expr.get("arg")
    if arg is None:
        errors.append("Operator 'not' braucht 'arg' (einzelner Ausdruck)")
        return errors

    return validate_expression(arg, depth + 1)


def count_leaf_nodes(ast: dict) -> int:
    """
    Zaehlt die atomaren Vergleiche (leaf nodes) im AST.

    Args:
        ast: Top-Level Constraint-Struktur oder einzelner Ausdruck

    Returns:
        Anzahl der atomaren Vergleichs-Knoten
    """
    if not isinstance(ast, dict):
        return 0

    op = ast.get("op")

    # Wenn es ein Top-Level Constraint ist (kind/condition/consequence)
    if "kind" in ast:
        count = 0
        if isinstance(ast.get("condition"), dict):
            count += count_leaf_nodes(ast["condition"])
        if isinstance(ast.get("consequence"), dict):
            count += count_leaf_nodes(ast["consequence"])
        return count

    # Leaf node (atomarer Vergleich)
    if op in COMPARISON_OPS:
        return 1

    # Boolean operator
    if op in BOOLEAN_OPS:
        args = ast.get("args", [])
        return sum(count_leaf_nodes(arg) for arg in args if isinstance(arg, dict))

    # Unary operator
    if op == "not":
        arg = ast.get("arg")
        return count_leaf_nodes(arg) if isinstance(arg, dict) else 0

    return 0


def get_depth(ast: dict) -> int:
    """
    Berechnet die maximale Verschachtelungstiefe des AST.

    Args:
        ast: Top-Level Constraint-Struktur oder einzelner Ausdruck

    Returns:
        Maximale Tiefe (0 fuer leaf node)
    """
    if not isinstance(ast, dict):
        return 0

    op = ast.get("op")

    # Top-Level Constraint
    if "kind" in ast:
        depths = []
        if isinstance(ast.get("condition"), dict):
            depths.append(get_depth(ast["condition"]) + 1)
        if isinstance(ast.get("consequence"), dict):
            depths.append(get_depth(ast["consequence"]) + 1)
        return max(depths) if depths else 0

    # Leaf node
    if op in COMPARISON_OPS:
        return 0

    # Boolean operator
    if op in BOOLEAN_OPS:
        args = ast.get("args", [])
        if not args:
            return 0
        return max(get_depth(arg) for arg in args if isinstance(arg, dict)) + 1

    # Unary operator
    if op == "not":
        arg = ast.get("arg")
        return (get_depth(arg) + 1) if isinstance(arg, dict) else 0

    return 0


def expression_depth(expr) -> int:
    """Verschachtelungstiefe wie in validate_expression gezaehlt (Blatt = 0, je and/or/not +1).

    Restbefund 9c: Grundlage fuer das Feld "depth" der Validierung; gueltig ist depth <= MAX_DEPTH.
    """
    if not isinstance(expr, dict):
        return 0
    op = expr.get("op")
    if op in BOOLEAN_OPS:
        args = [a for a in expr.get("args", []) if isinstance(a, dict)]
        return 1 + max((expression_depth(a) for a in args), default=0)
    if op == "not":
        return 1 + expression_depth(expr.get("arg"))
    return 0
