"""
REQ-6016: Hierarchische Klassen — Implizite Constraints

Generiert implizite Regeln aus der Hierarchie-Struktur:
- Wenn Eltern-Wert NICHT gewaehlt → Kind-Kategorie = "-" (nicht anwendbar)
  (implementiert als DependencyRule, damit IPOG/EachChoice/Linear es korrekt handhaben)
- Wenn Eltern-Wert gewaehlt → Kind-Kategorie darf "-" NICHT sein
  (implementiert als ForbiddenRule)

Diese Regeln werden in die RuleEngine integriert, sodass alle
Kombinatorik-Strategien (Each Choice, Linear, All, Pairwise, T-Wise)
automatisch Hierarchie-Constraints beachten.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from core.rules.rule_engine import ForbiddenRule, DependencyRule, RuleEngine
from app.models.hierarchy import (
    HierarchyDescriptor,
    HIERARCHY_NOT_APPLICABLE,
    MAX_HIERARCHY_DEPTH,
)


# ---------------------------------------------------------------------------
# Constraint Generation
# ---------------------------------------------------------------------------


def generate_hierarchy_constraints(
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
) -> List:
    """
    Generiert implizite Regeln aus der Hierarchie-Struktur.

    Fuer jedes Kind-Kategorie C mit Eltern-Wert P (in Eltern-Kategorie PC):

    1. DependencyRules: Fuer jeden Eltern-Wert V != P:
       WENN PC=V DANN C="-"
       (Wenn Eltern-Wert nicht aktiv, Kind wird automatisch auf "-" gesetzt)

    2. ForbiddenRule: PC=P AND C="-"
       (Wenn Eltern-Wert aktiv, Kind darf nicht "-" sein)

    Die DependencyRules sind entscheidend: IPOG initialisiert neue Kategorien
    mit dem ersten Wert. Wenn "-" der erste Wert ist, setzen die DependencyRules
    das Kind korrekterweise auf "-" fuer nicht-aktive Eltern.

    Args:
        hierarchy: HierarchyDescriptor mit parent_value_id Mapping
        categories: {category_name: [value1, value2, ...]}

    Returns:
        Liste von Rule-Instanzen (DependencyRule + ForbiddenRule)
    """
    rules: List = []

    for child_cat, parent_val in hierarchy.parent_value_id.items():
        parent_cat = hierarchy.get_parent_category(child_cat)
        if parent_cat is None:
            continue

        parent_values = categories.get(parent_cat, [])

        # Rule Type 1: DependencyRules fuer nicht-aktivierende Eltern-Werte
        # Fuer jeden Eltern-Wert V != P: WENN PC=V DANN C="-"
        for parent_v in parent_values:
            if parent_v == parent_val:
                continue  # Aktivierender Wert — hier gilt Regel 2
            rules.append(
                DependencyRule(
                    if_category=parent_cat,
                    if_value=parent_v,
                    then_category=child_cat,
                    then_value=HIERARCHY_NOT_APPLICABLE,
                )
            )

        # Rule Type 2: ForbiddenRule fuer aktivierenden Eltern-Wert + "-"
        # VERBOTEN: parent=P AND child="-"
        rules.append(
            ForbiddenRule(
                if_category=parent_cat,
                if_value=parent_val,
                then_category=child_cat,
                then_value=HIERARCHY_NOT_APPLICABLE,
            )
        )

    return rules


# ---------------------------------------------------------------------------
# RuleEngine Integration
# ---------------------------------------------------------------------------


def create_hierarchy_rule_engine(
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
    additional_rules: Optional[List] = None,
) -> RuleEngine:
    """
    Erzeugt eine RuleEngine mit Hierarchie-Constraints und optionalen
    benutzerdefinierten Regeln.

    REQ-6016: Kind-Kategorien werden so umgeordnet, dass "-" (N/A)
    den letzten Wert einnimmt. Dies stellt sicher, dass IPOG und andere
    Strategien, die mit dem ersten Wert initialisieren, keinen N/A-Wert
    fur aktive Eltern-Werte waehlen.

    Args:
        hierarchy: HierarchyDescriptor
        categories: Kategorien-Wertesets (wird kopiert und modifiziert)
        additional_rules: Zusaetzliche Regeln (ForbiddenRule, DependencyRule, etc.)

    Returns:
        RuleEngine-Instanz mit Hierarchie-Constraints
    """
    reordered_categories = _reorder_for_hierarchy(hierarchy, categories)
    hierarchy_rules = generate_hierarchy_constraints(hierarchy, reordered_categories)

    all_rules = list(additional_rules or [])
    all_rules.extend(hierarchy_rules)

    return RuleEngine(all_rules)


def prepare_hierarchy_categories(
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """
    Gibt Kategorien zurueck, die fuer Hierarchie-Generierung vorbereitet sind:
    - Kind-Kategorien haben "-" als letzten Wert
    - "-" ist in allen Kind-Kategorien enthalten
    - Kategorien sind nach Hierarchie-Tiefe sortiert (Eltern vor Kindern)

    Args:
        hierarchy: HierarchyDescriptor
        categories: Originale Kategorien

    Returns:
        Neue OrderedDict-artige Dict mit angepassten Wertelisten und
        korrekter Reihenfolge (Eltern vor Kindern)
    """
    return _reorder_for_hierarchy(hierarchy, categories)


def get_hierarchy_sorted_categories(
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """
    Gibt Kategorien in Hierarchie-Reihenfolge zurueck (Eltern vor Kindern).

    Dies ist entscheidend fuer IPOG: wenn Eltern-Kategorien zuerst verarbeitet
    werden, koennen DependencyRules korrekt angewendet werden, wenn Kind-
    Kategorien hinzugefuegt werden.

    Args:
        hierarchy: HierarchyDescriptor
        categories: Originale Kategorien

    Returns:
        Dict mit Kategorien in Hierarchie-Reihenfolge
    """
    result = _reorder_for_hierarchy(hierarchy, categories)

    # Sort by depth: root categories (depth=0) first, then children
    sorted_cats = {}
    for depth in range(MAX_HIERARCHY_DEPTH + 1):
        for cat_name, cat_depth in sorted(hierarchy.depth_map.items()):
            if cat_depth == depth and cat_name in result:
                sorted_cats[cat_name] = result[cat_name]
        # Add any categories not in depth_map (flat categories)
        if depth == 0:
            for cat_name in result:
                if cat_name not in hierarchy.depth_map and cat_name not in sorted_cats:
                    sorted_cats[cat_name] = result[cat_name]

    return sorted_cats


def _reorder_for_hierarchy(
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """Intern: Reorder categories for hierarchy generation."""
    result = {k: list(v) for k, v in categories.items()}

    for child_cat in hierarchy.get_all_child_categories():
        if child_cat in result:
            values = result[child_cat]
            # Ensure N/A is present
            if HIERARCHY_NOT_APPLICABLE not in values:
                values.append(HIERARCHY_NOT_APPLICABLE)
            # Move N/A to the end
            other_values = [v for v in values if v != HIERARCHY_NOT_APPLICABLE]
            result[child_cat] = other_values + [HIERARCHY_NOT_APPLICABLE]

    return result


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------


def is_valid_hierarchical_testcase(
    tc: Dict[str, str],
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
) -> bool:
    """
    Prueft ob ein Testfall alle Hierarchie-Constraints einhaelt.

    Args:
        tc: Testfall als {category_name: value_name}
        hierarchy: HierarchyDescriptor
        categories: Kategorien-Wertesets

    Returns:
        True wenn Testfall gueltig, False sonst
    """
    for child_cat, parent_val in hierarchy.parent_value_id.items():
        parent_cat = hierarchy.get_parent_category(child_cat)
        if parent_cat is None:
            continue

        parent_value_in_tc = tc.get(parent_cat)
        child_value_in_tc = tc.get(child_cat)

        if parent_value_in_tc == parent_val:
            # Eltern aktiv → Kind darf NICHT "-" sein
            if child_value_in_tc == HIERARCHY_NOT_APPLICABLE:
                return False
        # Wenn Eltern nicht aktiv: Kind MUSS "-" sein
        # (wird durch DependencyRule automatisch gesetzt)
        elif child_value_in_tc != HIERARCHY_NOT_APPLICABLE:
            return False

    return True


def enforce_hierarchy(
    tc: Dict[str, str],
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
) -> Dict[str, str]:
    """
    Erzwingt Hierarchie-Constraints in einem Testfall durch
    Setzen von "-" bei nicht-aktivierten Kind-Kategorien und
    Ersetzen von "-" durch gueltigen Wert bei aktivierten Eltern.

    Args:
        tc: Testfall (wird kopiert und modifiziert)
        hierarchy: HierarchyDescriptor
        categories: Kategorien-Wertesets

    Returns:
        Modifizierter Testfall mit korrekten Hierarchie-Werten
    """
    result = dict(tc)

    for child_cat, parent_val in hierarchy.parent_value_id.items():
        parent_cat = hierarchy.get_parent_category(child_cat)
        if parent_cat is None:
            continue

        parent_value = result.get(parent_cat)

        if parent_value != parent_val:
            # Eltern nicht aktiv -> Kind auf "-" setzen
            result[child_cat] = HIERARCHY_NOT_APPLICABLE
        elif result.get(child_cat) == HIERARCHY_NOT_APPLICABLE:
            # Eltern aktiv, aber Kind ist "-" -> ersetze durch ersten gueltigen Wert
            child_values = categories.get(child_cat, [])
            valid_values = [v for v in child_values if v != HIERARCHY_NOT_APPLICABLE]
            if valid_values:
                result[child_cat] = valid_values[0]

    return result


# ---------------------------------------------------------------------------
# Hierarchy-aware Generation Wrapper
# ---------------------------------------------------------------------------


def generate_with_hierarchy(
    strategy: str,
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
    additional_rules: Optional[List] = None,
    **kwargs,
) -> List[Dict[str, str]]:
    """
    Generiert Testfaelle mit Hierarchie-Unterstuetzung fuer alle Strategien.

    Löst das Problem, dass IPOG Kategorien alphabetisch sortiert und damit
    die Hierarchie-Reihenfolge (Eltern vor Kindern) zerstört.

    Strategie:
    1. Kategorien umbenennen, sodass Eltern alphabetisch vor Kindern kommen
    2. Generierung mit umbenannten Kategorien ausfuehren
    3. Ergebnisse zurueck-umbenennen
    4. Ungueltige Testfaelle filtern (Sicherheitsnetz)

    Args:
        strategy: 'each_choice', 'linear', 'all_combinations', 'pairwise', 'twise'
        hierarchy: HierarchyDescriptor
        categories: Originale Kategorien
        additional_rules: Zusaetzliche Regeln
        **kwargs: Zusätzliche Parameter (z.B. t fuer t_wise, deadline fuer ipo)

    Returns:
        Liste von Testfaellen, die alle Hierarchie-Constraints einhalten
    """
    # Step 1: Prepare categories (reorder values, add N/A)
    cats = _reorder_for_hierarchy(hierarchy, categories)

    # Step 2: Rename categories so parents come before children alphabetically
    rename_map, reverse_map = _create_rename_maps(hierarchy, cats)
    renamed_cats = {rename_map[k]: v for k, v in cats.items()}

    # Step 3: Generate hierarchy constraints with RENAMED category names
    renamed_rules = _generate_renamed_hierarchy_constraints(
        hierarchy, renamed_cats, rename_map
    )
    if additional_rules:
        renamed_rules.extend(_rename_rules_in_engine(list(additional_rules), rename_map))

    engine = RuleEngine(renamed_rules)

    # Step 4: Generate based on strategy
    if strategy == "each_choice":
        from combinatorics import each_choice as ec_mod
        result = ec_mod.generate(renamed_cats, rule_engine=engine)
    elif strategy == "linear":
        from combinatorics import linear_expansion as le_mod
        result = le_mod.generate(renamed_cats, rule_engine=engine)
    elif strategy == "all_combinations":
        from combinatorics import all_combinations as ac_mod
        result = ac_mod.generate(renamed_cats)
        # Filter invalid (all_combinations has no rule_engine parameter)
        result = [tc for tc in result if engine.is_combination_valid(tc)]
        result = [engine.apply_dependency_rules(tc) for tc in result]
    elif strategy == "pairwise":
        from combinatorics import ipo
        result = ipo.generate(renamed_cats, rule_engine=engine, **kwargs)
    elif strategy == "twise":
        from combinatorics import t_wise as tw_mod
        t_value = kwargs.get('t', 2)
        result = tw_mod.generate(renamed_cats, t=t_value, rule_engine=engine)
    else:
        raise ValueError(f"Unbekannte Strategie: {strategy}")

    # Step 5: Rename back to original category names
    result = [_rename_testcase(tc, reverse_map) for tc in result]

    # Step 6: Filter invalid (safety net)
    result = [tc for tc in result if is_valid_hierarchical_testcase(tc, hierarchy, cats)]

    # Step 7: Deduplicate
    result = _deduplicate(result)

    return result


def _generate_renamed_hierarchy_constraints(
    hierarchy: HierarchyDescriptor,
    renamed_categories: Dict[str, List[str]],
    rename_map: Dict[str, str],
) -> List:
    """
    Generiert Hierarchie-Constraints direkt mit umbenannten Kategorien.
    """
    rules: List = []

    for child_cat, parent_val in hierarchy.parent_value_id.items():
        parent_cat = hierarchy.get_parent_category(child_cat)
        if parent_cat is None:
            continue

        # Get renamed category names
        renamed_parent = rename_map.get(parent_cat, parent_cat)
        renamed_child = rename_map.get(child_cat, child_cat)

        parent_values = renamed_categories.get(renamed_parent, [])

        # DependencyRules for non-activating parent values
        for parent_v in parent_values:
            if parent_v == parent_val:
                continue
            rules.append(
                DependencyRule(
                    if_category=renamed_parent,
                    if_value=parent_v,
                    then_category=renamed_child,
                    then_value=HIERARCHY_NOT_APPLICABLE,
                )
            )

        # ForbiddenRule for activating parent + N/A child
        rules.append(
            ForbiddenRule(
                if_category=renamed_parent,
                if_value=parent_val,
                then_category=renamed_child,
                then_value=HIERARCHY_NOT_APPLICABLE,
            )
        )

    return rules


def _create_rename_maps(
    hierarchy: HierarchyDescriptor,
    categories: Dict[str, List[str]],
) -> tuple:
    """
    Erstellt Rename-Maps, sodass Eltern-Kategorien alphabetisch vor
    ihren Kind-Kategorien kommen.

    Strategie: Fuege Praefixe hinzu, die die Hierarchie-Tiefe kodieren.
    - Tiefe 0: "00_"
    - Tiefe 1: "01_"
    - Tiefe 2: "02_"
    """
    rename_map = {}
    reverse_map = {}

    for cat_name in categories:
        depth = hierarchy.depth_map.get(cat_name, 0)
        renamed = f"{depth:02d}_{cat_name}"
        rename_map[cat_name] = renamed
        reverse_map[renamed] = cat_name

    return rename_map, reverse_map


def _rename_testcase(
    tc: Dict[str, str],
    reverse_map: Dict[str, str],
) -> Dict[str, str]:
    """Umbennt Kategorien in einem Testfall zurueck."""
    return {reverse_map.get(k, k): v for k, v in tc.items()}


def _rename_rules_in_engine(
    rules: List,
    rename_map: Dict[str, str],
) -> List:
    """Umbennt Kategorien in Regeln."""
    renamed = []
    for rule in rules:
        if isinstance(rule, ForbiddenRule):
            renamed.append(ForbiddenRule(
                if_category=rename_map.get(rule.if_category, rule.if_category),
                if_value=rule.if_value,
                then_category=rename_map.get(rule.then_category, rule.then_category),
                then_value=rule.then_value,
            ))
        elif isinstance(rule, DependencyRule):
            renamed.append(DependencyRule(
                if_category=rename_map.get(rule.if_category, rule.if_category),
                if_value=rule.if_value,
                then_category=rename_map.get(rule.then_category, rule.then_category),
                then_value=rule.then_value,
            ))
        else:
            renamed.append(rule)
    return renamed


def _deduplicate(testcases: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Entfernt Duplikate."""
    seen = set()
    result = []
    for tc in testcases:
        key = tuple(sorted(tc.items()))
        if key not in seen:
            seen.add(key)
            result.append(tc)
    return result