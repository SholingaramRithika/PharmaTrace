"""Offline dataset integrity tests (no database needed)."""
from collections import Counter
from dataset import ID_KEY, SCENARIOS, build_dataset, summary
from reference_rules import evaluate

D = build_dataset()
LABEL_KEY = {"Medicine": "medicines", "Batch": "batches", "Organization": "organizations", "Location": "locations",
             "Shipment": "shipments", "Pharmacy": "pharmacies", "Recall": "recalls", "TraceabilityEvent": "events"}


def test_deterministic():
    assert build_dataset() == D


def test_target_counts():
    n = summary(D)["nodes"]
    suppliers_and_mfrs = sum(1 for o in D["organizations"] if o["role"] in ("Manufacturer", "Supplier"))
    dist_wh = sum(1 for o in D["organizations"] if o["role"] in ("Distributor", "WarehouseOperator"))
    assert 8 <= suppliers_and_mfrs <= 12
    assert 15 <= dist_wh <= 25
    assert 30 <= n["batches"] <= 50
    assert 10 <= n["pharmacies"] <= 20
    assert n["medicines"] >= 5 and n["recalls"] >= 1 and n["shipments"] > 50 and n["events"] > 50


def test_ids_unique_per_label():
    for label, key in LABEL_KEY.items():
        ids = [r[ID_KEY[label]] for r in D[key]]
        assert len(ids) == len(set(ids)), label


def test_no_dangling_relationships():
    ids = {l: {r[ID_KEY[l]] for r in D[k]} for l, k in LABEL_KEY.items()}
    for r in D["rels"]:
        assert r["fromId"] in ids[r["fromLabel"]], r
        assert r["toId"] in ids[r["toLabel"]], r


def test_no_duplicate_relationships():
    keys = [(r["type"], r["fromId"], r["toId"], tuple(sorted(r["props"].items()))) for r in D["rels"]]
    assert len(keys) == len(set(keys))


def test_quantities_and_dates_valid():
    for b in D["batches"]:
        assert b["quantity"] > 0 and b["expiryDate"] > b["manufacturingDate"]
    assert all(s["quantity"] > 0 for s in D["shipments"])


def test_all_scenarios_present():
    ids = {b["batchId"] for b in D["batches"]}
    for name, batch_ids in SCENARIOS.items():
        assert set(batch_ids) <= ids, name


def test_every_seeded_anomaly_is_found_and_nothing_else():
    """Reference rules must flag exactly the seeded scenario batches (no accidental anomalies)."""
    got = evaluate(D)
    assert got["DUPLICATE_LOT"] == {"BATCH-DUP-001", "BATCH-DUP-002"}
    assert got["UNVERIFIED_SUPPLIER"] == {"BATCH-UNVER-001"}
    assert got["UNEXPECTED_ROUTE"] == {"BATCH-UNEXP-001"}
    assert got["EXPIRED_BATCH"] == {"BATCH-EXPIRED-001"}
    assert got["QUANTITY_MISMATCH"] == {"BATCH-QTY-001"}
    assert got["MISSING_EVENT"] == {"BATCH-INCOMPLETE-001"}
    assert got["INCOMPLETE_PATH"] == {"BATCH-INCOMPLETE-001"}
    assert "BATCH-VALID-001" not in set().union(*got.values())


def test_recall_scenario_has_multiple_destinations():
    ships = {s["shipmentId"]: s for s in D["shipments"]}
    affected = {r["fromId"] for r in D["rels"] if r["type"] == "AFFECTED_BY" and r["toId"] == "RCL-001"}
    assert affected == set(SCENARIOS["S7_RECALLED_MULTI_DESTINATION"])
    tr = {(r["fromId"], r["toId"]) for r in D["rels"] if r["type"] == "TRANSPORTED_IN"}
    pharm_ships = {r["fromId"]: r["toId"] for r in D["rels"] if r["type"] == "DELIVERED_TO" and r["toLabel"] == "Pharmacy"}
    dests = {pharm_ships[s] for b, s in tr if b in affected and s in pharm_ships}
    assert len(dests) >= 5
    units = sum(ships[s]["quantity"] for b, s in tr if b in affected and s in pharm_ships)
    assert units == 24000  # 2 batches x 12000 delivered in full


def test_valid_batch_has_complete_route():
    rels = [r for r in D["rels"] if r["fromId"] == "BATCH-VALID-001"]
    kinds = Counter(r["type"] for r in rels)
    assert kinds["HAS_EVENT"] == 5 + 2 and kinds["TRANSPORTED_IN"] == 4  # 4 events + 3 DELIVERED; 1 inbound + 3 legs
