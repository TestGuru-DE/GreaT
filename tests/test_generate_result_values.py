"""REQ-4016 Regressionstests fuer Ergebniswerte in generierten Testfaellen."""


def _create_category_with_values(client, project_id: int, name: str, values: list[str], *, is_result: bool = False) -> int:
    category = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": name, "order_index": 0, "is_result": is_result},
    )
    assert category.status_code == 200, category.text
    category_id = category.json()["id"]
    for value in values:
        created = client.post(
            f"/api/categories/{category_id}/values",
            json={"value": value, "risk_weight": 1},
        )
        assert created.status_code == 200, created.text
    return category_id


# REQ-4016
def test_result_category_values_in_generated_testcases(client):
    project = client.post("/api/projects", json={"name": "REQ4016-ResultValues"})
    assert project.status_code == 200, project.text
    project_id = project.json()["id"]

    _create_category_with_values(client, project_id, "Browser", ["Chrome", "Firefox"])
    _create_category_with_values(client, project_id, "Ergebnis 1", ["Pass", "Fail"], is_result=True)

    generation = client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "all"},
    )
    assert generation.status_code == 200, generation.text

    response = client.get(f"/api/generations/{generation.json()['generation_id']}/testcases")
    assert response.status_code == 200, response.text
    payload = response.json()

    result_categories = payload["result_categories"]
    assert result_categories == [
        {
            "id": result_categories[0]["id"],
            "name": "Ergebnis 1",
            "editable": True,
            "values": [
                {"id": result_categories[0]["values"][0]["id"], "value": "Pass"},
                {"id": result_categories[0]["values"][1]["id"], "value": "Fail"},
            ],
        }
    ]

    testcases = payload["testcases"]
    assert len(testcases) == 2
    for testcase in testcases:
        assert testcase["assignments"]["Ergebnis 1"] == ""


# REQ-4016
def test_rule_with_result_value_sets_cell(client):
    project = client.post("/api/projects", json={"name": "REQ4016-RuleResult"})
    assert project.status_code == 200, project.text
    project_id = project.json()["id"]

    browser_id = _create_category_with_values(client, project_id, "Browser", ["Chrome", "Firefox"])
    result_id = _create_category_with_values(client, project_id, "Ergebnis 1", ["Pass", "Fail"], is_result=True)

    rule = client.post(
        f"/api/projects/{project_id}/rules",
        json={
            "type": "dependency",
            "if_category_id": browser_id,
            "if_value": "Chrome",
            "then_category_id": result_id,
            "then_value": "Pass",
        },
    )
    assert rule.status_code == 201, rule.text

    generation = client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "all", "apply_rules": True},
    )
    assert generation.status_code == 200, generation.text

    response = client.get(f"/api/generations/{generation.json()['generation_id']}/testcases")
    assert response.status_code == 200, response.text
    testcases = response.json()["testcases"]

    chrome_case = next(tc for tc in testcases if tc["assignments"]["Browser"] == "Chrome")
    firefox_case = next(tc for tc in testcases if tc["assignments"]["Browser"] == "Firefox")

    assert chrome_case["assignments"]["Ergebnis 1"] == "Pass"
    assert firefox_case["assignments"]["Ergebnis 1"] == ""
