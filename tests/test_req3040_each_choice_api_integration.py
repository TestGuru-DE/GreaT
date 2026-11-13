from __future__ import annotations

import time


def _unique_suffix():
    """Erzeugt einen eindeutigen Suffix fuer Test-Namen."""
    return f"{int(time.time() * 1000)}"


def _create_category_with_values(client, project_id: int, name: str, values: list[str], order_index: int) -> int:
    category_resp = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": name, "order_index": order_index},
    )
    assert category_resp.status_code == 200, category_resp.text
    category_id = category_resp.json()["id"]

    for value in values:
        value_resp = client.post(f"/api/categories/{category_id}/values", json={"value": value})
        assert value_resp.status_code == 200, value_resp.text

    return category_id


def test_req_3040_req_0801_each_choice_generation_with_rules_keeps_reachable_values(auth_client):
    """REQ-3040 + REQ-0801: API-Each-Choice mit Regeln muss erreichbare Werte behalten."""
    suffix = _unique_suffix()
    project_resp = auth_client.post(
        "/api/projects",
        json={"name": f"REQ3040-EachChoice-Integration-{suffix}"},
    )
    assert project_resp.status_code == 200, project_resp.text
    project_id = project_resp.json()["id"]

    customer_category_id = _create_category_with_values(
        auth_client,
        project_id,
        "Kundentyp",
        ["Neukunde", "Bestandskunde"],
        order_index=1,
    )
    seminar_category_id = _create_category_with_values(
        auth_client,
        project_id,
        "Seminar",
        ["SK", "T&Q"],
        order_index=2,
    )

    rule_resp = auth_client.post(
        f"/api/projects/{project_id}/rules",
        json={
            "type": "exclude",
            "if_category_id": seminar_category_id,
            "if_value": "SK",
            "then_category_id": customer_category_id,
            "then_value": "Neukunde",
        },
    )
    assert rule_resp.status_code == 201, rule_resp.text

    generate_resp = auth_client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "each", "apply_rules": True},
    )
    assert generate_resp.status_code == 200, generate_resp.text
    generation_id = generate_resp.json()["generation_id"]

    testcases_resp = auth_client.get(f"/api/generations/{generation_id}/testcases")
    assert testcases_resp.status_code == 200, testcases_resp.text
    assignments = [tc["assignments"] for tc in testcases_resp.json()["testcases"]]

    assert all(
        not (assignment.get("Kundentyp") == "Neukunde" and assignment.get("Seminar") == "SK")
        for assignment in assignments
    ), assignments
    assert any(assignment.get("Kundentyp") == "Neukunde" for assignment in assignments), assignments