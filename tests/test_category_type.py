"""REQ-5002: Kategorie-Typ (Ursache/Wirkung) Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).
"""
import time

import pytest

from app.database import SessionLocal
from app.models import Category, Project
from app.schemas import VALID_CATEGORY_TYPES


class TestCategoryTypeModel:
    """Tests fuer das category_type Feld im Category-Model."""

    def test_new_category_has_default_category_type(self):
        """Neue Kategorie hat Default category_type='standard'."""
        db = SessionLocal()
        try:
            project = Project(name="TestProject_Default")
            db.add(project)
            db.commit()
            db.refresh(project)

            cat = Category(
                project_id=project.id,
                name="TestCategory",
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)

            assert cat.category_type == "standard"
        finally:
            db.rollback()
            db.delete(project) if project.id else None
            db.commit()
            db.close()

    def test_category_can_be_created_as_cause(self):
        """Kategorie kann als 'cause' erstellt werden."""
        db = SessionLocal()
        try:
            project = Project(name="TestProject_Cause")
            db.add(project)
            db.commit()
            db.refresh(project)

            cat = Category(
                project_id=project.id,
                name="Ursache1",
                category_type="cause",
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)

            assert cat.category_type == "cause"
        finally:
            db.rollback()
            db.delete(project) if project.id else None
            db.commit()
            db.close()

    def test_category_can_be_created_as_effect(self):
        """Kategorie kann als 'effect' erstellt werden."""
        db = SessionLocal()
        try:
            project = Project(name="TestProject_Effect")
            db.add(project)
            db.commit()
            db.refresh(project)

            cat = Category(
                project_id=project.id,
                name="Wirkung1",
                category_type="effect",
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)

            assert cat.category_type == "effect"
        finally:
            db.rollback()
            db.delete(project) if project.id else None
            db.commit()
            db.close()

    def test_category_type_can_be_changed(self):
        """Kategorie-Typ kann geaendert werden."""
        db = SessionLocal()
        try:
            project = Project(name="TestProject_Change")
            db.add(project)
            db.commit()
            db.refresh(project)

            cat = Category(
                project_id=project.id,
                name="TestCategory",
                category_type="standard",
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)

            assert cat.category_type == "standard"

            # Aendere zu 'cause'
            cat.category_type = "cause"
            db.commit()
            db.refresh(cat)

            assert cat.category_type == "cause"

            # Aendere zu 'effect'
            cat.category_type = "effect"
            db.commit()
            db.refresh(cat)

            assert cat.category_type == "effect"
        finally:
            db.rollback()
            db.delete(project) if project.id else None
            db.commit()
            db.close()


class TestCategoryTypeSchema:
    """Tests fuer die Schema-Validierung von category_type."""

    def test_valid_category_types(self):
        """Alle gueltigen Typen werden akzeptiert."""
        from app.schemas import CategoryCreate

        for ctype in VALID_CATEGORY_TYPES:
            schema = CategoryCreate(name="Test", category_type=ctype)
            assert schema.category_type == ctype

    def test_invalid_category_type_rejected(self):
        """Ungueltiger Typ wird abgelehnt."""
        from app.schemas import CategoryCreate

        with pytest.raises(Exception):  # Pydantic ValidationError
            CategoryCreate(name="Test", category_type="invalid_type")

    def test_invalid_category_type_update_rejected(self):
        """Ungueltiger Typ in Update wird abgelehnt."""
        from app.schemas import CategoryUpdate

        with pytest.raises(Exception):  # Pydantic ValidationError
            CategoryUpdate(category_type="invalid_type")

    def test_category_update_allows_none(self):
        """CategoryUpdate erlaubt None fuer category_type."""
        from app.schemas import CategoryUpdate

        schema = CategoryUpdate(category_type=None)
        assert schema.category_type is None

    def test_category_update_valid_type(self):
        """CategoryUpdate akzeptiert gueltige Typen."""
        from app.schemas import CategoryUpdate

        schema = CategoryUpdate(category_type="cause")
        assert schema.category_type == "cause"


class TestCategoryTypeAPI:
    """API-Tests fuer category_type via REST-Endpunkte."""

    def _unique_suffix(self) -> str:
        return f"{int(time.time() * 1000000)}"

    def test_create_category_with_cause_type(self, auth_client):
        """POST /projects/{pid}/categories mit category_type='cause'."""
        suffix = self._unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_Cause_Test_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        resp = auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Ursache1_{suffix}", "category_type": "cause"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["category_type"] == "cause"

    def test_create_category_with_effect_type(self, auth_client):
        """POST /projects/{pid}/categories mit category_type='effect'."""
        suffix = self._unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_Effect_Test_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        resp = auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Wirkung1_{suffix}", "category_type": "effect"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["category_type"] == "effect"

    def test_create_category_default_standard(self, auth_client):
        """POST /projects/{pid}/categories ohne category_type -> 'standard'."""
        suffix = self._unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_Default_Test_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        resp = auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"StandardCat_{suffix}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["category_type"] == "standard"

    def test_create_category_invalid_type_rejected(self, auth_client):
        """POST /projects/{pid}/categories mit ungueltigem category_type -> 422."""
        suffix = self._unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_Invalid_Test_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        resp = auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"BadCat_{suffix}", "category_type": "invalid"},
        )
        assert resp.status_code == 422, resp.text

    def test_list_categories_includes_category_type(self, auth_client):
        """GET /projects/{pid}/categories inkludiert category_type."""
        suffix = self._unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_List_Test_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Ursache_{suffix}", "category_type": "cause"},
        )
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Wirkung_{suffix}", "category_type": "effect"},
        )

        resp = auth_client.get(f"/api/projects/{pid}/categories")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) == 2
        types = {c["category_type"] for c in data}
        assert "cause" in types
        assert "effect" in types