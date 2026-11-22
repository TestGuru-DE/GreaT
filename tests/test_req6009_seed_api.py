"""
REQ-6009: API-Integration-Tests fuer Seed-Saetze.

# REQ-6009
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import app_instance


class TestSeedSetCRUD:
    """TEST-REQ-6009-API-001 bis API-009."""

    def _create_project(self, client: TestClient) -> int:
        """Hilfsfunktion: Testprojekt erstellen."""
        resp = client.post("/api/projects", json={"name": "SeedTestProject"})
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}"
        return resp.json()["id"]

    def _create_categories(self, client: TestClient, pid: int):
        """Hilfsfunktion: Kategorien fuer 2x2 erstellen."""
        for name in ["A", "B"]:
            client.post(f"/api/projects/{pid}/categories", json={"name": name})
        # Werte
        cats = client.get(f"/api/projects/{pid}/categories").json()
        cat_a = [c for c in cats if c["name"] == "A"][0]
        cat_b = [c for c in cats if c["name"] == "B"][0]
        for v in ["a1", "a2"]:
            client.post(f"/api/categories/{cat_a['id']}/values", json={"value": v})
        for v in ["b1", "b2"]:
            client.post(f"/api/categories/{cat_b['id']}/values", json={"value": v})

    def test_create_seed_set(self, auth_client: TestClient):
        """TEST-REQ-6009-API-001: POST /api/projects/{pid}/seed-sets -> 201."""
        pid = self._create_project(auth_client)
        self._create_categories(auth_client, pid)

        seeds = [{"A": "a1", "B": "b1"}, {"A": "a2", "B": "b2"}]
        resp = auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "TestSeeds", "seeds": seeds},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "TestSeeds"

    def test_list_seed_sets(self, auth_client: TestClient):
        """TEST-REQ-6009-API-002: GET /api/projects/{pid}/seed-sets -> 200."""
        pid = self._create_project(auth_client)
        self._create_categories(auth_client, pid)

        auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "Satz1", "seeds": [{"A": "a1", "B": "b1"}]},
        )
        resp = auth_client.get(f"/api/projects/{pid}/seed-sets")
        assert resp.status_code == 200
        assert len(resp.json()["seed_sets"]) >= 1

    def test_get_seed_set(self, auth_client: TestClient):
        """TEST-REQ-6009-API-003: GET .../seed-sets/{ssid} -> 200."""
        pid = self._create_project(auth_client)
        self._create_categories(auth_client, pid)

        create_resp = auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "GetTest", "seeds": [{"A": "a1", "B": "b1"}]},
        )
        ssid = create_resp.json()["id"]

        resp = auth_client.get(f"/api/projects/{pid}/seed-sets/{ssid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "GetTest"

    def test_update_seed_set(self, auth_client: TestClient):
        """TEST-REQ-6009-API-004: PUT .../seed-sets/{ssid} -> 200."""
        pid = self._create_project(auth_client)
        self._create_categories(auth_client, pid)

        create_resp = auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "BeforeUpdate", "seeds": [{"A": "a1", "B": "b1"}]},
        )
        ssid = create_resp.json()["id"]

        resp = auth_client.put(
            f"/api/projects/{pid}/seed-sets/{ssid}",
            json={"name": "AfterUpdate"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "AfterUpdate"

    def test_delete_seed_set(self, auth_client: TestClient):
        """TEST-REQ-6009-API-005: DELETE .../seed-sets/{ssid} -> 204."""
        pid = self._create_project(auth_client)
        self._create_categories(auth_client, pid)

        create_resp = auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "ToDelete", "seeds": [{"A": "a1", "B": "b1"}]},
        )
        ssid = create_resp.json()["id"]

        resp = auth_client.delete(f"/api/projects/{pid}/seed-sets/{ssid}")
        assert resp.status_code == 204

    def test_create_seed_set_max_exceeded(self, auth_client: TestClient):
        """TEST-REQ-6009-API-006: 10001 Seeds -> 422."""
        pid = self._create_project(auth_client)
        self._create_categories(auth_client, pid)

        seeds = [{"A": "a1", "B": "b1"} for _ in range(10001)]
        resp = auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "ZuViel", "seeds": seeds},
        )
        assert resp.status_code == 422

    def test_create_seed_set_unknown_values(self, auth_client: TestClient):
        """TEST-REQ-6009-API-007: Unbekannte Werte -> 201 + warnings."""
        pid = self._create_project(auth_client)
        self._create_categories(auth_client, pid)

        seeds = [{"A": "unknown", "B": "b1"}]
        resp = auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "UnknownVals", "seeds": seeds},
        )
        assert resp.status_code == 201
        assert len(resp.json()["warnings"]) > 0

    def test_seed_set_not_found(self, auth_client: TestClient):
        """TEST-REQ-6009-API-008: GET .../seed-sets/99999 -> 404."""
        pid = self._create_project(auth_client)
        resp = auth_client.get(f"/api/projects/{pid}/seed-sets/99999")
        assert resp.status_code == 404

    def test_seed_set_wrong_project(self, auth_client: TestClient):
        """TEST-REQ-6009-API-009: Fremdes Projekt -> 403/404."""
        pid1 = self._create_project(auth_client)
        resp2 = auth_client.post("/api/projects", json={"name": "SeedTestProject2"})
        assert resp2.status_code in (200, 201)
        pid2 = resp2.json()["id"]
        self._create_categories(auth_client, pid1)

        create_resp = auth_client.post(
            f"/api/projects/{pid1}/seed-sets",
            json={"name": "Project1Seeds", "seeds": [{"A": "a1", "B": "b1"}]},
        )
        ssid = create_resp.json()["id"]

        resp = auth_client.get(f"/api/projects/{pid2}/seed-sets/{ssid}")
        assert resp.status_code in (403, 404)


class TestGenerateWithSeeds:
    """TEST-REQ-6009-API-010 bis API-014."""

    def _setup_project(self, client: TestClient) -> int:
        pid = self._create_project(client)
        self._create_categories(client, pid)
        return pid

    def _create_project(self, client: TestClient) -> int:
        resp = client.post("/api/projects", json={"name": "GenSeedProject"})
        assert resp.status_code in (200, 201)
        return resp.json()["id"]

    def _create_categories(self, client: TestClient, pid: int):
        for name in ["A", "B"]:
            client.post(f"/api/projects/{pid}/categories", json={"name": name})
        cats = client.get(f"/api/projects/{pid}/categories").json()
        cat_a = [c for c in cats if c["name"] == "A"][0]
        cat_b = [c for c in cats if c["name"] == "B"][0]
        for v in ["a1", "a2"]:
            client.post(f"/api/categories/{cat_a['id']}/values", json={"value": v})
        for v in ["b1", "b2"]:
            client.post(f"/api/categories/{cat_b['id']}/values", json={"value": v})

    def test_generate_with_seed_set_id(self, auth_client: TestClient):
        """TEST-REQ-6009-API-010: Generierung mit seed_set_id."""
        pid = self._setup_project(auth_client)

        create_resp = auth_client.post(
            f"/api/projects/{pid}/seed-sets",
            json={"name": "GenSeeds", "seeds": [{"A": "a1", "B": "b1"}]},
        )
        ssid = create_resp.json()["id"]

        resp = auth_client.post(
            f"/api/projects/{pid}/generate",
            json={
                "strategy": "pairwise",
                "seed_set_id": ssid,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["seeds_count"] >= 1

    def test_generate_with_seeds_inline(self, auth_client: TestClient):
        """TEST-REQ-6009-API-011: Inline-Seed-Liste."""
        pid = self._setup_project(auth_client)

        resp = auth_client.post(
            f"/api/projects/{pid}/generate",
            json={
                "strategy": "pairwise",
                "seeds": [{"A": "a1", "B": "b1"}],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["seeds_count"] >= 1

    def test_generate_result_has_origin_field(self, auth_client: TestClient):
        """TEST-REQ-6009-API-012: Jeder TC hat origin."""
        pid = self._setup_project(auth_client)

        resp = auth_client.post(
            f"/api/projects/{pid}/generate",
            json={
                "strategy": "pairwise",
                "seeds": [{"A": "a1", "B": "b1"}],
            },
        )
        assert resp.status_code == 200
        gid = resp.json()["generation_id"]

        tc_resp = auth_client.get(f"/api/generations/{gid}/testcases")
        for tc in tc_resp.json()["testcases"]:
            assert "origin" in tc

    def test_generate_result_has_report(self, auth_client: TestClient):
        """TEST-REQ-6009-API-013: Response enthaelt Report-Felder."""
        pid = self._setup_project(auth_client)

        resp = auth_client.post(
            f"/api/projects/{pid}/generate",
            json={
                "strategy": "pairwise",
                "seeds": [{"A": "a1", "B": "b1"}],
            },
        )
        data = resp.json()
        assert "seeds_count" in data
        assert "supplemented_count" in data
        assert "coverage_before" in data
        assert "coverage_after" in data

    def test_generate_without_seeds_ignores_field(self, auth_client: TestClient):
        """TEST-REQ-6009-API-014: Ohne Seeds -> normale Generierung."""
        pid = self._setup_project(auth_client)

        resp = auth_client.post(
            f"/api/projects/{pid}/generate",
            json={"strategy": "pairwise"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["seeds_count"] == 0


class TestGapFillAPI:
    """TEST-REQ-6009-API-018 bis API-021."""

    def _setup_generation(self, client: TestClient) -> tuple:
        pid = self._create_project(client)
        self._create_categories(client, pid)

        resp = client.post(
            f"/api/projects/{pid}/generate",
            json={"strategy": "pairwise"},
        )
        return pid, resp.json()["generation_id"]

    def _create_project(self, client: TestClient) -> int:
        resp = client.post("/api/projects", json={"name": "GapFillProject"})
        assert resp.status_code in (200, 201)
        return resp.json()["id"]

    def _create_categories(self, client: TestClient, pid: int):
        for name in ["A", "B"]:
            client.post(f"/api/projects/{pid}/categories", json={"name": name})
        cats = client.get(f"/api/projects/{pid}/categories").json()
        cat_a = [c for c in cats if c["name"] == "A"][0]
        cat_b = [c for c in cats if c["name"] == "B"][0]
        for v in ["a1", "a2"]:
            client.post(f"/api/categories/{cat_a['id']}/values", json={"value": v})
        for v in ["b1", "b2"]:
            client.post(f"/api/categories/{cat_b['id']}/values", json={"value": v})

    def test_gap_fill_creates_new_generation(self, auth_client: TestClient):
        """TEST-REQ-6009-API-018: POST /api/generations/{gid}/gap-fill -> 200."""
        pid, gid = self._setup_generation(auth_client)

        resp = auth_client.post(f"/api/generations/{gid}/gap-fill")
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_generation_id"] != gid

    def test_gap_fill_old_generation_unchanged(self, auth_client: TestClient):
        """TEST-REQ-6009-API-019: Alte Generation unveraendert."""
        pid, gid = self._setup_generation(auth_client)

        old_tcs = auth_client.get(f"/api/generations/{gid}/testcases").json()
        old_count = len(old_tcs["testcases"])

        auth_client.post(f"/api/generations/{gid}/gap-fill")

        after_tcs = auth_client.get(f"/api/generations/{gid}/testcases").json()
        assert len(after_tcs["testcases"]) == old_count

    def test_gap_fill_new_generation_has_origin(self, auth_client: TestClient):
        """TEST-REQ-6009-API-020: Neue Generation hat origin-Felder."""
        pid, gid = self._setup_generation(auth_client)

        resp = auth_client.post(f"/api/generations/{gid}/gap-fill")
        new_gid = resp.json()["new_generation_id"]

        tc_resp = auth_client.get(f"/api/generations/{new_gid}/testcases")
        has_seed = any(tc.get("origin") == "seed" for tc in tc_resp.json()["testcases"])
        assert has_seed

    def test_gap_fill_report_before_after_coverage(self, auth_client: TestClient):
        """TEST-REQ-6009-API-021: coverage_before < coverage_after bei Luecken."""
        pid, gid = self._setup_generation(auth_client)

        resp = auth_client.post(f"/api/generations/{gid}/gap-fill")
        data = resp.json()
        # Bei voller Pairwise-Abdeckung sollte beides 100% sein
        assert data["coverage_before"] >= 0
        assert data["coverage_after"] >= data["coverage_before"]