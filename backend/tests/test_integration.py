"""Live-database tests. REQUIRE a running Neo4j with schema + data loaded
(python database/setup_db.py all). Skipped automatically when NEO4J_PASSWORD is unset
or the database is unreachable. Use a dedicated/test database: write tests create and
delete TEST-* nodes only."""
import pytest
from fastapi.testclient import TestClient
from app.config import get_settings
from app.main import create_app
from tests.conftest import neo4j_available
from dataset import SCENARIOS, build_dataset, summary
from reference_rules import evaluate

pytestmark = [pytest.mark.neo4j, pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")]


@pytest.fixture(scope="module")
def api():
    get_settings.cache_clear()
    import os
    os.environ["ENABLE_WRITES"] = "true"
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c


def test_health_connected(api):
    assert api.get("/api/health").json()["database"]["connected"] is True


def test_counts_match_generator(api):
    exp = summary(build_dataset())
    c = api.get("/api/overview").json()["counts"]
    assert c["batches"] >= exp["nodes"]["batches"] and c["medicines"] == exp["nodes"]["medicines"]


def test_constraints_and_indexes_exist(api):
    j = api.get("/api/insights").json()
    names = {c["name"] for c in j["constraints"]}
    assert {"batch_id", "medicine_id", "organization_id"} <= names
    assert any(i["name"] == "batch_lot" for i in j["indexes"])


def test_cypher_rules_match_reference(api):
    got = {}
    for f in api.get("/api/risk/findings").json()["findings"]:
        got.setdefault(f["rule"], set()).add(f["batchId"])
    assert got == evaluate()


def test_trace_valid_batch(api):
    j = api.get("/api/traceability/BATCH-VALID-001").json()
    assert j["gaps"] == [] and j["issues"] == [] and len(j["graph"]["nodes"]) > 8


def test_trace_incomplete_batch_reports_gaps(api):
    j = api.get("/api/traceability/BATCH-INCOMPLETE-001").json()
    assert any("RECEIVED" in g for g in j["gaps"]) and any("no recorded destination" in g for g in j["gaps"])


def test_trace_unknown_404(api):
    assert api.get("/api/traceability/BATCH-NOPE-999").status_code == 404


def test_recall_impact(api):
    j = api.get("/api/recall/RCL-001/impact").json()
    assert j["totals"]["batches"] == 2 and j["totals"]["pharmacies"] >= 5 and j["totals"]["unitsDeliveredToPharmacies"] == 24000


def test_graph_edges_have_both_endpoints(api):
    g = api.get("/api/graph/demo").json()
    ids = {n["id"] for n in g["nodes"]}
    assert g["edges"] and all(e["source"] in ids and e["target"] in ids for e in g["edges"])


def test_crud_roundtrip_and_duplicate_prevention(api):
    body = {"batchId": "TEST-IT-1", "medicineId": "MED-001", "quantity": 10, "manufacturingDate": "2026-01-01", "expiryDate": "2027-01-01"}
    api.delete("/api/crud/batches/TEST-IT-1")
    assert api.post("/api/crud/batches", json=body).status_code == 201
    assert api.post("/api/crud/batches", json=body).status_code == 409
    assert api.patch("/api/crud/batches/TEST-IT-1", json={"status": "Released"}).json()["updated"]["properties"]["status"] == "Released"
    assert api.delete("/api/crud/batches/TEST-IT-1").status_code == 200
    assert api.get("/api/crud/batches/TEST-IT-1").status_code == 404


def test_every_read_template_executes(api):
    qs = api.get("/api/lab/queries").json()["queries"]
    for q in qs:
        if q["kind"] != "write":
            r = api.post("/api/lab/run", json={"queryId": q["id"]})
            assert r.status_code == 200, (q["id"], r.text)


def test_profile_returns_plan(api):
    r = api.post("/api/lab/run", json={"queryId": "profile_traversal"}).json()
    assert r["plan"] and r["profiled"]
