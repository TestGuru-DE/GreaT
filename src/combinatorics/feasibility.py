"""Machbarkeit von Wertekombinationen unter Regeln und Constraints.

Beantwortet: Gibt es einen VOLLSTAENDIGEN, regelkonformen Testfall, der eine
gegebene Teilbelegung (z. B. ein Paar) enthaelt?

Die Teilpruefung RuleEngine.is_combination_valid() verwirft eine Teilbelegung
nur, wenn eine Regel SICHER verletzt ist. Paare, die erst ueber zwei verkettete
Constraints unmoeglich werden, bestehen sie trotzdem. Dafuer sucht diese Klasse
per Tiefensuche eine Vervollstaendigung.

Genutzt fuer:
- Abdeckung: nur machbare Tupel zaehlen als moeglich (BUG K-06)
- Warnungen zu unerreichbaren Werten (REQ-6001 AK-8, BUG K-06/K-07)
- regelbewusstes Vervollstaendigen von Testfaellen (risk_based, Lueckenschluss)

Effizienz: Die Suche laeuft nur ueber Kategorien, die in Regeln vorkommen.
Andere Kategorien sind frei waehlbar und beeinflussen die Machbarkeit nicht.
Ergebnisse werden je (relevanter) Teilbelegung zwischengespeichert. Ein
Knotenbudget begrenzt die Suche; wird es erschoepft, gilt die Belegung als
machbar (konservativ: nichts wird faelschlich als unmoeglich gemeldet).
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .budget import checkpoint

Assignment = Dict[str, str]


def _rule_categories(rule_engine, categories: Dict[str, List[str]]) -> set:
    """Kategorien, die in irgendeiner Regel oder einem Constraint vorkommen."""
    names: set = set()
    for attr in ("_combine_rules", "_forbidden_rules", "_dependency_rules"):
        for rule in getattr(rule_engine, attr, []):
            names.update((rule.if_category, rule.then_category))
    constraint_rules = getattr(rule_engine, "_constraint_rules", [])
    if constraint_rules:
        try:
            from app.constraints.references import iter_references
        except ImportError:  # pragma: no cover - ohne App-Paket: alle Kategorien relevant
            return set(categories)
        for rule in constraint_rules:
            id_to_name = {cid: name for name, cid in rule.category_map.items()}
            for cid, _ in iter_references(rule.expression):
                if cid in id_to_name:
                    names.add(id_to_name[cid])
    return names & set(categories)


class FeasibilityChecker:
    """Prueft und vervollstaendigt Teilbelegungen gegen eine RuleEngine."""

    def __init__(self, categories: Dict[str, List[str]], rule_engine=None, node_budget: int = 20000):
        self.categories = categories
        self.engine = rule_engine
        self.node_budget = node_budget
        self.exhausted = False  # True, wenn eine Suche am Budget abgebrochen wurde
        self._cache: Dict[frozenset, bool] = {}
        if rule_engine is None:
            self.relevant: List[str] = []
        else:
            rel = _rule_categories(rule_engine, categories)
            # wenige Werte zuerst: kleinerer Suchbaum
            self.relevant = sorted(rel, key=lambda c: (len(categories[c]), c))

    # -- Grundpruefung -------------------------------------------------------

    def is_consistent(self, partial: Assignment) -> bool:
        """Keine Regel ist durch die Teilbelegung sicher verletzt.

        Abhaengigkeitsregeln (WENN a=x DANN b=y) gelten als Bedingung: ein Testfall
        mit a=x und b != y kommt nach ihrer Anwendung nie vor.
        """
        if self.engine is None:
            return True
        if not self.engine.is_combination_valid(partial):
            return False
        for rule in getattr(self.engine, "_dependency_rules", []):
            if partial.get(rule.if_category) == rule.if_value:
                then_val = partial.get(rule.then_category)
                if then_val is not None and then_val != rule.then_value:
                    return False
        return True

    # -- Machbarkeit -----------------------------------------------------------

    def is_feasible(self, partial: Assignment) -> bool:
        """Gibt es einen vollstaendigen regelkonformen Testfall mit dieser Teilbelegung?"""
        if self.engine is None:
            return all(partial.get(c) in self.categories.get(c, []) for c in partial)
        if not self.is_consistent(partial):
            return False
        relevant_part = {c: v for c, v in partial.items() if c in self.relevant}
        key = frozenset(relevant_part.items())
        if key not in self._cache:
            remaining = [c for c in self.relevant if c not in relevant_part]
            self._nodes = 0
            self._cache[key] = self._search(dict(relevant_part), remaining, 0)
        return self._cache[key]

    def _search(self, partial: Assignment, remaining: List[str], idx: int) -> bool:
        if idx == len(remaining):
            return True
        self._nodes += 1
        if self._nodes > self.node_budget:
            self.exhausted = True
            return True  # konservativ
        if self._nodes % 256 == 0:
            checkpoint()
        cat = remaining[idx]
        try:
            for val in self.categories[cat]:
                partial[cat] = val
                if self.is_consistent(partial) and self._search(partial, remaining, idx + 1):
                    return True
            return False
        finally:
            partial.pop(cat, None)

    def is_satisfiable(self) -> bool:
        """Gibt es ueberhaupt einen regelkonformen Testfall?"""
        return self.is_feasible({})

    def unreachable_values(self) -> List[tuple]:
        """(Kategorie, Wert) fuer jeden Wert, der in keinem gueltigen Testfall vorkommen kann."""
        result = []
        for cat in self.categories:
            for val in self.categories[cat]:
                if not self.is_feasible({cat: val}):
                    result.append((cat, val))
        return result

    # -- Vervollstaendigen ---------------------------------------------------------

    def complete(self, partial: Assignment, preferences: Optional[Dict[str, Iterable[str]]] = None) -> Optional[Assignment]:
        """Ergaenzt die Teilbelegung zu einem vollstaendigen gueltigen Testfall.

        preferences: je Kategorie die bevorzugte Reihenfolge der Werte.
        Gibt None zurueck, wenn die Teilbelegung nicht machbar ist.
        """
        if not self.is_feasible(partial):
            return None
        result = dict(partial)
        preferences = preferences or {}
        # Regel-Kategorien zuerst (dort entscheidet sich die Gueltigkeit)
        order = [c for c in self.relevant if c not in result] + \
                [c for c in self.categories if c not in result and c not in self.relevant]
        for cat in order:
            candidates = list(preferences.get(cat, [])) + [v for v in self.categories[cat]
                                                           if v not in set(preferences.get(cat, []))]
            for val in candidates:
                result[cat] = val
                if self.is_feasible(result):
                    break
            else:  # nur bei erschoepftem Budget denkbar
                return None
        return result
