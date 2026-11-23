"""
REQ-6016: Hierarchische Klassen — Datenmodell-Erweiterung

Fügt parent_value_id zum Category-Modell hinzu, um Unter-Kategorien
zu modellieren. Eine Kategorie kann als Kind einer anderen Kategorie
definiert werden, aktiviert durch einen spezifischen Eltern-Wert.

Maximal 3 Ebenen tief. Keine zyklischen Referenzen.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HIERARCHY_NOT_APPLICABLE = "-"  # Sonderwert: nicht anwendbar
MAX_HIERARCHY_DEPTH = 3


# ---------------------------------------------------------------------------
# Hierarchy Descriptor (pure data, no DB dependency)
# ---------------------------------------------------------------------------


class HierarchyDescriptor:
    """
    Repräsentiert die Hierarchie-Struktur eines Projekts als in-memory
    Datenstruktur. Wird von hierarchy_constraints.py und coverage.py
    verwendet, um implizite Constraints und Coverage-Berechnungen zu
    ermöglichen, ohne direkt auf das ORM zuzugreifen.

    Attributes:
        parent_value_id: Mapping {child_category_name: parent_value_name}
            Gibt den Eltern-Wert an, der die Kind-Kategorie aktiviert.
        child_categories: Mapping {parent_value_name: [child_category_names]}
            Umgekehrtes Mapping: welche Kinder hat ein Eltern-Wert?
        depth_map: Mapping {category_name: int}
            Tiefe jeder Kategorie (0 = Wurzel, 1 = Kind, 2 = Enkel)
    """

    def __init__(self):
        # child_category_name -> parent_value_name (der Wert, der sie aktiviert)
        self.parent_value_id: Dict[str, str] = {}
        # parent_category_name -> parent_value_name -> [child_category_names]
        self.child_map: Dict[str, Dict[str, List[str]]] = {}
        # category_name -> depth (0=root, 1=child, 2=grandchild)
        self.depth_map: Dict[str, int] = {}

    @classmethod
    def from_categories(
        cls,
        categories: Dict[str, List[str]],
        parent_value_ids: Dict[str, Optional[str]],
    ) -> "HierarchyDescriptor":
        """
        Erzeugt HierarchyDescriptor aus flachen Datenstrukturen.

        Args:
            categories: {category_name: [value1, value2, ...]}
            parent_value_ids: {child_category_name: parent_value_name | None}
                parent_value_name ist der Wert des Elterns, der diese Kategorie aktiviert.
                None bedeutet: diese Kategorie hat keinen Eltern-Wert (Wurzelkategorie).

        Returns:
            HierarchyDescriptor-Instanz

        Raises:
            ValueError: bei zu großer Tiefe (>3 Ebenen) oder zyklischen Referenzen
        """
        desc = cls()

        for cat_name, parent_val in parent_value_ids.items():
            if parent_val is None:
                desc.depth_map[cat_name] = 0
                continue

            # parent_val ist der Name des Eltern-WERTES
            # Wir müssen die Eltern-Kategorie finden, die diesen Wert enthält
            parent_cat = None
            for cat_name_check, vals in categories.items():
                if parent_val in vals:
                    parent_cat = cat_name_check
                    break

            if parent_cat is None:
                raise ValueError(
                    f"Parent value '{parent_val}' for category '{cat_name}' "
                    f"not found in any category"
                )

            desc.parent_value_id[cat_name] = parent_val

            # Build child map
            if parent_cat not in desc.child_map:
                desc.child_map[parent_cat] = {}
            if parent_val not in desc.child_map[parent_cat]:
                desc.child_map[parent_cat][parent_val] = []
            desc.child_map[parent_cat][parent_val].append(cat_name)

            # Depth: parent depth + 1
            parent_depth = desc.depth_map.get(parent_cat, 0)
            desc.depth_map[cat_name] = parent_depth + 1

        # Validate depth (max 3 Ebenen = depth 0,1,2)
        for cat_name, depth in desc.depth_map.items():
            if depth >= MAX_HIERARCHY_DEPTH:
                raise ValueError(
                    f"Category '{cat_name}' exceeds max depth {MAX_HIERARCHY_DEPTH} "
                    f"(depth={depth}). Max 3 levels allowed."
                )

        return desc

    def get_parent_category(self, child_category: str) -> Optional[str]:
        """Gibt die Eltern-Kategorie einer Kind-Kategorie zurück."""
        parent_val = self.parent_value_id.get(child_category)
        if parent_val is None:
            return None
        for cat_name, val_map in self.child_map.items():
            if parent_val in val_map:
                return cat_name
        return None

    def get_parent_value(self, child_category: str) -> Optional[str]:
        """Gibt den Eltern-WERT zurück, der eine Kind-Kategorie aktiviert."""
        return self.parent_value_id.get(child_category)

    def get_children(self, parent_category: str, parent_value: str) -> List[str]:
        """Gibt alle Kind-Kategorien eines Eltern-Wertes zurück."""
        return self.child_map.get(parent_category, {}).get(parent_value, [])

    def is_child_category(self, category_name: str) -> bool:
        """Prüft ob eine Kategorie eine Kind-Kategorie ist."""
        return category_name in self.parent_value_id

    def get_all_child_categories(self) -> List[str]:
        """Gibt alle Kind-Kategorien zurück."""
        return list(self.parent_value_id.keys())

    def get_hierarchy_chain(self, category_name: str) -> List[Tuple[str, str]]:
        """
        Gibt die Hierarchie-Kette einer Kategorie als Liste von
        (category_name, parent_value_name) Tupeln zurück, von der Wurzel
        zur aktuellen Kategorie.
        """
        chain = []
        current = category_name
        visited = set()

        while current in self.parent_value_id:
            if current in visited:
                raise ValueError(f"Circular hierarchy detected involving '{current}'")
            visited.add(current)
            parent_val = self.parent_value_id[current]
            parent_cat = self.get_parent_category(current)
            if parent_cat is None:
                break
            chain.append((parent_cat, parent_val))
            current = parent_cat

        chain.reverse()
        return chain

    def validate_no_cycles(self) -> bool:
        """
        Prüft auf zyklische Referenzen.
        Returns True wenn keine Zyklen existieren.
        """
        for cat_name in list(self.parent_value_id.keys()):
            try:
                self.get_hierarchy_chain(cat_name)
            except ValueError:
                return False
        return True

    def get_effective_categories(
        self, categories: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Gibt Kategorien mit erweitertem Werteset zurück: jede Kind-Kategorie
        enthält HIERARCHY_NOT_APPLICABLE ("-") als zusätzlichen Wert.
        """
        result = dict(categories)
        for child_cat in self.get_all_child_categories():
            if child_cat in result:
                values = result[child_cat]
                if HIERARCHY_NOT_APPLICABLE not in values:
                    result[child_cat] = values + [HIERARCHY_NOT_APPLICABLE]
        return result