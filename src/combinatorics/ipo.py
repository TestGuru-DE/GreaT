"""IPOG-Algorithmus fuer Pairwise-Generierung (BUG B-02: korrigierte Fassung).

Referenz: Y. Lei, R. Kacker, D. R. Kuhn, V. Okun, J. Lawrence:
"IPOG: A General Strategy for T-Way Software Testing", ECBS 2007.

Ablauf (t = 2):
1. Kategorien nach absteigender Werteanzahl ordnen (kleinere Suiten).
2. Startsuite = alle gueltigen Paare der ersten beiden Kategorien.
3. Fuer jede weitere Kategorie:
   a) Horizontales Wachstum: Jeder bestehende Testfall erhaelt den Wert der
      neuen Kategorie, der die meisten noch offenen Paare abdeckt.
   b) Vertikales Wachstum: Verbleibende Paare werden zuerst in bestehende
      Testfaelle mit freien Stellen ("don't care") eingetragen; nur wenn das
      nicht geht, entsteht ein neuer Testfall.
4. Freie Stellen werden mit einem gueltigen Wert gefuellt.
5. Kontrolle: Moegliche Paare, die (z. B. durch Regeln beim Fuellen) nicht
   abgedeckt sind, werden gezielt nachgetragen.

Regeln (REQ-3040, REQ-6001): Ein Paar ist "moeglich", wenn die Teilbelegung aus
genau diesen zwei Werten gueltig ist; ein Testfall wird nur gebildet, wenn seine
(Teil-)Belegung gueltig ist. Zeitbudget: combinatorics.budget.checkpoint().
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from .budget import checkpoint, time_budget  # BUG B-03

Testcase = Dict[str, Optional[str]]


def generate(
    categories: Dict[str, List[str]],
    rule_engine=None,
    deadline: Optional[float] = None,
) -> List[Dict[str, str]]:
    """Pairwise-Generierung (IPOG). Deterministisch fuer gleiche Eingaben.

    Args:
        categories: Kategoriename -> Werteliste.
        rule_engine: optionale RuleEngine (is_combination_valid, apply_dependency_rules).
        deadline: optionale Unix-Zeit; bei Ueberschreitung BudgetExceeded.
    """
    if deadline is not None:
        with time_budget(deadline):
            return _best_of(categories, rule_engine)
    return _best_of(categories, rule_engine)


def _best_of(categories: Dict[str, List[str]], rule_engine) -> List[Dict[str, str]]:
    """Rechnet zwei Gleichstandsregeln und liefert die kleinere Suite.

    Beide Laeufe sind deterministisch und schnell (Millisekunden bis wenige
    Zehntelsekunden); kleine Modelle profitieren von der einfachen Regel,
    grosse von der Bevorzugung von Werten mit vielen offenen Paaren.
    """
    first = _generate(categories, rule_engine, prefer_open=False)
    second = _generate(categories, rule_engine, prefer_open=True)
    return second if len(second) < len(first) else first


def _generate(categories: Dict[str, List[str]], rule_engine, prefer_open: bool = False) -> List[Dict[str, str]]:
    if not categories or any(len(v) == 0 for v in categories.values()):
        return []

    # Schneller Pfad: Engine ohne Regeln muss nicht befragt werden
    has_rules = rule_engine is not None and any(
        getattr(rule_engine, attr, True)
        for attr in ("_combine_rules", "_forbidden_rules", "_dependency_rules", "_constraint_rules")
    )

    def valid(tc: Testcase) -> bool:
        if not has_rules:
            return True
        return rule_engine.is_combination_valid({k: v for k, v in tc.items() if v is not None})

    # Reihenfolge: viele Werte zuerst, bei Gleichstand nach Name (deterministisch)
    keys = sorted(categories.keys(), key=lambda k: (-len(categories[k]), k))
    n = len(keys)

    if n == 1:
        result = [{keys[0]: v} for v in categories[keys[0]] if valid({keys[0]: v})]
        return _finish(result, rule_engine)

    # --- Startsuite aus den ersten beiden Kategorien ---
    k0, k1 = keys[0], keys[1]
    suite: List[Testcase] = []
    for v0 in categories[k0]:
        for v1 in categories[k1]:
            checkpoint()
            tc: Testcase = {k0: v0, k1: v1}
            if valid(tc):
                suite.append(tc)

    # --- Kategorien schrittweise hinzufuegen ---
    for i in range(2, n):
        checkpoint()
        new_cat = keys[i]
        prev_cats = keys[:i]
        new_values = categories[new_cat]

        # Offene (moegliche) Paare: (prev_cat, prev_val, new_val)
        uncovered: Set[Tuple[str, str, str]] = set()
        for c in prev_cats:
            for pv in categories[c]:
                for nv in new_values:
                    checkpoint()
                    if valid({c: pv, new_cat: nv}):
                        uncovered.add((c, pv, nv))

        # a) Horizontales Wachstum
        # Gleichstand: Wert mit den meisten noch offenen Paaren bevorzugen
        open_per_value = {nv: 0 for nv in new_values}
        for _c, _pv, _nv in uncovered:
            open_per_value[_nv] += 1
        for tc in suite:
            checkpoint()
            best_val, best_gain = None, (-1, -1)
            for nv in new_values:
                candidate = dict(tc)
                candidate[new_cat] = nv
                if not valid(candidate):
                    continue
                gain = (sum(
                    1 for c in prev_cats
                    if tc.get(c) is not None and (c, tc[c], nv) in uncovered
                ), open_per_value[nv] if prefer_open else 0)
                if gain > best_gain:
                    best_val, best_gain = nv, gain
            tc[new_cat] = best_val  # None = don't care (kein gueltiger Wert gefunden)
            if best_val is not None:
                for c in prev_cats:
                    if tc.get(c) is not None and (c, tc[c], best_val) in uncovered:
                        uncovered.discard((c, tc[c], best_val))
                        open_per_value[best_val] -= 1

        # b) Vertikales Wachstum (deterministische Reihenfolge)
        order = {c: idx for idx, c in enumerate(prev_cats)}
        for c, pv, nv in sorted(uncovered, key=lambda p: (order[p[0]], categories[p[0]].index(p[1]), new_values.index(p[2]))):
            checkpoint()
            placed = False
            for tc in suite:
                if tc.get(c) not in (None, pv) or tc.get(new_cat) not in (None, nv):
                    continue
                if tc.get(c) == pv and tc.get(new_cat) == nv:
                    placed = True  # bereits abgedeckt (durch fruehere Platzierung)
                    break
                candidate = dict(tc)
                candidate[c] = pv
                candidate[new_cat] = nv
                if valid(candidate):
                    tc[c] = pv
                    tc[new_cat] = nv
                    placed = True
                    break
            if not placed:
                new_tc: Testcase = {k: None for k in keys[: i + 1]}
                new_tc[c] = pv
                new_tc[new_cat] = nv
                suite.append(new_tc)

    # --- Freie Stellen fuellen ---
    completed: List[Dict[str, str]] = []
    for tc in suite:
        checkpoint()
        filled = _fill_dont_cares(tc, keys, categories, valid)
        if filled is not None:
            completed.append(filled)

    # --- Kontrolle: fehlende moegliche Paare nachtragen ---
    completed.extend(_cover_missing_pairs(completed, keys, categories, valid))

    # --- Redundanz entfernen: Testfaelle, deren Paare alle mehrfach vorkommen ---
    completed = _remove_redundant(completed, keys)

    return _finish(completed, rule_engine)


def _remove_redundant(suite: List[Dict[str, str]], keys: List[str]) -> List[Dict[str, str]]:
    """Entfernt Testfaelle, deren saemtliche Paare auch in anderen Testfaellen vorkommen.

    Durchlauf von hinten (spaet erzeugte Testfaelle decken oft nur noch wenige
    Paare ab). Die Paarabdeckung bleibt unveraendert.
    """
    from collections import Counter

    def pairs(tc: Dict[str, str]):
        return [
            (keys[a], tc[keys[a]], keys[b], tc[keys[b]])
            for a in range(len(keys)) for b in range(a + 1, len(keys))
        ]

    counts: Counter = Counter()
    for tc in suite:
        counts.update(pairs(tc))

    kept: List[Optional[Dict[str, str]]] = list(suite)
    for idx in range(len(kept) - 1, -1, -1):
        checkpoint()
        tc_pairs = pairs(kept[idx])  # type: ignore[arg-type]
        if all(counts[p] > 1 for p in tc_pairs):
            counts.subtract(tc_pairs)
            kept[idx] = None
    return [tc for tc in kept if tc is not None]


def _fill_dont_cares(
    tc: Testcase, keys: List[str], categories: Dict[str, List[str]], valid
) -> Optional[Dict[str, str]]:
    """Fuellt freie Stellen mit dem ersten gueltigen Wert (begrenzte Rueckverfolgung)."""
    result: Testcase = {k: tc.get(k) for k in keys}
    open_cats = [k for k in keys if result[k] is None]

    def backtrack(idx: int) -> bool:
        checkpoint()
        if idx == len(open_cats):
            return True
        cat = open_cats[idx]
        for v in categories[cat]:
            result[cat] = v
            if valid(result) and backtrack(idx + 1):
                return True
        result[cat] = None
        return False

    if not valid(result) or not backtrack(0):
        return None
    return {k: v for k, v in result.items()}  # type: ignore[misc]


def _cover_missing_pairs(
    suite: List[Dict[str, str]], keys: List[str], categories: Dict[str, List[str]], valid
) -> List[Dict[str, str]]:
    """Traegt moegliche Paare nach, die noch in keinem Testfall vorkommen."""
    covered: Set[Tuple[str, str, str, str]] = set()
    for tc in suite:
        for a in range(len(keys)):
            for b in range(a + 1, len(keys)):
                covered.add((keys[a], tc[keys[a]], keys[b], tc[keys[b]]))

    extra: List[Dict[str, str]] = []
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            ca, cb = keys[a], keys[b]
            for va in categories[ca]:
                for vb in categories[cb]:
                    checkpoint()
                    if (ca, va, cb, vb) in covered or not valid({ca: va, cb: vb}):
                        continue
                    filled = _fill_dont_cares({ca: va, cb: vb}, keys, categories, valid)
                    if filled is None:
                        continue  # im Gesamtmodell unmoeglich (indirekter Regelkonflikt)
                    extra.append(filled)
                    for x in range(len(keys)):
                        for y in range(x + 1, len(keys)):
                            covered.add((keys[x], filled[keys[x]], keys[y], filled[keys[y]]))
    return extra


def _finish(testcases: List[Dict[str, str]], rule_engine) -> List[Dict[str, str]]:
    if rule_engine is not None:
        testcases = [rule_engine.apply_dependency_rules(tc) for tc in testcases]
    return _deduplicate(testcases)


def _deduplicate(testcases: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Entfernt Duplikate aus Testfall-Liste."""
    seen: Set[Tuple] = set()
    result: List[Dict[str, str]] = []
    for tc in testcases:
        checkpoint()
        key = tuple(sorted(tc.items()))
        if key not in seen:
            seen.add(key)
            result.append(tc)
    return result
