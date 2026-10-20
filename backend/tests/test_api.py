from tests.conftest import FakeClient


def test_health_reports_disconnected_honestly(make_client):
    c, _ = make_client(FakeClient(up=False))
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["database"]["connected"] is False and r.json()["status"] == "degraded"


def test_health_connected(make_client):
    c, _ = make_client(FakeClient(rows=[{"nodes": 5}]))
    assert c.get("/api/health").json()["database"] == {"connected": True, "nodes": 5}


def test_db_down_gives_503_envelope(make_client):
    c, _ = make_client(FakeClient(up=False))
    r = c.get("/api/medicines")
    assert r.status_code == 503 and r.json()["error"]["code"] == "DATABASE_UNAVAILABLE"


def test_invalid_node_id_rejected(make_client):
    c, _ = make_client()
    for bad in ["Batch:a;b", "Evil:1", "Batch:", "nocolon", "Batch:" + "x" * 70, "Batch:a%20b"]:
        r = c.get(f"/api/graph/node/{bad}")
        assert r.status_code == 400, bad


def test_unknown_batch_is_404_not_fabricated(make_client):
    c, _ = make_client(FakeClient(rows=[]))
    r = c.get("/api/traceability/BATCH-NOPE-999")
    assert r.status_code == 404 and "not found" in r.json()["error"]["message"].lower()


def test_malformed_batch_id_422(make_client):
    c, _ = make_client()
    r = c.get("/api/traceability/a b;DROP")
    assert r.status_code in (404, 422)


def test_bad_recall_id_422(make_client):
    c, _ = make_client()
    assert c.get("/api/recall/XYZ/impact").status_code == 422


def test_search_validation(make_client):
    c, _ = make_client()
    assert c.get("/api/graph/search?q=").status_code == 422
    assert c.get("/api/graph/search?q=x&labels=Evil").status_code == 400
    assert c.get("/api/graph/search?q=x&limit=999").status_code == 422


def test_neighbors_rejects_unknown_reltype(make_client):
    c, _ = make_client()
    assert c.get("/api/graph/neighbors/Batch:BATCH-001?relTypes=EVIL").status_code == 400


def test_writes_disabled_by_default(make_client):
    c, fake = make_client(ENABLE_WRITES="false")
    r = c.post("/api/crud/batches", json={"batchId": "TEST-A1B", "medicineId": "MED-001", "quantity": 5,
                                           "manufacturingDate": "2026-01-01", "expiryDate": "2027-01-01"})
    assert r.status_code == 403 and not fake.calls


def test_admin_token_required_when_set(make_client):
    c, _ = make_client(ENABLE_WRITES="true", ADMIN_TOKEN="s3cret")
    assert c.delete("/api/crud/batches/TEST-ABC").status_code == 401
    assert c.delete("/api/crud/batches/TEST-ABC", headers={"X-Admin-Token": "s3cret"}).status_code == 404


def test_crud_validation(make_client):
    c, fake = make_client(ENABLE_WRITES="true")
    base = {"batchId": "TEST-A1B", "medicineId": "MED-001", "quantity": 5, "manufacturingDate": "2026-01-01", "expiryDate": "2027-01-01"}
    assert c.post("/api/crud/batches", json={**base, "batchId": "BATCH-001"}).status_code == 422   # not TEST-
    assert c.post("/api/crud/batches", json={**base, "quantity": 0}).status_code == 422
    assert c.post("/api/crud/batches", json={**base, "quantity": -3}).status_code == 422
    assert c.post("/api/crud/batches", json={**base, "expiryDate": "2025-01-01"}).status_code == 422
    assert c.delete("/api/crud/batches/BATCH-001").status_code == 422  # real batches can't be targeted
    assert not fake.calls


def test_crud_create_missing_medicine_is_404(make_client):
    c, _ = make_client(ENABLE_WRITES="true")
    r = c.post("/api/crud/batches", json={"batchId": "TEST-A1B", "medicineId": "MED-999", "quantity": 5,
                                           "manufacturingDate": "2026-01-01", "expiryDate": "2027-01-01"})
    assert r.status_code == 404


def test_lab_unknown_query_404(make_client):
    c, _ = make_client()
    assert c.post("/api/lab/run", json={"queryId": "drop_everything"}).status_code == 404


def test_lab_rejects_raw_cypher_and_bad_params(make_client):
    c, fake = make_client(ENABLE_WRITES="true")
    assert c.post("/api/lab/run", json={"queryId": "match_batch", "params": {"batchId": "x'}) DETACH DELETE n //"}}).status_code == 422
    assert c.post("/api/lab/run", json={"queryId": "match_batch", "params": {"cypher": "MATCH (n) RETURN n"}}).status_code == 422
    assert not fake.calls


def test_lab_write_blocked_when_disabled(make_client):
    c, fake = make_client(ENABLE_WRITES="false")
    r = c.post("/api/lab/run", json={"queryId": "delete_test_batch"})
    assert r.status_code == 403 and not fake.calls


def test_lab_read_runs_with_validated_params(make_client):
    c, fake = make_client()
    r = c.post("/api/lab/run", json={"queryId": "match_batch", "params": {"batchId": "BATCH-001"}})
    assert r.status_code == 200 and fake.calls[0][1] == {"batchId": "BATCH-001"}


def test_lab_catalogue_listing(make_client):
    c, _ = make_client()
    j = c.get("/api/lab/queries").json()
    assert len(j["queries"]) >= 12 and "writesEnabled" in j


def test_cors_restricted(make_client):
    c, _ = make_client(CORS_ORIGINS="https://app.example.com")
    ok = c.get("/api/lab/queries", headers={"Origin": "https://app.example.com"})
    bad = c.get("/api/lab/queries", headers={"Origin": "https://evil.example.com"})
    assert ok.headers.get("access-control-allow-origin") == "https://app.example.com"
    assert "access-control-allow-origin" not in bad.headers


def test_docs_hidden_in_production(make_client):
    c, _ = make_client(APP_ENV="production")
    assert c.get("/docs").status_code == 404


def test_no_secrets_in_error_output(make_client):
    c, _ = make_client(FakeClient(up=False), NEO4J_PASSWORD="topsecretpw")
    assert "topsecretpw" not in c.get("/api/overview").text
