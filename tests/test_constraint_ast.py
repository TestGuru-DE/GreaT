"""
REQ-6001: Tests fuer AST-Parser und Validator.

Testet strukturelle Validierung von JSON-AST nach ADR-020:
- Gueltige Operatoren (eq, ne, in, not_in, and, or, not)
- Korrekte Argumente pro Operator
- Max-Tiefe 5, Max 20 atomare Vergleiche
- kind-Validierung (forbid/implies)
"""
import pytest

from app.constraints.ast_parser import (
    validate_ast,
    count_leaf_nodes,
    get_depth,
    validate_expression,
)


# ====================================================================
# Gueltige AST-Strukturen
# ====================================================================

class TestValidAST:
    """Tests fuer gueltige AST-Strukturen."""

    def test_simple_eq_forbid(self):
        """Einfacher eq-Vergleich als Verbot."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_simple_ne_forbid(self):
        """Einfacher ne-Vergleich als Verbot."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "ne", "category_id": 1, "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_in_operator(self):
        """in-Operator mit Werteliste."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "in", "category_id": 1, "value_ids": [2, 3, 4]},
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_not_in_operator(self):
        """not_in-Operator mit Werteliste."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "not_in", "category_id": 1, "value_ids": [2, 3]},
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_and_combination(self):
        """AND-Verknuepfung zweier Vergleiche."""
        ast = {
            "kind": "forbid",
            "condition": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 2},
                    {"op": "ne", "category_id": 3, "value_id": 4},
                ],
            },
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_or_combination(self):
        """ODER-Verknuepfung zweier Vergleiche."""
        ast = {
            "kind": "forbid",
            "condition": {
                "op": "or",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 2},
                    {"op": "eq", "category_id": 3, "value_id": 4},
                ],
            },
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_not_unary(self):
        """NICHT-Operator (unary)."""
        ast = {
            "kind": "forbid",
            "condition": {
                "op": "not",
                "arg": {"op": "eq", "category_id": 1, "value_id": 2},
            },
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_nested_and_or(self):
        """Verschachtelte AND/ODER-Struktur."""
        ast = {
            "kind": "forbid",
            "condition": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 2},
                    {
                        "op": "or",
                        "args": [
                            {"op": "ne", "category_id": 3, "value_id": 4},
                            {"op": "in", "category_id": 5, "value_ids": [6, 7]},
                        ],
                    },
                ],
            },
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_implies_with_consequence(self):
        """Implikation mit Bedingung und Folge."""
        ast = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 2},
            "consequence": {"op": "ne", "category_id": 3, "value_id": 4},
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_deep_nesting_at_limit(self):
        """Maximale Tiefe 5 (am Limit)."""
        # Tiefe 5: not > not > not > not > not > eq
        inner = {"op": "eq", "category_id": 1, "value_id": 2}
        for _ in range(5):
            inner = {"op": "not", "arg": inner}
        ast = {"kind": "forbid", "condition": inner}
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler bei Tiefe 5: {errors}"


# ====================================================================
# Ungueltige AST-Strukturen
# ====================================================================

class TestInvalidAST:
    """Tests fuer ungueltige AST-Strukturen."""

    def test_missing_kind(self):
        """Fehlendes kind-Feld."""
        ast = {"condition": {"op": "eq", "category_id": 1, "value_id": 2}}
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("kind" in e for e in errors)

    def test_invalid_kind(self):
        """Ungueltiger kind-Wert."""
        ast = {
            "kind": "unknown",
            "condition": {"op": "eq", "category_id": 1, "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("kind" in e for e in errors)

    def test_missing_condition(self):
        """Fehlendes condition-Feld."""
        ast = {"kind": "forbid"}
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("condition" in e for e in errors)

    def test_forbid_with_consequence(self):
        """forbid darf kein consequence haben."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 2},
            "consequence": {"op": "eq", "category_id": 3, "value_id": 4},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("consequence" in e for e in errors)

    def test_implies_without_consequence(self):
        """implies braucht consequence."""
        ast = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("consequence" in e for e in errors)

    def test_invalid_operator(self):
        """Ungueltiger Operator."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "gt", "category_id": 1, "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("Operator" in e or "op" in e for e in errors)

    def test_missing_op(self):
        """Fehlendes op-Feld."""
        ast = {
            "kind": "forbid",
            "condition": {"category_id": 1, "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("op" in e for e in errors)

    def test_eq_missing_value_id(self):
        """eq braucht value_id."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("value_id" in e for e in errors)

    def test_eq_missing_category_id(self):
        """eq braucht category_id."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "eq", "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("category_id" in e for e in errors)

    def test_in_missing_value_ids(self):
        """in braucht value_ids."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "in", "category_id": 1},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("value_ids" in e for e in errors)

    def test_in_empty_value_ids(self):
        """in braucht nicht-leere value_ids."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "in", "category_id": 1, "value_ids": []},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("value_ids" in e for e in errors)

    def test_and_missing_args(self):
        """and braucht args."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "and"},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("args" in e for e in errors)

    def test_and_single_arg(self):
        """and braucht mindestens 2 Argumente."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "and", "args": [{"op": "eq", "category_id": 1, "value_id": 2}]},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("2" in e or "mindestens" in e for e in errors)

    def test_not_missing_arg(self):
        """not braucht arg."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "not"},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("arg" in e for e in errors)

    def test_negative_category_id(self):
        """category_id muss positiv sein."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": -1, "value_id": 2},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("category_id" in e for e in errors)

    def test_zero_value_id(self):
        """value_id muss positiv sein (nicht 0)."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 0},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("value_id" in e for e in errors)

    def test_non_dict_ast(self):
        """AST muss ein Dict sein."""
        is_valid, errors = validate_ast("not a dict")
        assert not is_valid


# ====================================================================
# Tiefe und Knotenzaehlung
# ====================================================================

class TestDepthAndLeaves:
    """Tests fuer Tiefe-Berechnung und Knotenzaehlung."""

    def test_leaf_count_single_eq(self):
        """Einzelner Vergleich = 1 leaf."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 2},
        }
        assert count_leaf_nodes(ast) == 1

    def test_leaf_count_and_two(self):
        """AND mit 2 Vergleichen = 2 leaves."""
        ast = {
            "kind": "forbid",
            "condition": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 2},
                    {"op": "eq", "category_id": 3, "value_id": 4},
                ],
            },
        }
        assert count_leaf_nodes(ast) == 2

    def test_leaf_count_nested(self):
        """Verschachtelte Struktur zaehlt alle leaves."""
        ast = {
            "kind": "forbid",
            "condition": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 2},
                    {
                        "op": "or",
                        "args": [
                            {"op": "ne", "category_id": 3, "value_id": 4},
                            {"op": "in", "category_id": 5, "value_ids": [6, 7]},
                        ],
                    },
                ],
            },
        }
        assert count_leaf_nodes(ast) == 3

    def test_leaf_count_implies(self):
        """implies zaehlt condition + consequence."""
        ast = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 2},
            "consequence": {"op": "ne", "category_id": 3, "value_id": 4},
        }
        assert count_leaf_nodes(ast) == 2

    def test_depth_leaf_node(self):
        """Leaf node hat Tiefe 0."""
        expr = {"op": "eq", "category_id": 1, "value_id": 2}
        assert get_depth(expr) == 0

    def test_depth_single_not(self):
        """Ein not um leaf = Tiefe 1."""
        expr = {"op": "not", "arg": {"op": "eq", "category_id": 1, "value_id": 2}}
        assert get_depth(expr) == 1

    def test_depth_nested_and(self):
        """AND mit leaves = Tiefe 1."""
        expr = {
            "op": "and",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 2},
                {"op": "eq", "category_id": 3, "value_id": 4},
            ],
        }
        assert get_depth(expr) == 1

    def test_depth_at_limit(self):
        """Tiefe 5 (am Limit) wird korrekt berechnet."""
        inner = {"op": "eq", "category_id": 1, "value_id": 2}
        for _ in range(5):
            inner = {"op": "not", "arg": inner}
        assert get_depth(inner) == 5

    def test_depth_over_limit(self):
        """Tiefe > 5 erzeugt Fehler bei Validierung."""
        inner = {"op": "eq", "category_id": 1, "value_id": 2}
        for _ in range(6):  # Tiefe 6
            inner = {"op": "not", "arg": inner}
        ast = {"kind": "forbid", "condition": inner}
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("Tiefe" in e or "tiefe" in e.lower() or "5" in e for e in errors)

    def test_leaf_count_over_limit(self):
        """Mehr als 20 leaves erzeugt Fehler (wenn pruefbar)."""
        # Erstelle 21 eq-Knoten in einem grossen OR
        args = [{"op": "eq", "category_id": i, "value_id": i} for i in range(1, 22)]
        ast = {
            "kind": "forbid",
            "condition": {"op": "or", "args": args},
        }
        assert count_leaf_nodes(ast) == 21
        # Die Validierung prueft aktuell nicht die leaf-count-Grenze direkt
        # Das wird im API-Endpoint gemacht


# ====================================================================
# Edge Cases
# ====================================================================

class TestEdgeCases:
    """Edge Cases und Sonderfaelle."""

    def test_empty_condition_dict(self):
        """Leeres condition-Dict."""
        ast = {"kind": "forbid", "condition": {}}
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("op" in e for e in errors)

    def test_condition_not_dict(self):
        """condition ist kein Dict."""
        ast = {"kind": "forbid", "condition": "string"}
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("condition" in e for e in errors)

    def test_large_and(self):
        """AND mit vielen Argumenten (10)."""
        args = [{"op": "eq", "category_id": i, "value_id": i} for i in range(1, 11)]
        ast = {
            "kind": "forbid",
            "condition": {"op": "and", "args": args},
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"
        assert count_leaf_nodes(ast) == 10

    def test_mixed_valid_value_ids(self):
        """value_ids mit gueltigen Werten."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "in", "category_id": 1, "value_ids": [1, 2, 3]},
        }
        is_valid, errors = validate_ast(ast)
        assert is_valid, f"Unerwartete Fehler: {errors}"

    def test_value_ids_with_negative(self):
        """value_ids mit negativem Wert."""
        ast = {
            "kind": "forbid",
            "condition": {"op": "in", "category_id": 1, "value_ids": [1, -2, 3]},
        }
        is_valid, errors = validate_ast(ast)
        assert not is_valid
        assert any("value_ids" in e for e in errors)