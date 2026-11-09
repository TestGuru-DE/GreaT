"""REQ-5003/5004/5005/5013/5014/5015/5018/5019/5020/5021: Entscheidungstabelle-Generierung

Generiert alle gueltigen Kombinationen der Ursachen (2^N fuer Boolean).
Ursachen werden automatisch mit Y/N gefuellt.
Wirkungen bleiben initial leer.

REQ-5013: Collapsing (redundante Regeln zusammenfassen)
REQ-5014: Checksum-Validierung
REQ-5015: Extended Entry (mehr als 2 Werte pro Ursache)
REQ-5018: Cause-Effect-Graph-Daten fuer Visualisierung
REQ-5019: Widerspruchserkennung
REQ-5020: Vollstaendigkeitspruefung (Luecken-Erkennung)
REQ-5021: Priorisierung von Wirkungen (Override)
"""
import itertools
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from .models import Category, Value
from .config import get_max_testcases

logger = logging.getLogger(__name__)


def _build_effect_list(db: Session, effects, effect_mode: str) -> List[Dict[str, Any]]:
    """REQ-5016: Bauen die effect-Liste mit optionalen Werten.

    Args:
        db: Datenbank-Session
        effects: Liste von Category-Objekten (Wirkungen)
        effect_mode: "binary" oder "text"

    Returns:
        Liste von Dicts mit id, name und optional values.
    """
    if effect_mode == "text":
        result = []
        for effect in effects:
            values = db.query(Value).filter(Value.category_id == effect.id).all()
            if values:
                effect_values = [v.value for v in values]
            else:
                # Fallback-Werte wenn keine Werte existieren
                effect_values = ["Genehmigen", "Ablehnen", "Manuelle Pruefung"]
            result.append({
                "id": effect.id,
                "name": effect.name,
                "values": effect_values,
            })
        return result
    else:
        # binary-Modus: nur id und name
        return [{"id": e.id, "name": e.name} for e in effects]


def generate_decision_table(db: Session, project_id: int,
                            use_extended_entry: bool = False,
                            effect_mode: str = "binary") -> Dict[str, Any]:
    """Generiert eine vollstaendige Entscheidungstabelle.

    REQ-5003: Layout (Ursachen oben, Wirkungen unten)
    REQ-5004: Boolean-Werte (Y/N) fuer jede Ursache
    REQ-5005: Alle Kombinationen generieren (2^N)
    REQ-5015: Extended Entry (mehr als 2 Werte pro Ursache)
    REQ-5016: Wirkungen als Text (effect_mode="text")

    Args:
        db: Datenbank-Session
        project_id: Projekt-ID
        use_extended_entry: Wenn True, verwendet echte Werte der Kategorie (REQ-5015)
        effect_mode: "binary" (default, X/-) oder "text" (Werte aus Wirkung-Kategorie)

    Returns:
        {
            "causes": [{"id": ..., "name": ..., "values": ["Y", "N"]}],
            "effects": [{"id": ..., "name": ..., "values": [...]}],
            "rules": [
                {
                    "id": 1,
                    "causes": {"cause_id": "Y", ...},
                    "effects": {"effect_id": None, ...},  # initial leer
                },
                ...
            ],
            "total_rules": int,
        }
    """
    # Hole Ursache- und Wirkungskategorien
    causes = (
        db.query(Category)
        .filter(
            Category.project_id == project_id,
            Category.category_type == "cause",
        )
        .order_by(Category.order_index, Category.id)
        .all()
    )

    effects = (
        db.query(Category)
        .filter(
            Category.project_id == project_id,
            Category.category_type == "effect",
        )
        .order_by(Category.order_index, Category.id)
        .all()
    )

    if not causes:
        # REQ-5016: effect_mode="text" fuegt Werte der Wirkungskategorien hinzu
        effect_list = _build_effect_list(db, effects, effect_mode)
        return {
            "causes": [],
            "effects": effect_list,
            "rules": [],
            "total_rules": 0,
            "error": "Keine Ursachen definiert. Erstellen Sie mindestens eine Kategorie vom Typ 'cause'.",
        }

    # REQ-5004: Boolean-Werte (Y/N) fuer jede Ursache
    # REQ-5015: Extended Entry – echte Werte der Kategorie verwenden
    if use_extended_entry:
        cause_values_map: Dict[int, List[str]] = {}
        for cause in causes:
            values = db.query(Value).filter(Value.category_id == cause.id).all()
            if values:
                cause_values_map[cause.id] = [v.value for v in values]
            else:
                # Fallback: Y/N wenn keine Werte existieren
                cause_values_map[cause.id] = ["Y", "N"]
    else:
        cause_values_map = {c.id: ["Y", "N"] for c in causes}

    if not effects:
        return {
            "causes": [{"id": c.id, "name": c.name, "values": cause_values_map[c.id]} for c in causes],
            "effects": [],
            "rules": [],
            "total_rules": 0,
            "error": "Keine Wirkungen definiert. Erstellen Sie mindestens eine Kategorie vom Typ 'effect'.",
        }

    # REQ-5005: Alle Kombinationen generieren
    # REQ-5015: Bei Extended Entry ist die Anzahl das Produkt aller Wertemengen
    value_lists = [cause_values_map[c.id] for c in causes]
    num_combinations = 1
    for vl in value_lists:
        num_combinations *= len(vl)
    max_testcases = get_max_testcases()

    if num_combinations > max_testcases:
        # REQ-5016: effect_mode="text" fuegt Werte der Wirkungskategorien hinzu
        effect_list = _build_effect_list(db, effects, effect_mode)
        return {
            "causes": [{"id": c.id, "name": c.name, "values": cause_values_map[c.id]} for c in causes],
            "effects": effect_list,
            "rules": [],
            "total_rules": 0,
            "total_combinations": num_combinations,
            "error": (
                f"Zu viele Kombinationen ({num_combinations}). "
                f"Limit: {max_testcases}. "
                f"Reduzieren Sie die Ursachen oder erhoehen Sie das Limit."
            ),
        }

    # Generiere alle Kombinationen (kartesisches Produkt)
    combinations = list(itertools.product(*value_lists))

    # Erstelle Regeln
    rules: List[Dict[str, Any]] = []
    for i, combo in enumerate(combinations, 1):
        rule: Dict[str, Any] = {
            "id": i,
            "causes": {},
            "effects": {},
        }

        # REQ-5003: Ursachen automatisch mit Y/N fuellen
        for j, cause in enumerate(causes):
            rule["causes"][cause.id] = combo[j]

        # REQ-5003: Wirkungen initial leer (None = leer, Tester tragt manuell ein)
        for effect in effects:
            rule["effects"][effect.id] = None

        rules.append(rule)

    # REQ-5016: effect_mode="text" fuegt Werte der Wirkungskategorien hinzu
    effect_list = _build_effect_list(db, effects, effect_mode)

    return {
        "causes": [{"id": c.id, "name": c.name, "values": cause_values_map[c.id]} for c in causes],
        "effects": effect_list,
        "rules": rules,
        "total_rules": len(rules),
    }


def apply_constraints(rules: List[Dict], constraints: List[Dict]) -> List[Dict]:
    """REQ-5007-5011: Constraints auf Regeln anwenden.

    Args:
        rules: Liste der generierten Regeln
        constraints: Liste von Constraint-Definitionen
            [{"type": "E", "causes": [id1, id2]}, ...]

    Supported constraint types:
        E - Exclusive: max 1 cause can be Y
        O - One-and-Only-One: exactly 1 cause must be Y
        I - Inclusive: at least 1 cause must be Y
        R - Requires: if cause1=Y then cause2=Y
        M - Mask: if effect1=X then effect2=— (None)

    Returns:
        Gefilterte Liste der gueltigen Regeln
    """
    if not constraints:
        return rules

    filtered = list(rules)

    for constraint in constraints:
        ctype = constraint.get("type")

        if ctype == "E":  # Exclusive: max 1 cause can be Y
            cause_ids = constraint.get("causes", [])
            filtered = [
                r
                for r in filtered
                if sum(1 for c_id in cause_ids if r["causes"].get(c_id) == "Y") <= 1
            ]

        elif ctype == "O":  # One-and-Only-One: exactly 1 cause must be Y
            cause_ids = constraint.get("causes", [])
            filtered = [
                r
                for r in filtered
                if sum(1 for c_id in cause_ids if r["causes"].get(c_id) == "Y") == 1
            ]

        elif ctype == "I":  # Inclusive: at least 1 cause must be Y
            cause_ids = constraint.get("causes", [])
            filtered = [
                r
                for r in filtered
                if any(r["causes"].get(c_id) == "Y" for c_id in cause_ids)
            ]

        elif ctype == "R":  # Requires: if c1=Y then c2=Y
            c1 = constraint.get("from")
            c2 = constraint.get("to")
            if c1 is not None and c2 is not None:
                filtered = [
                    r
                    for r in filtered
                    if not (r["causes"].get(c1) == "Y" and r["causes"].get(c2) == "N")
                ]

        elif ctype == "M":  # Mask: if effect1=X then effect2=— (None)
            e1 = constraint.get("from")
            e2 = constraint.get("to")
            if e1 is not None and e2 is not None:
                for r in filtered:
                    if r["effects"].get(e1) == "X":
                        r["effects"][e2] = None

    return filtered


# =============================================================================
# REQ-5013: Collapsing (redundante Regeln zusammenfassen)
# =============================================================================

def collapse_rules(rules: List[Dict]) -> tuple[List[Dict], int]:
    """REQ-5013: Automatisches Zusammenfassen redundanter Regeln.

    3 Bedingungen (ISTQB):
    1. Identische Aktionen (Wirkungen)
    2. Genau eine Ursache unterscheidet sich
    3. Zusammen decken sie alle Werte dieser Ursache ab (Y und N)

    Args:
        rules: Liste von Regeln mit 'id', 'causes', 'effects'

    Returns:
        (reduzierte Regeln, Anzahl reduzierter Regeln)
    """
    if len(rules) <= 1:
        return rules, 0

    collapsed = True
    reduced_count = 0

    while collapsed:
        collapsed = False
        for i in range(len(rules)):
            if rules[i].get("_collapsed"):
                continue
            for j in range(i + 1, len(rules)):
                if rules[j].get("_collapsed"):
                    continue

                # Bedingung 1: Identische Wirkungen
                if rules[i]["effects"] != rules[j]["effects"]:
                    continue

                # Bedingung 2: Genau eine Ursache unterscheidet sich
                diff_causes = []
                all_cause_ids = set(rules[i]["causes"].keys()) | set(rules[j]["causes"].keys())
                for cause_id in all_cause_ids:
                    v1 = rules[i]["causes"].get(cause_id)
                    v2 = rules[j]["causes"].get(cause_id)
                    if v1 != v2:
                        diff_causes.append(cause_id)

                if len(diff_causes) != 1:
                    continue

                # Bedingung 3: Zusammen decken sie alle Werte ab (Y und N)
                vals = {rules[i]["causes"][diff_causes[0]], rules[j]["causes"][diff_causes[0]]}
                if vals != {"Y", "N"}:
                    continue

                # Collapsing!
                merged = {
                    "id": rules[i]["id"],
                    "causes": dict(rules[i]["causes"]),
                    "effects": dict(rules[i]["effects"]),
                }
                merged["causes"][diff_causes[0]] = "-"  # Don't Care
                rules[i] = merged
                rules[j]["_collapsed"] = True
                collapsed = True
                reduced_count += 1

    # Entferne zusammengefasste Regeln
    rules = [r for r in rules if not r.pop("_collapsed", False)]
    return rules, reduced_count


# =============================================================================
# REQ-5014: Checksum-Validierung
# =============================================================================

def calculate_checksum(rules: List[Dict], num_causes: int) -> Dict[str, Any]:
    """REQ-5014: Checksum-Validierung der Entscheidungstabelle.

    Checksum = Summe(2^(Anzahl Don't-Care pro Regel))
    - == 2^n -> Vollstaendig
    - > 2^n  -> Uberschneidungen
    - < 2^n  -> Luecken

    Args:
        rules: Liste von Regeln mit 'causes'
        num_causes: Anzahl der Ursachen (n)

    Returns:
        Dict mit 'checksum', 'expected', 'status', 'message'
    """
    checksum = 0
    for rule in rules:
        dont_care_count = sum(1 for v in rule["causes"].values() if v == "-")
        checksum += 2 ** dont_care_count

    expected = 2 ** num_causes

    if checksum == expected:
        status = "complete"
    elif checksum > expected:
        status = "overlap"
    else:
        status = "gap"

    return {
        "checksum": checksum,
        "expected": expected,
        "status": status,
        "message": {
            "complete": "Vollstaendig – alle Kombinationen abgedeckt",
            "overlap": "Uberschneidungen – einige Kombinationen mehrfach abgedeckt",
            "gap": "Luecken – nicht alle Kombinationen abgedeckt",
        }[status],
    }


# =============================================================================
# REQ-5019: Widerspruchserkennung
# =============================================================================

def detect_contradictions(rules: List[Dict]) -> List[Dict[str, Any]]:
    """REQ-5019: Erkennung widerspruechlicher Regeln.

    Zwei Regeln widersprechen sich wenn:
    - Identische oder ueberlappende Ursachen (durch Don't Care)
    - Unterschiedliche Wirkungen

    Args:
        rules: Liste von Regeln mit 'id', 'causes', 'effects'

    Returns:
        Liste von Widerspruechen mit 'rule_a', 'rule_b', 'message'
    """
    contradictions = []

    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            # Ueberlappende Ursachen?
            overlaps = True
            all_cause_ids = set(rules[i]["causes"].keys()) | set(rules[j]["causes"].keys())
            for cause_id in all_cause_ids:
                v1 = rules[i]["causes"].get(cause_id)
                v2 = rules[j]["causes"].get(cause_id)
                if v1 != "-" and v2 != "-" and v1 != v2:
                    overlaps = False
                    break

            if not overlaps:
                continue

            # Unterschiedliche Wirkungen?
            if rules[i]["effects"] == rules[j]["effects"]:
                continue

            contradictions.append({
                "rule_a": rules[i]["id"],
                "rule_b": rules[j]["id"],
                "message": f"Regel R{rules[i]['id']} und R{rules[j]['id']} widersprechen sich",
            })

    return contradictions


# =============================================================================
# REQ-5020: Vollstaendigkeitspruefung (Luecken-Erkennung)
# =============================================================================

def detect_gaps(rules: List[Dict], num_causes: int,
                constraints: List[Dict] = None) -> List[Dict[str, Any]]:
    """REQ-5020: Erkennung ungedeckter Kombinationen.

    Args:
        rules: Liste von Regeln mit 'causes'
        num_causes: Anzahl der Ursachen (n)
        constraints: Optional, nicht in der Grundversion verwendet

    Returns:
        Liste von Luecken mit 'combination', 'message'
    """
    if not rules:
        return []

    # Extrahiere cause IDs aus der ersten Regel
    cause_ids = list(rules[0]["causes"].keys())
    if not cause_ids:
        return []

    # Generiere alle moeglichen Y/N Kombinationen
    all_combos = list(itertools.product(["Y", "N"], repeat=len(cause_ids)))

    # Finde welche nicht abgedeckt sind
    covered = set()
    for rule in rules:
        for combo in all_combos:
            match = True
            for idx, cause_id in enumerate(cause_ids):
                rule_val = rule["causes"].get(cause_id)
                if rule_val != "-" and rule_val != combo[idx]:
                    match = False
                    break
            if match:
                covered.add(combo)

    gaps = [c for c in all_combos if c not in covered]

    return [
        {
            "combination": dict(zip(cause_ids, gap)),
            "message": f"Kombination {dict(zip(cause_ids, gap))} ist nicht abgedeckt",
        }
        for gap in gaps
    ]


# =============================================================================
# REQ-5018: Cause-Effect-Graph-Daten fuer Visualisierung
# =============================================================================

def generate_cause_effect_graph(db: Session, project_id: int) -> Dict[str, Any]:
    """REQ-5018: Cause-Effect-Graph-Daten fuer Visualisierung.

    Liest alle Ursachen, Wirkungen und Constraints eines Projekts und
    erzeugt einen Graphen mit Knoten (causes/effects) und Kanten (edges
    aus Constraints).

    Args:
        db: Datenbank-Session
        project_id: Projekt-ID

    Returns:
        {
            "causes": [{"id": 1, "name": "C1"}, ...],
            "effects": [{"id": 1, "name": "E1"}, ...],
            "edges": [
                {"from": "cause:1", "to": "effect:1", "type": "requires"},
                {"from": "cause:1", "to": "cause:2", "type": "E"},
            ],
            "constraints": [
                {"id": 1, "type": "E", "targets": [1, 2], "description": "..."},
            ]
        }
    """
    from .models.decision_table_constraint import DecisionTableConstraint

    causes = (
        db.query(Category)
        .filter(
            Category.project_id == project_id,
            Category.category_type == "cause",
        )
        .order_by(Category.order_index, Category.id)
        .all()
    )

    effects = (
        db.query(Category)
        .filter(
            Category.project_id == project_id,
            Category.category_type == "effect",
        )
        .order_by(Category.order_index, Category.id)
        .all()
    )

    constraints = (
        db.query(DecisionTableConstraint)
        .filter(DecisionTableConstraint.project_id == project_id)
        .all()
    )

    # Label-Mapping fuer Constraint-Typen
    label_map = {
        "E": "Exclusive",
        "O": "One-and-Only-One",
        "I": "Inclusive",
        "R": "Requires",
        "M": "Mask",
    }

    edges: List[Dict[str, Any]] = []
    for c in constraints:
        ctype = c.constraint_type
        targets = c.targets

        if ctype in ("E", "O", "I"):
            # Group constraints: cause-cause edges (alle Paare)
            if isinstance(targets, list):
                for i in range(len(targets)):
                    for j in range(i + 1, len(targets)):
                        edges.append({
                            "from": f"cause:{targets[i]}",
                            "to": f"cause:{targets[j]}",
                            "type": ctype,
                            "label": label_map[ctype],
                        })

        elif ctype == "R":
            # Requires: cause-cause edge (directional)
            if isinstance(targets, dict):
                edges.append({
                    "from": f"cause:{targets['from']}",
                    "to": f"cause:{targets['to']}",
                    "type": "requires",
                    "label": label_map["R"],
                })

        elif ctype == "M":
            # Mask: effect-effect edge (directional)
            if isinstance(targets, dict):
                edges.append({
                    "from": f"effect:{targets['from']}",
                    "to": f"effect:{targets['to']}",
                    "type": "mask",
                    "label": label_map["M"],
                })

    return {
        "causes": [{"id": c.id, "name": c.name} for c in causes],
        "effects": [{"id": e.id, "name": e.name} for e in effects],
        "edges": edges,
        "constraints": [
            {
                "id": c.id,
                "type": c.constraint_type,
                "targets": c.targets,
                "description": c.description,
            }
            for c in constraints
        ],
    }


# =============================================================================
# REQ-5021: Priorisierung von Wirkungen (Override)
# =============================================================================

def apply_effect_priorities(
    rules: List[Dict],
    effects: List[Dict],
    priorities: Optional[Dict[int, int]],
    enable_override: bool = False,
) -> List[Dict]:
    """REQ-5021: Priorisierung von Wirkungen bei Override.

    Wenn in einer Regel mehrere Wirkungen aktiv sind (X),
    gewinnt die hoechst-priorisierte. Andere werden zu — (None).

    Args:
        rules: Liste von Regeln mit 'id', 'causes', 'effects'
        effects: Liste von Wirkung-Definitionen (nicht direkt verwendet,
                 aber fuer API-Konsistenz uebergeben)
        priorities: Dict {effect_id: priority}, wobei 1 = hoechste Prioritaet.
                    None oder leer bedeutet keine Priorisierung.
        enable_override: Wenn True, werden niedrig-priorisierte Wirkungen
                         zu "-" (Don't Care) statt None gesetzt.
                         Dies aktiviert die Don't Care Reduktion fuer
                         hohe Prioritaet (opt-in Toggle).

    Returns:
        Modifizierte Liste von Regeln (in-place Modifikation der effects).
    """
    if not priorities:
        return rules

    for rule in rules:
        # Finde alle aktivierten Wirkungen (value == "X")
        active_effects = [
            (eid, val)
            for eid, val in rule["effects"].items()
            if val == "X"
        ]

        # Nur wenn mehr als eine Wirkung aktiv
        if len(active_effects) <= 1:
            continue

        # Sortiere nach Prioritaet (niedrigere Zahl = hoehere Prioritaet)
        # Default 999 fuer Wirkungen ohne explizite Prioritaet
        active_effects.sort(key=lambda x: priorities.get(x[0], 999))

        # Behalte nur die hoechst-priorisierte, setze den Rest
        for eid, val in active_effects[1:]:
            # REQ-5021: enable_override Toggle
            if enable_override:
                # Don't Care Reduktion: "-" statt None
                rule["effects"][eid] = "-"
            else:
                # Standard: auf None setzen
                rule["effects"][eid] = None

    return rules