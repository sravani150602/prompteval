def setup_run(client):
    dataset = client.post("/datasets", json={"name":"heldout","version":"1", "examples":[{"input_text":"charged twice","reference_answer":"billing","checks":{"exact_match":"billing"}}]}).json()
    variants = [client.post("/prompt-variants", json={"name":name,"template":"{input}"}).json()["id"] for name in ["v1", "v2", "v3"]]
    return client.post("/runs", json={"dataset_id":dataset["id"],"prompt_variant_ids":variants,"repeats":3,"seed":42})


def test_run_persists_lineage_and_metrics(client):
    response = setup_run(client)
    assert response.status_code == 201
    body = response.json()
    assert body["metrics"]["result_count"] == 9
    assert body["dataset_version"] == "1"
    assert body["evaluator_version"] == "1.0.0"


def test_baseline_regression_gate(client):
    first = setup_run(client).json()
    assert client.post("/baselines", json={"name":"main","run_id":first["id"]}).status_code == 201
    second = client.post("/runs", json={"dataset_id": first["dataset_id"], "prompt_variant_ids": first["prompt_variant_ids"], "repeats": 3, "seed": 42}).json()
    response = client.get(f'/runs/{second["id"]}/regression?baseline_name=main')
    assert response.status_code == 200
    assert response.json()["passed"] is True
