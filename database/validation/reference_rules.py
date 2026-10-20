"""Pure-Python reference implementation of the seven risk rules.

Used (1) offline to prove the dataset contains exactly the seeded anomalies, and
(2) in the live-database integration test to cross-check the Cypher rules.
"""
from __future__ import annotations
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset import AS_OF, REQUIRED_EVENTS, build_dataset  # noqa: E402


def evaluate(data: dict | None = None, as_of: date = AS_OF) -> dict[str, set[str]]:
    d = data or build_dataset()
    batches = {b["batchId"]: b for b in d["batches"]}
    ships = {s["shipmentId"]: s for s in d["shipments"]}
    pharm = {p["pharmacyId"]: p for p in d["pharmacies"]}
    orgs = {o["organizationId"]: o for o in d["organizations"]}
    out = defaultdict(set)
    out_rels = defaultdict(list)
    for r in d["rels"]:
        out_rels[(r["type"], r["fromLabel"], r["fromId"])].append(r["toId"])
    # incoming FOLLOWED_BY
    has_prev = {r["toId"] for r in d["rels"] if r["type"] == "FOLLOWED_BY"}
    # 1 duplicate lot
    by_lot = defaultdict(list)
    for b in batches.values():
        by_lot[b["lotNumber"]].append(b["batchId"])
    for ids in by_lot.values():
        if len(ids) > 1:
            out["DUPLICATE_LOT"].update(ids)
    # 2 unverified supplier
    for r in d["rels"]:
        if r["type"] == "SUPPLIES_TO" and orgs[r["fromId"]]["verificationStatus"] != "Verified":
            out["UNVERIFIED_SUPPLIER"].add(r["toId"])
    for bid in batches:
        shp = out_rels[("TRANSPORTED_IN", "Batch", bid)]
        # 3 unexpected route
        for s in shp:
            for dest in out_rels[("DELIVERED_TO", "Shipment", s)]:
                if dest in pharm and pharm[dest]["region"] != batches[bid]["intendedRegion"]:
                    out["UNEXPECTED_ROUTE"].add(bid)
            # 7 incomplete path
            if not out_rels[("DELIVERED_TO", "Shipment", s)]:
                out["INCOMPLETE_PATH"].add(bid)
        # 5 quantity
        for s in shp:
            if s not in has_prev:
                down = sum(ships[t]["quantity"] for t in out_rels[("FOLLOWED_BY", "Shipment", s)])
                if down > ships[s]["quantity"] or ships[s]["quantity"] > batches[bid]["quantity"]:
                    out["QUANTITY_MISMATCH"].add(bid)
    # 4 expired
    for b in batches.values():
        if date.fromisoformat(b["expiryDate"]) < as_of:
            out["EXPIRED_BATCH"].add(b["batchId"])
    # 6 missing events
    types = defaultdict(set)
    ev = {e["eventId"]: e for e in d["events"]}
    for r in d["rels"]:
        if r["type"] == "HAS_EVENT":
            types[r["fromId"]].add(ev[r["toId"]]["eventType"])
    for bid in batches:
        if any(t not in types[bid] for t in REQUIRED_EVENTS):
            out["MISSING_EVENT"].add(bid)
    return dict(out)


if __name__ == "__main__":
    for k, v in sorted(evaluate().items()):
        print(f"{k:22} {sorted(v)}")
