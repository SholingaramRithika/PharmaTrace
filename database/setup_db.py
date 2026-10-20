"""PharmaTrace database setup tool.

Usage (from repo root, with .env configured):
    python database/setup_db.py schema      # constraints + indexes
    python database/setup_db.py load        # MERGE synthetic data (idempotent)
    python database/setup_db.py validate    # compare DB against generator
    python database/setup_db.py reset --confirm   # delete ALL data (local use)
    python database/setup_db.py all         # schema + load + validate
"""
from __future__ import annotations
import os, re, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dataset import build_dataset, summary, ID_KEY, SCENARIOS  # noqa: E402

DATE_FIELDS = {"Batch": ["manufacturingDate", "expiryDate"]}
DATETIME_FIELDS = {"Shipment": ["departureTime", "arrivalTime"], "Recall": ["issuedAt"],
                   "TraceabilityEvent": ["timestamp"]}
NODE_KEYS = {"Medicine": "medicines", "Batch": "batches", "Organization": "organizations", "Location": "locations",
             "Shipment": "shipments", "Pharmacy": "pharmacies", "Recall": "recalls", "TraceabilityEvent": "events"}
REL_RE = re.compile(r"^[A-Z_]+$")


def load_env():
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_driver():
    from neo4j import GraphDatabase
    load_env()
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not pwd:
        sys.exit("NEO4J_PASSWORD is not set. Copy .env.example to .env and edit it.")
    return GraphDatabase.driver(uri, auth=(user, pwd)), os.environ.get("NEO4J_DATABASE", "neo4j")


def init_schema(driver, db):
    text = (Path(__file__).parent / "schema.cypher").read_text()
    stmts = [s.strip() for s in re.sub(r"//.*", "", text).split(";") if s.strip()]
    with driver.session(database=db) as s:
        for st in stmts:
            s.run(st).consume()
    print(f"Schema OK: {len(stmts)} statements applied (constraints + indexes).")


def load_data(driver, db):
    data = build_dataset()
    with driver.session(database=db) as s:
        for label, key in NODE_KEYS.items():
            idk = ID_KEY[label]
            temporal = DATE_FIELDS.get(label, []) + DATETIME_FIELDS.get(label, [])
            rows = [{"id": r[idk], "props": {k: v for k, v in r.items() if k not in temporal and k != idk},
                     "t": {k: r.get(k) for k in temporal}} for r in data[key]]
            sets = "".join(f"\nSET n.{f} = date(row.t.{f})" for f in DATE_FIELDS.get(label, []))
            sets += "".join(f"\nSET n.{f} = datetime(row.t.{f})" for f in DATETIME_FIELDS.get(label, []))
            q = f"UNWIND $rows AS row MERGE (n:{label} {{{idk}: row.id}}) SET n += row.props{sets}"
            s.run(q, rows=rows).consume()
        groups: dict = {}
        for r in data["rels"]:
            assert REL_RE.match(r["type"]) and r["fromLabel"] in ID_KEY and r["toLabel"] in ID_KEY
            groups.setdefault((r["type"], r["fromLabel"], r["toLabel"]), []).append(
                {"f": r["fromId"], "t": r["toId"], "props": r["props"]})
        for (typ, fl, tl), rows in groups.items():
            q = (f"UNWIND $rows AS row MATCH (a:{fl} {{{ID_KEY[fl]}: row.f}}) MATCH (b:{tl} {{{ID_KEY[tl]}: row.t}}) "
                 f"MERGE (a)-[r:{typ}]->(b) SET r += row.props")
            s.run(q, rows=rows).consume()
    print("Load OK:", json.dumps(summary(data)["nodes"]), "relationships:", summary(data)["totalRelationships"])


def reset(driver, db):
    with driver.session(database=db) as s:
        s.run("MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS").consume()
    print("All nodes and relationships deleted.")


def validate(driver, db) -> bool:
    exp = summary(build_dataset())
    ok = True
    with driver.session(database=db) as s:
        got_nodes = {r["l"]: r["c"] for r in s.run("MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS c")}
        got_rels = {r["t"]: r["c"] for r in s.run("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c")}
        print(f"{'Label':20}{'expected':>10}{'actual':>10}")
        for label, key in NODE_KEYS.items():
            e, g = exp["nodes"][key], got_nodes.get(label, 0)
            ok &= e == g
            print(f"{label:20}{e:>10}{g:>10}  {'OK' if e == g else 'MISMATCH'}")
        for t, e in exp["relationships"].items():
            g = got_rels.get(t, 0)
            ok &= e == g
            print(f"{t:20}{e:>10}{g:>10}  {'OK' if e == g else 'MISMATCH'}")
        ids = [b for v in SCENARIOS.values() for b in v]
        found = {r["id"] for r in s.run("MATCH (b:Batch) WHERE b.batchId IN $ids RETURN b.batchId AS id", ids=ids)}
        missing = set(ids) - found
        print("Scenario batches present:", len(found), "/", len(ids), "missing:", sorted(missing))
        ok &= not missing
    print("VALIDATION", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "help":
        print(__doc__); sys.exit(0)
    drv, db = get_driver()
    try:
        drv.verify_connectivity()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Cannot connect to Neo4j: {e}\nCheck that the DBMS is started and .env is correct.")
    if cmd == "schema": init_schema(drv, db)
    elif cmd == "load": load_data(drv, db)
    elif cmd == "validate": sys.exit(0 if validate(drv, db) else 1)
    elif cmd == "reset":
        if "--confirm" not in sys.argv: sys.exit("Refusing without --confirm")
        reset(drv, db)
    elif cmd == "all":
        init_schema(drv, db); load_data(drv, db); sys.exit(0 if validate(drv, db) else 1)
    else: print(__doc__)
    drv.close()
