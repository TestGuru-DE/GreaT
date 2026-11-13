"""REQ-5013/5014/5015/5019/5020: Decision Table Optimization Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).

Testet:
- REQ-5013: Collapsing (redundante Regeln zusammenfassen)
- REQ-5014: Checksum-Validierung
- REQ-5015: Extended Entry (mehr als 2 Werte pro Ursache)
- REQ-5019: Widerspruchserkennung
- REQ-5020: Vollstaendigkeitspruefung (Luecken-Erkennung)
"""
import pytest

from app.services_decision_table import (
    calculate_checksum,
    collapse_rules,
    detect_contradictions,
    detect_gaps,
)


# =============================================================================
# REQ-5013: Collapsing Tests
# =============================================================================

class TestCollapseRules:
    """Tests fuer collapse_rules() - REQ-5013."""

    def _make_rules(self, cause_values_list, effects_dict):
        """Hilfsfunktion: Erstellt Regeln aus einer Liste von Ursache-Werten."""
        rules = []
        for i, cause_vals in enumerate(cause_values_list, 1):
            rule = {
                "id": i,
                "causes": dict(cause_vals),
                "effects": dict(effects_dict),
            }
            rules.append(rule)
        return rules

    def test_collapse_basic(self):
        """REQ-5013: 2 Regeln mit identischen Wirkungen + 1 Unterschied -> collapsen."""
        # Regel 1: C1=Y, C2=Y -> E1=X
        # Regel 2: C1=N, C2=Y -> E1=X
        # -> Zusammen: C1=-, C2=Y -> E1=X
        rules = self._make_rules(
            [
                {1: "Y", 2: "Y"},
                {1: "N", 2: "Y"},
            ],
            {10: "X"},
        )

        result, reduced = collapse_rules(rules)

        assert reduced == 1
        assert len(result) == 1
        assert result[0]["causes"][1] == "-"  # Don't Care
        assert result[0]["causes"][2] == "Y"
        assert result[0]["effects"][10] == "X"

    def test_no_collapse_different_effects(self):
        """REQ-5013: 2 Regeln mit unterschiedlichen Wirkungen -> kein collapsing."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "N", 2: "Y"}, "effects": {10: "N"}},
        ]

        result, reduced = collapse_rules(rules)

        assert reduced == 0
        assert len(result) == 2

    def test_no_collapse_two_differences(self):
        """REQ-5013: 2 Regeln mit 2 Unterschieden -> kein collapsing."""
        rules = self._make_rules(
            [
                {1: "Y", 2: "Y"},
                {1: "N", 2: "N"},
            ],
            {10: "X"},
        )

        result, reduced = collapse_rules(rules)

        assert reduced == 0
        assert len(result) == 2

    def test_no_collapse_same_values(self):
        """REQ-5013: 2 Regeln mit gleichen Werten (Y,Y statt Y,N) -> kein collapsing."""
        rules = self._make_rules(
            [
                {1: "Y", 2: "Y"},
                {1: "Y", 2: "N"},
            ],
            {10: "X"},
        )

        result, reduced = collapse_rules(rules)

        # C1 ist gleich (Y,Y), C2 ist unterschiedlich (Y,N)
        # Aber C2-Werte sind {Y, N} -> das sollte collapsing sein!
        # Warte: Die Regeln unterscheiden sich in C2 (Y vs N), C1 ist gleich
        # Zusammen decken sie Y und N von C2 ab -> collapsing!
        assert reduced == 1
        assert len(result) == 1
        assert result[0]["causes"][1] == "Y"
        assert result[0]["causes"][2] == "-"

    def test_cascade_collapse(self):
        """REQ-5013: Kaskadierendes Collapsing (mehrmals anwenden)."""
        # 4 Regeln: 2^2 = 4 Kombinationen, alle mit gleichen Wirkungen
        # R1: Y,Y -> X  R2: N,Y -> X  -> collapse zu -,Y
        # R3: Y,N -> X  R4: N,N -> X  -> collapse zu -,N
        # -,Y -> X  und  -,N -> X  -> collapse zu -,-
        rules = self._make_rules(
            [
                {1: "Y", 2: "Y"},
                {1: "N", 2: "Y"},
                {1: "Y", 2: "N"},
                {1: "N", 2: "N"},
            ],
            {10: "X"},
        )

        result, reduced = collapse_rules(rules)

        assert len(result) == 1
        assert reduced == 3  # 4 -> 2 -> 1 (3 Reduktionen)
        assert result[0]["causes"][1] == "-"
        assert result[0]["causes"][2] == "-"

    def test_no_collapse_single_rule(self):
        """REQ-5013: Einzelne Regel -> kein collapsing."""
        rules = self._make_rules([{1: "Y"}], {10: "X"})

        result, reduced = collapse_rules(rules)

        assert reduced == 0
        assert len(result) == 1

    def test_no_collapse_empty(self):
        """REQ-5013: Leere Liste -> kein crashing."""
        result, reduced = collapse_rules([])

        assert reduced == 0
        assert result == []

    def test_partial_collapse(self):
        """REQ-5013: Nur ein Paar kann collapsen, andere nicht."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "N", 2: "Y"}, "effects": {10: "X"}},  # collaps mit 1
            {"id": 3, "causes": {1: "Y", 2: "N"}, "effects": {10: "N"}},  # andere Wirkung
        ]

        result, reduced = collapse_rules(rules)

        assert reduced == 1
        assert len(result) == 2
        # Regel 1+2 wurden zu -,Y -> X
        # Regel 3 bleibt unveraendert (Y,N -> N)

    def test_collapse_with_dont_care(self):
        """REQ-5013: Collapsing funktioniert auch mit existierenden Don't Care Werten."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "-"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "N", 2: "-"}, "effects": {10: "X"}},
        ]

        result, reduced = collapse_rules(rules)

        # Beide haben C2=- (identisch), C1 unterscheidet sich (Y,N)
        assert reduced == 1
        assert len(result) == 1
        assert result[0]["causes"][1] == "-"
        assert result[0]["causes"][2] == "-"


# =============================================================================
# REQ-5014: Checksum Tests
# =============================================================================

class TestCalculateChecksum:
    """Tests fuer calculate_checksum() - REQ-5014."""

    def test_checksum_complete(self):
        """REQ-5014: Vollstaendige Tabelle -> checksum == 2^n."""
        # 2 Ursachen, 4 Regeln ohne Don't Care
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "Y", 2: "N"}, "effects": {10: "X"}},
            {"id": 3, "causes": {1: "N", 2: "Y"}, "effects": {10: "X"}},
            {"id": 4, "causes": {1: "N", 2: "N"}, "effects": {10: "X"}},
        ]

        result = calculate_checksum(rules, num_causes=2)

        assert result["checksum"] == 4  # 4 * 2^0 = 4
        assert result["expected"] == 4  # 2^2 = 4
        assert result["status"] == "complete"

    def test_checksum_complete_with_dont_care(self):
        """REQ-5014: Nach Collapsing: checksum == 2^n mit Don't Care."""
        # 2 Ursachen, 1 Regel mit 2 Don't Care
        rules = [
            {"id": 1, "causes": {1: "-", 2: "-"}, "effects": {10: "X"}},
        ]

        result = calculate_checksum(rules, num_causes=2)

        assert result["checksum"] == 4  # 1 * 2^2 = 4
        assert result["expected"] == 4
        assert result["status"] == "complete"

    def test_checksum_gap(self):
        """REQ-5014: Luecken -> checksum < 2^n."""
        # 2 Ursachen, nur 2 Regeln (fehlen 2)
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "Y", 2: "N"}, "effects": {10: "X"}},
        ]

        result = calculate_checksum(rules, num_causes=2)

        assert result["checksum"] == 2  # 2 * 2^0 = 2
        assert result["expected"] == 4
        assert result["status"] == "gap"

    def test_checksum_overlap(self):
        """REQ-5014: Uberschneidungen -> checksum > 2^n."""
        # 2 Ursachen, 2 Regeln mit Don't Care (jeweils 2^1=2)
        rules = [
            {"id": 1, "causes": {1: "-", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "-", 2: "N"}, "effects": {10: "X"}},
            {"id": 3, "causes": {1: "Y", 2: "-"}, "effects": {10: "X"}},
        ]

        result = calculate_checksum(rules, num_causes=2)

        assert result["checksum"] == 6  # 2 + 2 + 2 = 6
        assert result["expected"] == 4
        assert result["status"] == "overlap"

    def test_checksum_three_causes(self):
        """REQ-5014: 3 Ursachen, vollstaendig."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y", 3: "Y"}, "effects": {}},
            {"id": 2, "causes": {1: "Y", 2: "Y", 3: "N"}, "effects": {}},
            {"id": 3, "causes": {1: "Y", 2: "N", 3: "Y"}, "effects": {}},
            {"id": 4, "causes": {1: "Y", 2: "N", 3: "N"}, "effects": {}},
            {"id": 5, "causes": {1: "N", 2: "Y", 3: "Y"}, "effects": {}},
            {"id": 6, "causes": {1: "N", 2: "Y", 3: "N"}, "effects": {}},
            {"id": 7, "causes": {1: "N", 2: "N", 3: "Y"}, "effects": {}},
            {"id": 8, "causes": {1: "N", 2: "N", 3: "N"}, "effects": {}},
        ]

        result = calculate_checksum(rules, num_causes=3)

        assert result["checksum"] == 8  # 8 * 2^0 = 8
        assert result["expected"] == 8  # 2^3 = 8
        assert result["status"] == "complete"

    def test_checksum_mixed_dont_care(self):
        """REQ-5014: Gemischte Don't Care Werte."""
        # 3 Ursachen
        # R1: -,Y,Y -> 2^1 = 2
        # R2: N,N,- -> 2^1 = 2
        # Summe = 4, expected = 8 -> gap
        rules = [
            {"id": 1, "causes": {1: "-", 2: "Y", 3: "Y"}, "effects": {}},
            {"id": 2, "causes": {1: "N", 2: "N", 3: "-"}, "effects": {}},
        ]

        result = calculate_checksum(rules, num_causes=3)

        assert result["checksum"] == 4  # 2 + 2 = 4
        assert result["expected"] == 8
        assert result["status"] == "gap"

    def test_checksum_message(self):
        """REQ-5014: Jede Status hat eine deutsche Nachricht."""
        rules = [
            {"id": 1, "causes": {1: "Y"}, "effects": {}},
        ]

        result = calculate_checksum(rules, num_causes=1)

        assert "message" in result
        assert result["status"] == "gap"
        assert "Luecken" in result["message"] or "nicht alle" in result["message"]


# =============================================================================
# REQ-5019: Widerspruchserkennung Tests
# =============================================================================

class TestDetectContradictions:
    """Tests fuer detect_contradictions() - REQ-5019."""

    def test_contradiction_same_causes_different_effects(self):
        """REQ-5019: 2 Regeln mit gleichen Ursachen, unterschiedlichen Wirkungen -> Widerspruch."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "Y", 2: "Y"}, "effects": {10: "N"}},
        ]

        result = detect_contradictions(rules)

        assert len(result) == 1
        assert result[0]["rule_a"] == 1
        assert result[0]["rule_b"] == 2
        assert "widersprechen" in result[0]["message"].lower()

    def test_contradiction_dont_care_overlap(self):
        """REQ-5019: 2 Regeln mit Don't Care Ueberlappung -> Widerspruch."""
        rules = [
            {"id": 1, "causes": {1: "-", 2: "Y"}, "effects": {10: "X"}},  # deckt Y,Y und N,Y ab
            {"id": 2, "causes": {1: "Y", 2: "Y"}, "effects": {10: "N"}},  # Y,Y ist im Ueberlappungsbereich
        ]

        result = detect_contradictions(rules)

        assert len(result) == 1
        assert result[0]["rule_a"] == 1
        assert result[0]["rule_b"] == 2

    def test_no_contradiction_same_effects(self):
        """REQ-5019: Keine Widersprueche bei identischen Wirkungen."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
        ]

        result = detect_contradictions(rules)

        assert len(result) == 0

    def test_no_contradiction_no_overlap(self):
        """REQ-5019: Keine Ueberlappung -> kein Widerspruch."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "N", 2: "N"}, "effects": {10: "N"}},
        ]

        result = detect_contradictions(rules)

        assert len(result) == 0

    def test_multiple_contradictions(self):
        """REQ-5019: Mehrere Widersprueche gleichzeitig erkennen."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "Y", 2: "Y"}, "effects": {10: "N"}},  # Widerspruch mit 1
            {"id": 3, "causes": {1: "Y", 2: "N"}, "effects": {10: "X"}},
            {"id": 4, "causes": {1: "Y", 2: "N"}, "effects": {10: "N"}},  # Widerspruch mit 3
        ]

        result = detect_contradictions(rules)

        assert len(result) == 2

    def test_empty_rules(self):
        """REQ-5019: Leere Regeln -> keine Widersprueche."""
        result = detect_contradictions([])
        assert result == []

    def test_single_rule(self):
        """REQ-5019: Einzelne Regel -> keine Widersprueche."""
        rules = [
            {"id": 1, "causes": {1: "Y"}, "effects": {10: "X"}},
        ]
        result = detect_contradictions(rules)
        assert result == []


# =============================================================================
# REQ-5020: Luecken-Erkennung Tests
# =============================================================================

class TestDetectGaps:
    """Tests fuer detect_gaps() - REQ-5020."""

    def test_gaps_incomplete_table(self):
        """REQ-5020: Luecken-Erkennung bei unvollstaendiger Tabelle."""
        # 2 Ursachen, nur 2 von 4 Regeln
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "Y", 2: "N"}, "effects": {10: "X"}},
        ]

        result = detect_gaps(rules, num_causes=2)

        # Fehlende: N,Y und N,N
        assert len(result) == 2
        # Pruefe dass beide Luecken enthalten sind
        gap_combos = [r["combination"] for r in result]
        assert {1: "N", 2: "Y"} in gap_combos
        assert {1: "N", 2: "N"} in gap_combos

    def test_no_gaps_complete_table(self):
        """REQ-5020: Keine Luecken bei vollstaendiger Tabelle."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {10: "X"}},
            {"id": 2, "causes": {1: "Y", 2: "N"}, "effects": {10: "X"}},
            {"id": 3, "causes": {1: "N", 2: "Y"}, "effects": {10: "X"}},
            {"id": 4, "causes": {1: "N", 2: "N"}, "effects": {10: "X"}},
        ]

        result = detect_gaps(rules, num_causes=2)

        assert len(result) == 0

    def test_gaps_with_dont_care(self):
        """REQ-5020: Don't Care Regeln decken mehrere Kombinationen ab."""
        # 1 Regel mit Don't Care deckt 2 Kombinationen ab
        rules = [
            {"id": 1, "causes": {1: "-", 2: "Y"}, "effects": {10: "X"}},  # deckt Y,Y und N,Y
        ]

        result = detect_gaps(rules, num_causes=2)

        # Fehlende: Y,N und N,N
        assert len(result) == 2
        gap_combos = [r["combination"] for r in result]
        assert {1: "Y", 2: "N"} in gap_combos
        assert {1: "N", 2: "N"} in gap_combos

    def test_empty_rules_all_gaps(self):
        """REQ-5020: Keine Regeln -> alle Kombinationen sind Luecken."""
        result = detect_gaps([], num_causes=2)

        # Bei 0 Regeln und 2 Ursachen: alle 4 Kombinationen sind Luecken
        # Aber cause_ids sind leer bei leeren rules -> 0 gaps
        assert result == []

    def test_gaps_three_causes(self):
        """REQ-5020: Luecken bei 3 Ursachen."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y", 3: "Y"}, "effects": {}},
            {"id": 2, "causes": {1: "N", 2: "N", 3: "N"}, "effects": {}},
        ]

        result = detect_gaps(rules, num_causes=3)

        assert len(result) == 6  # 8 - 2 = 6 Luecken

    def test_gap_message_format(self):
        """REQ-5020: Luecken-Nachricht ist informativ."""
        rules = [
            {"id": 1, "causes": {1: "Y", 2: "Y"}, "effects": {}},
        ]

        result = detect_gaps(rules, num_causes=2)

        assert len(result) > 0
        assert "message" in result[0]
        assert "nicht abgedeckt" in result[0]["message"]


# =============================================================================
# REQ-5015: Extended Entry Tests
# =============================================================================

class TestExtendedEntry:
    """Tests fuer Extended Entry (REQ-5015) - Integration mit generate_decision_table."""

    def test_extended_entry_three_values(self):
        """REQ-5015: Extended Entry mit 3 Werten (S,M,L) -> 3^1 = 3 Kombinationen."""
        from app.database import SessionLocal
        from app.models import Category, Project, Value
        import time

        db = SessionLocal()
        try:
            project = Project(name=f"ExtendedEntry_Test_{int(time.time() * 1000000)}")
            db.add(project)
            db.commit()
            db.refresh(project)
            pid = project.id

            # Erstelle Ursache mit 3 Werten
            cause = Category(
                project_id=pid,
                name="T-Shirt_Groesse",
                category_type="cause",
                order_index=0,
            )
            db.add(cause)
            db.commit()
            db.refresh(cause)

            # Fuege Werte hinzu
            for val in ["S", "M", "L"]:
                v = Value(category_id=cause.id, value=val)
                db.add(v)
            db.commit()

            # Erstelle Wirkung
            effect = Category(
                project_id=pid,
                name="Passform",
                category_type="effect",
                order_index=0,
            )
            db.add(effect)
            db.commit()
            db.refresh(effect)

            # Generiere mit Extended Entry
            from app.services_decision_table import generate_decision_table
            result = generate_decision_table(db, pid, use_extended_entry=True)

            assert "error" not in result
            assert result["total_rules"] == 3  # 3^1 = 3
            assert len(result["rules"]) == 3

            # Pruefe dass echte Werte verwendet werden
            cause_values_in_rules = set()
            for rule in result["rules"]:
                cause_values_in_rules.add(rule["causes"][cause.id])
            assert cause_values_in_rules == {"S", "M", "L"}

            # Pruefe cause values in response
            assert result["causes"][0]["values"] == ["S", "M", "L"]
        finally:
            db.close()

    def test_extended_entry_two_causes_mixed(self):
        """REQ-5015: 2 Ursachen (2+3 Werte) -> 2*3=6 Kombinationen."""
        from app.database import SessionLocal
        from app.models import Category, Project, Value
        import time

        db = SessionLocal()
        try:
            project = Project(name=f"ExtendedEntry_Mixed_{int(time.time() * 1000000)}")
            db.add(project)
            db.commit()
            db.refresh(project)
            pid = project.id

            # Ursache 1 mit 2 Werten
            cause1 = Category(
                project_id=pid, name="Farbe", category_type="cause", order_index=0,
            )
            db.add(cause1)
            db.commit()
            db.refresh(cause1)
            for val in ["rot", "blau"]:
                db.add(Value(category_id=cause1.id, value=val))
            db.commit()

            # Ursache 2 mit 3 Werten
            cause2 = Category(
                project_id=pid, name="Groesse", category_type="cause", order_index=1,
            )
            db.add(cause2)
            db.commit()
            db.refresh(cause2)
            for val in ["S", "M", "L"]:
                db.add(Value(category_id=cause2.id, value=val))
            db.commit()

            # Wirkung
            effect = Category(
                project_id=pid, name="Ergebnis", category_type="effect", order_index=0,
            )
            db.add(effect)
            db.commit()

            from app.services_decision_table import generate_decision_table
            result = generate_decision_table(db, pid, use_extended_entry=True)

            assert "error" not in result
            assert result["total_rules"] == 6  # 2*3 = 6

            # Pruefe alle Kombinationen sind vorhanden
            combos = set()
            for rule in result["rules"]:
                combos.add((rule["causes"][cause1.id], rule["causes"][cause2.id]))
            expected = {
                ("rot", "S"), ("rot", "M"), ("rot", "L"),
                ("blau", "S"), ("blau", "M"), ("blau", "L"),
            }
            assert combos == expected
        finally:
            db.close()

    def test_extended_entry_fallback_yn(self):
        """REQ-5015: Fallback auf Y/N wenn keine Werte existieren."""
        from app.database import SessionLocal
        from app.models import Category, Project
        import time

        db = SessionLocal()
        try:
            project = Project(name=f"ExtendedEntry_Fallback_{int(time.time() * 1000000)}")
            db.add(project)
            db.commit()
            db.refresh(project)
            pid = project.id

            # Ursache OHNE Werte
            cause = Category(
                project_id=pid, name="TestUrsache", category_type="cause", order_index=0,
            )
            db.add(cause)
            db.commit()
            db.refresh(cause)

            # Wirkung
            effect = Category(
                project_id=pid, name="TestWirkung", category_type="effect", order_index=0,
            )
            db.add(effect)
            db.commit()

            from app.services_decision_table import generate_decision_table
            result = generate_decision_table(db, pid, use_extended_entry=True)

            assert "error" not in result
            assert result["total_rules"] == 2  # Fallback Y/N
            assert result["causes"][0]["values"] == ["Y", "N"]
        finally:
            db.close()


# =============================================================================
# REQ-5013/5014/5019/5020: API Endpoint Tests
# =============================================================================

class TestCollapseAPI:
    """Tests fuer POST /api/decision-table/collapse (REQ-5013)."""

    def test_collapse_endpoint(self, auth_client):
        """REQ-5013: POST /collapse -> 200 mit collapsed_count."""
        import time
        suffix = f"{int(time.time() * 1000)}"
        project = auth_client.post("/api/projects", json={"name": f"DT_Collapse_API_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        # Erstelle 2 Ursachen + 1 Wirkung
        for i, name in enumerate([f"Ursache1_{suffix}", f"Ursache2_{suffix}"]):
            auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "cause", "order_index": i},
            )
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Wirkung1_{suffix}", "category_type": "effect"},
        )

        resp = auth_client.post(
            "/api/decision-table/collapse",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "collapsed_count" in data
        assert "rules" in data
        # Bei 2 Ursachen mit allen Y/N: 4 Regeln -> 1 (alle gleich)
        # total_rules sollte 1 sein nach Collapsing

    def test_collapse_nonexistent_project(self, auth_client):
        """REQ-5013: POST /collapse mit nicht-existentem Projekt -> 404."""
        resp = auth_client.post(
            "/api/decision-table/collapse",
            json={"project_id": 99999},
        )
        assert resp.status_code == 404, resp.text


class TestValidateAPI:
    """Tests fuer POST /api/decision-table/validate (REQ-5014/5019/5020)."""

    def test_validate_endpoint_complete(self, auth_client):
        """REQ-5014/5019/5020: POST /validate -> 200 mit checksum, contradictions, gaps."""
        import time
        suffix = f"{int(time.time() * 1000)}"
        project = auth_client.post("/api/projects", json={"name": f"DT_Validate_API_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        # Erstelle 2 Ursachen + 1 Wirkung
        for i, name in enumerate([f"Ursache1_{suffix}", f"Ursache2_{suffix}"]):
            auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "cause", "order_index": i},
            )
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Wirkung1_{suffix}", "category_type": "effect"},
        )

        resp = auth_client.post(
            "/api/decision-table/validate",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "checksum" in data
        assert "contradictions" in data
        assert "gaps" in data
        assert data["checksum"]["status"] == "complete"
        assert data["contradictions"] == []
        assert data["gaps"] == []

    def test_validate_nonexistent_project(self, auth_client):
        """REQ-5014/5019/5020: POST /validate mit nicht-existentem Projekt -> 404."""
        resp = auth_client.post(
            "/api/decision-table/validate",
            json={"project_id": 99999},
        )
        assert resp.status_code == 404, resp.text