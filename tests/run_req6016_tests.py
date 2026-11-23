"""Test runner for REQ-6016 hierarchy tests."""
import sys, os
# Add src/ to path
SRC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import traceback
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule
from combinatorics import coverage
from combinatorics.hierarchy_constraints import (
    generate_hierarchy_constraints,
    create_hierarchy_rule_engine,
    prepare_hierarchy_categories,
    is_valid_hierarchical_testcase,
    enforce_hierarchy,
    generate_with_hierarchy,
)
from app.models.hierarchy import (
    HierarchyDescriptor,
    HIERARCHY_NOT_APPLICABLE,
    MAX_HIERARCHY_DEPTH,
)

# Test data
CATEGORIES_FLAT = {
    "PaymentMethod": ["CreditCard", "PayPal", "None"],
    "Amount": ["Low", "High"],
}

CATEGORIES_WITH_CHILD = {
    "PaymentMethod": ["CreditCard", "PayPal", "None"],
    "CardType": ["Visa", "MC", "Amex", "-"],
    "Amount": ["Low", "High"],
}

HIERARCHY_2LEVEL = HierarchyDescriptor.from_categories(
    categories=CATEGORIES_WITH_CHILD,
    parent_value_ids={
        "CardType": "CreditCard",
        "Amount": None,
        "PaymentMethod": None,
    },
)

CATEGORIES_3LEVEL = {
    "PaymentMethod": ["CreditCard", "PayPal"],
    "CardType": ["Visa", "MC", "-"],
    "CardFeature": ["Contactless", "Chip", "-"],
}

HIERARCHY_3LEVEL = HierarchyDescriptor.from_categories(
    categories=CATEGORIES_3LEVEL,
    parent_value_ids={
        "PaymentMethod": None,
        "CardType": "CreditCard",
        "CardFeature": "Visa",
    },
)


def test_001_no_child_without_parent():
    result = generate_with_hierarchy("each_choice", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    for tc in result:
        parent_val = tc.get("PaymentMethod")
        child_val = tc.get("CardType")
        if parent_val == "CreditCard":
            assert child_val != "-", f"Child '-' when parent active: {tc}"
        else:
            assert child_val == "-", f"Child '{child_val}' when parent not active: {tc}"

def test_002_all_testcases_valid():
    result = generate_with_hierarchy("pairwise", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    for tc in result:
        assert is_valid_hierarchical_testcase(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD), f"Invalid: {tc}"

def test_003_enforce_sets_na():
    tc = {"PaymentMethod": "PayPal", "CardType": "Visa", "Amount": "Low"}
    result = enforce_hierarchy(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    assert result["CardType"] == "-"
    assert result["PaymentMethod"] == "PayPal"

def test_004_enforce_preserves_active():
    tc = {"PaymentMethod": "CreditCard", "CardType": "Visa", "Amount": "High"}
    result = enforce_hierarchy(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    assert result["CardType"] == "Visa"

def test_005_each_choice_covers_all():
    result = generate_with_hierarchy("each_choice", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    pm_vals = {tc["PaymentMethod"] for tc in result}
    assert "CreditCard" in pm_vals
    assert "PayPal" in pm_vals
    assert "None" in pm_vals
    for tc in result:
        if tc["PaymentMethod"] == "CreditCard":
            assert tc["CardType"] != "-"

def test_006_linear_expansion():
    result = generate_with_hierarchy("linear", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    for tc in result:
        assert is_valid_hierarchical_testcase(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    assert len(result) > 0

def test_007_all_combinations():
    result = generate_with_hierarchy("all_combinations", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    for tc in result:
        assert is_valid_hierarchical_testcase(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    assert len(result) > 0
    for tc in result:
        if tc["PaymentMethod"] in ("PayPal", "None"):
            assert tc["CardType"] == "-"

def test_008_pairwise_coverage():
    result = generate_with_hierarchy("pairwise", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    for tc in result:
        assert is_valid_hierarchical_testcase(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    pairs = {(tc["PaymentMethod"], tc["CardType"]) for tc in result}
    for ct in ["Visa", "MC", "Amex"]:
        assert ("CreditCard", ct) in pairs, f"Missing: CreditCard + {ct}"
    for tc in result:
        if tc["PaymentMethod"] in ("PayPal", "None"):
            assert tc["CardType"] == "-"

def test_009_twise():
    result = generate_with_hierarchy("twise", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD, t=2)
    for tc in result:
        assert is_valid_hierarchical_testcase(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    assert len(result) > 0

def test_010_coverage_excludes_invalid():
    testcases = [
        {"PaymentMethod": "CreditCard", "CardType": "Visa", "Amount": "Low"},
        {"PaymentMethod": "CreditCard", "CardType": "MC", "Amount": "High"},
    ]
    cats = prepare_hierarchy_categories(HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    result = coverage.calculate_coverage(testcases=testcases, categories=cats, t=2, hierarchy=HIERARCHY_2LEVEL)
    assert result.possible > 0
    assert result.covered > 0

def test_011_heatmap_hierarchy():
    testcases = [{"PaymentMethod": "CreditCard", "CardType": "Visa", "Amount": "Low"}]
    cats = prepare_hierarchy_categories(HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    heatmap = coverage.compute_heatmap(
        cat_a="PaymentMethod", cat_b="CardType",
        testcases=testcases, categories=cats, hierarchy=HIERARCHY_2LEVEL,
    )
    cell = heatmap.cells.get(("PayPal", "Visa"))
    assert cell is not None and cell.status == "excluded"
    cell2 = heatmap.cells.get(("CreditCard", "Visa"))
    assert cell2 is not None and cell2.status == "covered"
    cell3 = heatmap.cells.get(("CreditCard", "-"))
    assert cell3 is not None and cell3.status == "excluded"

def test_012_max_depth():
    cats = {"A": ["a1"], "B": ["b1", "-"], "C": ["c1", "-"], "D": ["d1", "-"]}
    try:
        HierarchyDescriptor.from_categories(
            categories=cats,
            parent_value_ids={"A": None, "B": "a1", "C": "b1", "D": "c1"},
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "exceeds max depth" in str(e)

def test_013_flat_project():
    hierarchy = HierarchyDescriptor.from_categories(
        categories=CATEGORIES_FLAT,
        parent_value_ids={"PaymentMethod": None, "Amount": None},
    )
    result = generate_with_hierarchy("each_choice", hierarchy, CATEGORIES_FLAT)
    assert len(result) > 0

def test_014_three_level():
    result = generate_with_hierarchy("pairwise", HIERARCHY_3LEVEL, CATEGORIES_3LEVEL)
    for tc in result:
        assert is_valid_hierarchical_testcase(tc, HIERARCHY_3LEVEL, CATEGORIES_3LEVEL)
    for tc in result:
        if tc["PaymentMethod"] == "PayPal":
            assert tc["CardType"] == "-"
            assert tc["CardFeature"] == "-"
    for tc in result:
        if tc.get("CardType") == "MC":
            assert tc["CardFeature"] == "-"

def test_015_constraint_generation():
    cats = prepare_hierarchy_categories(HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
    rules = generate_hierarchy_constraints(HIERARCHY_2LEVEL, cats)
    assert len(rules) > 0
    dep_rules = [r for r in rules if isinstance(r, DependencyRule)]
    forb_rules = [r for r in rules if isinstance(r, ForbiddenRule)]
    assert len(dep_rules) >= 2
    assert len(forb_rules) >= 1
    has_paypal_dep = any(
        r.if_category == "PaymentMethod" and r.if_value == "PayPal"
        and r.then_category == "CardType" and r.then_value == "-"
        for r in dep_rules
    )
    assert has_paypal_dep
    has_cc_forbidden = any(
        r.if_category == "PaymentMethod" and r.if_value == "CreditCard"
        and r.then_category == "CardType" and r.then_value == "-"
        for r in forb_rules
    )
    assert has_cc_forbidden


# Run all tests
tests = [
    ("TEST-REQ-6016-001", test_001_no_child_without_parent),
    ("TEST-REQ-6016-002", test_002_all_testcases_valid),
    ("TEST-REQ-6016-003", test_003_enforce_sets_na),
    ("TEST-REQ-6016-004", test_004_enforce_preserves_active),
    ("TEST-REQ-6016-005", test_005_each_choice_covers_all),
    ("TEST-REQ-6016-006", test_006_linear_expansion),
    ("TEST-REQ-6016-007", test_007_all_combinations),
    ("TEST-REQ-6016-008", test_008_pairwise_coverage),
    ("TEST-REQ-6016-009", test_009_twise),
    ("TEST-REQ-6016-010", test_010_coverage_excludes_invalid),
    ("TEST-REQ-6016-011", test_011_heatmap_hierarchy),
    ("TEST-REQ-6016-012", test_012_max_depth),
    ("TEST-REQ-6016-013", test_013_flat_project),
    ("TEST-REQ-6016-014", test_014_three_level),
    ("TEST-REQ-6016-015", test_015_constraint_generation),
]

passed = 0
failed = 0
errors = []

for test_id, func in tests:
    try:
        func()
        passed += 1
        print(f"PASS: {test_id}")
    except Exception as e:
        failed += 1
        errors.append(f"FAIL: {test_id}: {e}")
        traceback.print_exc()

print(f"\n=== Results: {passed}/{len(tests)} passed, {failed} failed ===")
if errors:
    for err in errors:
        print(f"  {err}")
    sys.exit(1)
else:
    print("All tests passed!")