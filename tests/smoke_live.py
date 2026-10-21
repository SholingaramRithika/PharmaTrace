"""End-to-end check against a RUNNING backend + loaded Neo4j (stdlib only).

    python tests/smoke_live.py [http://localhost:8000]

Asserts the seeded demo results documented in docs/DEMO_GUIDE.md. Exits non-zero on any failure,
so paste the output back if something fails. Creates and deletes TEST-SMOKE-1 (needs ENABLE_WRITES=true;
the CRUD step is skipped with a notice if writes are disabled).
"""
import json, sys, urllib.request, urllib.error

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
fails = 0


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def check(name, ok, detail=""):
    global fails
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    fails += 0 if ok else 1


try:
    s, h = call("GET", "/api/health")
except urllib.error.URLError as e:
    sys.exit(f"Cannot reach the API at {BASE}: {e.reason}. Start the backend first.")
check("health connected", s == 200 and h["database"]["connected"], h)
if not (s == 200 and h["database"]["connected"]):
    sys.exit("Database not connected; start Neo4j and load data (python database/setup_db.py all).")
s, o = call("GET", "/api/overview")
c = o["counts"]
check("dataset counts (8 medicines, 40 batches, 25 orgs, 133 shipments)", (c["medicines"], c["batches"], c["organizations"], c["shipments"]) == (8, 40, 25, 133), c)
check("relationships >= 1394", c["relationships"] >= 1394, c["relationships"])
s, r = call("GET", "/api/risk/findings")
rules = {}
for f in r["findings"]:
    rules.setdefault(f["rule"], set()).add(f["batchId"])
expected = {"DUPLICATE_LOT": {"BATCH-DUP-001", "BATCH-DUP-002"}, "UNVERIFIED_SUPPLIER": {"BATCH-UNVER-001"}, "UNEXPECTED_ROUTE": {"BATCH-UNEXP-001"},
            "EXPIRED_BATCH": {"BATCH-EXPIRED-001"}, "QUANTITY_MISMATCH": {"BATCH-QTY-001"}, "MISSING_EVENT": {"BATCH-INCOMPLETE-001"}, "INCOMPLETE_PATH": {"BATCH-INCOMPLETE-001"}}
check("risk rules flag exactly the seeded batches", rules == expected, {k: sorted(v) for k, v in rules.items()})
s, t = call("GET", "/api/traceability/BATCH-VALID-001")
check("valid batch: no gaps, no findings, graph present", s == 200 and not t["gaps"] and not t["issues"] and len(t["graph"]["nodes"]) > 8, t.get("gaps"))
s, t = call("GET", "/api/traceability/BATCH-INCOMPLETE-001")
check("incomplete batch reports missing RECEIVED and open shipment", s == 200 and any("RECEIVED" in g for g in t["gaps"]) and any("no recorded destination" in g for g in t["gaps"]), t.get("gaps"))
s, _ = call("GET", "/api/traceability/BATCH-NOPE-999")
check("unknown batch -> 404", s == 404)
s, i = call("GET", "/api/recall/RCL-001/impact")
tt = i.get("totals", {})
check("recall RCL-001: 2 batches, 6 pharmacies, 24000 units", (tt.get("batches"), tt.get("pharmacies"), tt.get("unitsDeliveredToPharmacies")) == (2, 6, 24000), tt)
s, m = call("GET", "/api/medicines")
check("8 medicines with forms", len(m["medicines"]) == 8 and all(x["form"] for x in m["medicines"]))
s, g = call("GET", "/api/graph/demo")
ids = {n["id"] for n in g["nodes"]}
check("demo graph: edges reference existing nodes", g["edges"] and all(e["source"] in ids and e["target"] in ids for e in g["edges"]))
s, q = call("GET", "/api/lab/queries")
bad = []
for x in q["queries"]:
    if x["kind"] != "write":
        st, res = call("POST", "/api/lab/run", {"queryId": x["id"]})
        if st != 200:
            bad.append((x["id"], res))
check(f"all {sum(x['kind'] != 'write' for x in q['queries'])} read templates execute", not bad, bad[:3])
s, p = call("POST", "/api/lab/run", {"queryId": "profile_traversal"})
check("PROFILE returns a plan with db hits", s == 200 and p["plan"] and p["profiled"])
s, ins = call("GET", "/api/insights")
check("insights: constraints and indexes exist", s == 200 and len(ins["constraints"]) >= 8 and len(ins["indexes"]) >= 17, (len(ins.get("constraints", [])), len(ins.get("indexes", []))))
if q["writesEnabled"]:
    body = {"batchId": "TEST-SMOKE-1", "medicineId": "MED-001", "quantity": 10, "manufacturingDate": "2026-01-01", "expiryDate": "2027-01-01"}
    call("DELETE", "/api/crud/batches/TEST-SMOKE-1")
    check("CRUD create 201", call("POST", "/api/crud/batches", body)[0] == 201)
    check("CRUD duplicate -> 409", call("POST", "/api/crud/batches", body)[0] == 409)
    check("CRUD update", call("PATCH", "/api/crud/batches/TEST-SMOKE-1", {"status": "Released"})[0] == 200)
    check("CRUD delete", call("DELETE", "/api/crud/batches/TEST-SMOKE-1")[0] == 200)
    check("CRUD deleted -> 404", call("GET", "/api/crud/batches/TEST-SMOKE-1")[0] == 404)
else:
    print("SKIP CRUD (ENABLE_WRITES=false)")
print("\nRESULT:", "ALL PASSED" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
