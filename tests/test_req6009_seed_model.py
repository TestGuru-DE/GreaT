"""
REQ-6009: Tests fuer Seed-Modell, Validierung, CSV-Parsing.

Testet:
- SeedSet-Modell (CRUD, CASCADE, Max-Grenze)
- Seed-Validierung (unbekannte Werte, Duplikate, etc.)
- CSV-Parsing (leere Zellen, BOM, Trennzeichen)
"""
import pytest
import json


# ---------------------------------------------------------------------------
# MOCK-DATEN
# ---------------------------------------------------------------------------

CATS_2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
}


# ---------------------------------------------------------------------------
# TestSeedSetModel
# ---------------------------------------------------------------------------

class TestSeedSetModel:

    def test_seed_set_created_with_name(self, db_session):
        """TEST-REQ-6009-MDL-001: SeedSet mit Name + Seeds anlegen."""
        from app.models import Project
        from app.models.seed import SeedSet, SeedCase

        project = Project(name="ModelTestProject")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        seed_set = SeedSet(project_id=project.id, name="Meine Seeds")
        db_session.add(seed_set)
        db_session.flush()

        sc = SeedCase(
            seed_set_id=seed_set.id,
            assignment_json=json.dumps({"A": "a1", "B": "b1"}),
            order_index=0,
        )
        db_session.add(sc)
        db_session.commit()

        # Lesen
        ss = db_session.query(SeedSet).filter(SeedSet.id == seed_set.id).first()
        assert ss is not None
        assert ss.name == "Meine Seeds"
        assert len(ss.seed_cases) == 1

    def test_multiple_seed_sets_per_project(self, db_session):
        """TEST-REQ-6009-MDL-002: 3 SeedSets mit gleichem project_id."""
        from app.models import Project
        from app.models.seed import SeedSet

        project = Project(name="MultiSetProject")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        for i in range(3):
            db_session.add(SeedSet(project_id=project.id, name=f"Set{i}"))
        db_session.commit()

        count = db_session.query(SeedSet).filter(
            SeedSet.project_id == project.id
        ).count()
        assert count == 3

    def test_seed_set_zero_seeds_allowed(self, db_session):
        """TEST-REQ-6009-MDL-006: Leerer Satz erlaubt."""
        from app.models import Project
        from app.models.seed import SeedSet

        project = Project(name="EmptySetProject")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        seed_set = SeedSet(project_id=project.id, name="Empty")
        db_session.add(seed_set)
        db_session.commit()

        ss = db_session.query(SeedSet).filter(SeedSet.id == seed_set.id).first()
        assert ss is not None
        assert len(ss.seed_cases) == 0

    def test_seed_deleted_with_project(self, db_session):
        """TEST-REQ-6009-MDL-007: Project loeschen -> SeedSets CASCADE."""
        from app.models import Project
        from app.models.seed import SeedSet, SeedCase

        project = Project(name="CascadeProject")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        seed_set = SeedSet(project_id=project.id, name="CascadeSet")
        db_session.add(seed_set)
        db_session.flush()

        sc = SeedCase(
            seed_set_id=seed_set.id,
            assignment_json=json.dumps({"A": "a1"}),
            order_index=0,
        )
        db_session.add(sc)
        db_session.commit()

        # Projekt loeschen
        db_session.delete(project)
        db_session.commit()

        # SeedSets sollten CASCADE-geloestcht sein
        ss = db_session.query(SeedSet).filter(SeedSet.id == seed_set.id).first()
        assert ss is None


# ---------------------------------------------------------------------------
# TestSeedValidation
# ---------------------------------------------------------------------------

class TestSeedValidation:

    def test_seed_unknown_category_rejected(self):
        """TEST-REQ-6009-VAL-001: Unbekannte Kategorie -> Warnung."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"UnknownCat": "val", "A": "a1", "B": "b1"}]
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert any("Unbekannte Kategorie" in w for w in warnings)

    def test_seed_unknown_value_reported(self):
        """TEST-REQ-6009-VAL-002: Unbekannter Wert -> Warnung."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"A": "unknown_value", "B": "b1"}]
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert any("nicht in Kategorie" in w for w in warnings)

    def test_seed_empty_string_treated_as_any(self):
        """TEST-REQ-6009-VAL-003: "" -> None."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"A": "", "B": "b1"}]
        normalized, _ = validate_seeds(seeds, CATS_2X2)

        assert normalized[0]["A"] is None

    def test_seed_missing_category_treated_as_any(self):
        """TEST-REQ-6009-VAL-004: Fehlende Kategorie -> None."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"A": "a1"}]
        normalized, _ = validate_seeds(seeds, CATS_2X2)

        assert normalized[0]["B"] is None

    def test_seed_duplicate_detection(self):
        """TEST-REQ-6009-VAL-005: Duplikate entfernt + Warnung."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [
            {"A": "a1", "B": "b1"},
            {"A": "a1", "B": "b1"},
            {"A": "a2", "B": "b2"},
        ]
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert len(normalized) == 2
        assert any("dupliziert" in w.lower() for w in warnings)


# ---------------------------------------------------------------------------
# TestCSVSeedImport
# ---------------------------------------------------------------------------

class TestCSVSeedImport:

    def test_csv_import_basic(self):
        """TEST-REQ-6009-CSV-001: 3 Seeds, alle gueltig."""
        from app.services_seed import parse_csv_seeds

        csv_text = "A,B\na1,b1\na2,b2\na1,b2\n"
        seeds, warnings = parse_csv_seeds(csv_text, CATS_2X2)

        assert len(seeds) == 3
        assert seeds[0] == {"A": "a1", "B": "b1"}

    def test_csv_import_empty_cell_as_any(self):
        """TEST-REQ-6009-CSV-003: Leere Zelle -> None."""
        from app.services_seed import parse_csv_seeds

        csv_text = "A,B\na1,\n,b1\n,\n"
        seeds, warnings = parse_csv_seeds(csv_text, CATS_2X2)

        assert len(seeds) == 3
        assert seeds[0]["B"] is None
        assert seeds[1]["A"] is None
        assert seeds[2]["A"] is None
        assert seeds[2]["B"] is None

    def test_csv_import_empty_file(self):
        """TEST-REQ-6009-CSV-005: Leere CSV -> 0 Seeds."""
        from app.services_seed import parse_csv_seeds

        seeds, warnings = parse_csv_seeds("", CATS_2X2)
        assert len(seeds) == 0

    def test_csv_import_header_only(self):
        """TEST-REQ-6009-CSV-006: Nur Header -> 0 Seeds."""
        from app.services_seed import parse_csv_seeds

        seeds, warnings = parse_csv_seeds("A,B\n", CATS_2X2)
        assert len(seeds) == 0

    def test_csv_import_unknown_value_warning(self):
        """TEST-REQ-6009-CSV-002: Unbekannter Wert -> Warnung."""
        from app.services_seed import parse_csv_seeds

        csv_text = "A,B\na1,b_unknown\n"
        seeds, warnings = parse_csv_seeds(csv_text, CATS_2X2)

        assert any("nicht in Kategorie" in w for w in warnings)

    def test_csv_import_unknown_column_warning(self):
        """TEST-REQ-6009-CSV-004: Unbekannte Spalte -> Warnung."""
        from app.services_seed import parse_csv_seeds

        csv_text = "A,B,UnknownCol\na1,b1,foo\n"
        seeds, warnings = parse_csv_seeds(csv_text, CATS_2X2)

        assert any("Unbekannte Spalte" in w for w in warnings)

    def test_csv_import_special_characters(self):
        """TEST-REQ-6009-CSV-007: Umlaute, Sonderzeichen."""
        from app.services_seed import parse_csv_seeds

        cats_special = {
            "A": ["a1", "a\u00fcber"],
            "B": ["b1", "b\u00f6"],
        }

        csv_text = "A,B\na\u00fcber,b\u00f6\n"
        seeds, warnings = parse_csv_seeds(csv_text, cats_special)

        assert len(seeds) == 1
        assert seeds[0]["A"] == "a\u00fcber"
        assert seeds[0]["B"] == "b\u00f6"

    def test_csv_import_semicolon_delimiter(self):
        """E10: Semikolon-Trennzeichen erkennen."""
        from app.services_seed import parse_csv_seeds

        csv_text = "A;B\na1;b1\na2;b2\n"
        seeds, warnings = parse_csv_seeds(csv_text, CATS_2X2)

        assert len(seeds) == 2
        assert seeds[0] == {"A": "a1", "B": "b1"}

    def test_csv_import_bom(self):
        """E9: UTF-8-BOM wird ignoriert."""
        from app.services_seed import parse_csv_seeds

        csv_text = "\ufeffA,B\na1,b1\n"
        seeds, warnings = parse_csv_seeds(csv_text, CATS_2X2)

        assert len(seeds) == 1
        assert seeds[0] == {"A": "a1", "B": "b1"}