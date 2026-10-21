"""Deterministic synthetic dataset for PharmaTrace (SIMULATED DATA ONLY).

All organizations, medicines and pharmacies are fictional. Seeded anomalies
are simulated test scenarios and do not represent real-world misconduct.
Pure Python: no database needed, so integrity can be tested offline.
"""
from __future__ import annotations

import random
from collections import Counter
from datetime import date, datetime, timedelta

SEED = 42
AS_OF = date(2026, 10, 18)  # reference date for expiry rules
REGIONS = ["North", "South", "East", "West", "Central"]

# label -> unique id property
ID_KEY = {
    "Medicine": "medicineId", "Batch": "batchId", "Organization": "organizationId",
    "Location": "locationId", "Shipment": "shipmentId", "Pharmacy": "pharmacyId",
    "Recall": "recallId", "TraceabilityEvent": "eventId",
}

SCENARIOS = {
    "S1_VALID_ROUTE": ["BATCH-VALID-001"],
    "S2_UNEXPECTED_DESTINATION": ["BATCH-UNEXP-001"],
    "S3_UNVERIFIED_SUPPLIER": ["BATCH-UNVER-001"],
    "S4_EXPIRED_BATCH": ["BATCH-EXPIRED-001"],
    "S5_CONFLICTING_IDENTIFIER": ["BATCH-DUP-001", "BATCH-DUP-002"],
    "S6_QUANTITY_INCONSISTENCY": ["BATCH-QTY-001"],
    "S7_RECALLED_MULTI_DESTINATION": ["BATCH-RECALL-001", "BATCH-RECALL-002"],
    "S8_INCOMPLETE_PATH": ["BATCH-INCOMPLETE-001"],
}

MEDICINES = [  # id, name, code, category, form (all fictional)
    ("MED-001", "Cardiolix 50mg", "CRD-050", "Cardiovascular", "Tablet"),
    ("MED-002", "Neurovance 20mg", "NRV-020", "Neurology", "Capsule"),
    ("MED-003", "Gastrofin Syrup", "GST-100", "Gastroenterology", "Bottle"),
    ("MED-004", "Pulmoclear 10mg", "PLM-010", "Respiratory", "Tablet"),
    ("MED-005", "Immunora Inj.", "IMN-005", "Immunology", "Vial"),
    ("MED-006", "Diabetrol 500mg", "DBT-500", "Endocrinology", "Tablet"),
    ("MED-007", "Antibiotex 250mg", "ABX-250", "Anti-infective", "Capsule"),
    ("MED-008", "Dermacalm Cream", "DRM-030", "Dermatology", "Box"),
]
MANUFACTURERS = [("ORG-M01", "Aurelia Pharma Labs", "North"), ("ORG-M02", "Borealis Biotech", "South"),
                 ("ORG-M03", "Cedrus Therapeutics", "East"), ("ORG-M04", "Delmar Formulations", "West")]
SUPPLIERS = [("ORG-S01", "Evergreen Reagents", "North", "Verified"), ("ORG-S02", "Fathom Chemicals", "South", "Verified"),
             ("ORG-S03", "Granite Excipients", "East", "Verified"), ("ORG-S04", "Helix Raw Materials", "West", "Verified"),
             ("ORG-S05", "Ionia Trading Co", "Central", "Unverified")]
DISTRIBUTORS = [(f"ORG-D{i:02d}", n, REGIONS[(i - 1) % 5]) for i, n in enumerate(
    ["Juniper Logistics", "Keystone Distribution", "Lumen Cold Chain", "Meridian Freight",
     "Nimbus Carriers", "Orchid Medical Transport", "Pinnacle Dispatch", "Quartz Supply Lines"], 1)]
WAREHOUSES = [  # operator id, name, region
    ("ORG-W01", "Atlas Storage North-1", "North"), ("ORG-W02", "Atlas Storage North-2", "North"),
    ("ORG-W03", "Beacon Storage South-1", "South"), ("ORG-W04", "Beacon Storage South-2", "South"),
    ("ORG-W05", "Crest Storage East-1", "East"), ("ORG-W06", "Dune Storage West-1", "West"),
    ("ORG-W07", "Dune Storage West-2", "West"), ("ORG-W08", "Ember Storage Central-1", "Central")]
PHARMACY_REGIONS = ["North"] * 3 + ["South"] * 3 + ["East"] * 2 + ["West"] * 3 + ["Central"] * 3
PHARMACY_NAMES = ["CareFirst", "HealWell", "MediPoint", "PharmaHub", "WellSpring", "RxCorner", "VitalDose",
                  "LifeLine", "CureMart", "HealthGate", "TabletTown", "OmniRx", "PillPost", "NovaCare"]
REQUIRED_EVENTS = ["MANUFACTURED", "QC_RELEASED", "SHIPPED", "RECEIVED"]


class _Builder:
    def __init__(self):
        self.d = {k: [] for k in ["medicines", "organizations", "locations", "pharmacies", "batches",
                                  "shipments", "recalls", "events", "rels"]}
        self.ship_n = 0
        self.evt_n = 0
        self.rng = random.Random(SEED)

    def rel(self, typ, fl, fid, tl, tid, **props):
        self.d["rels"].append({"type": typ, "fromLabel": fl, "fromId": fid,
                               "toLabel": tl, "toId": tid, "props": props})


def _event(b, batch_id, etype, when: datetime, desc, tgt_label, tgt_id):
    b.evt_n += 1
    eid = f"EVT-{b.evt_n:05d}"
    b.d["events"].append({"eventId": eid, "eventType": etype, "timestamp": when.isoformat(), "description": desc})
    b.rel("HAS_EVENT", "Batch", batch_id, "TraceabilityEvent", eid)
    b.rel("RECORDED_AT", "TraceabilityEvent", eid, tgt_label, tgt_id)


def _route(b, batch, mfr_loc, wh_idx, dests, leg2_qty, distributor,
           skip_received=False, open_last_leg=False):
    """Manufacturing site -> warehouse (leg 1) -> pharmacies (leg 2 shipments)."""
    bid, qty = batch["batchId"], batch["quantity"]
    mfg = date.fromisoformat(batch["manufacturingDate"])
    wh_loc = f"LOC-W{wh_idx + 1:02d}"
    t0 = datetime(mfg.year, mfg.month, mfg.day, 8) + timedelta(days=10)
    b.ship_n += 1
    s1 = f"SHP-{b.ship_n:04d}"
    b.d["shipments"].append({"shipmentId": s1, "departureTime": t0.isoformat(),
                             "arrivalTime": (t0 + timedelta(days=2)).isoformat(),
                             "quantity": qty, "status": "Delivered"})
    b.rel("TRANSPORTED_IN", "Batch", bid, "Shipment", s1)
    b.rel("SHIPPED_FROM", "Shipment", s1, "Location", mfr_loc)
    b.rel("DELIVERED_TO", "Shipment", s1, "Location", wh_loc)
    b.rel("HANDLED_BY", "Shipment", s1, "Organization", distributor)
    b.rel("STORED_AT", "Batch", bid, "Location", wh_loc)
    m0 = datetime(mfg.year, mfg.month, mfg.day, 8)
    _event(b, bid, "MANUFACTURED", m0, "Batch manufactured", "Location", mfr_loc)
    _event(b, bid, "QC_RELEASED", m0 + timedelta(days=7), "QC release", "Location", mfr_loc)
    _event(b, bid, "SHIPPED", t0, "Shipped to warehouse", "Location", mfr_loc)
    if not skip_received:
        _event(b, bid, "RECEIVED", t0 + timedelta(days=2), "Received at warehouse", "Location", wh_loc)
    for i, (ph, q) in enumerate(zip(dests, leg2_qty)):
        b.ship_n += 1
        s2 = f"SHP-{b.ship_n:04d}"
        dep = t0 + timedelta(days=5 + i)
        incomplete = open_last_leg and i == len(dests) - 1
        b.d["shipments"].append({"shipmentId": s2, "departureTime": dep.isoformat(),
                                 "arrivalTime": None if incomplete else (dep + timedelta(days=1)).isoformat(),
                                 "quantity": q, "status": "InTransit" if incomplete else "Delivered"})
        b.rel("TRANSPORTED_IN", "Batch", bid, "Shipment", s2)
        b.rel("FOLLOWED_BY", "Shipment", s1, "Shipment", s2)
        b.rel("SHIPPED_FROM", "Shipment", s2, "Location", wh_loc)
        b.rel("HANDLED_BY", "Shipment", s2, "Organization", distributor)
        if not incomplete:
            b.rel("DELIVERED_TO", "Shipment", s2, "Pharmacy", ph)
            b.rel("DISPENSED_AT", "Batch", bid, "Pharmacy", ph)
            _event(b, bid, "DELIVERED", dep + timedelta(days=1), f"Delivered to {ph}", "Pharmacy", ph)


def _split(total, k):
    base = total // k
    parts = [base] * k
    parts[0] += total - base * k
    return parts


def build_dataset() -> dict:
    b = _Builder()
    rng, d = b.rng, b.d
    for mid, name, code, cat, form in MEDICINES:
        d["medicines"].append({"medicineId": mid, "name": name, "drugCode": code, "category": cat, "form": form})
    for oid, n, r in MANUFACTURERS:
        d["organizations"].append({"organizationId": oid, "name": n, "role": "Manufacturer",
                                   "verificationStatus": "Verified", "region": r})
        d["locations"].append({"locationId": "LOC-" + oid[4:], "name": f"{n} Plant", "region": r,
                               "locationType": "ManufacturingSite"})
        b.rel("OPERATED_BY", "Location", "LOC-" + oid[4:], "Organization", oid)
    for oid, n, r, v in SUPPLIERS:
        d["organizations"].append({"organizationId": oid, "name": n, "role": "Supplier",
                                   "verificationStatus": v, "region": r})
    for oid, n, r in DISTRIBUTORS:
        d["organizations"].append({"organizationId": oid, "name": n, "role": "Distributor",
                                   "verificationStatus": "Verified", "region": r})
    for oid, n, r in WAREHOUSES:
        d["organizations"].append({"organizationId": oid, "name": n, "role": "WarehouseOperator",
                                   "verificationStatus": "Verified", "region": r})
        lid = "LOC-" + oid[4:]
        d["locations"].append({"locationId": lid, "name": n, "region": r, "locationType": "Warehouse"})
        b.rel("OPERATED_BY", "Location", lid, "Organization", oid)
    for i, r in enumerate(PHARMACY_REGIONS):
        d["pharmacies"].append({"pharmacyId": f"PH-{i + 1:02d}", "name": f"{PHARMACY_NAMES[i]} Pharmacy",
                                "region": r, "verificationStatus": "Verified"})

    wh_by_region = {r: [i for i, w in enumerate(WAREHOUSES) if w[2] == r] for r in REGIONS}
    ph_by_region = {r: [p["pharmacyId"] for p in d["pharmacies"] if p["region"] == r] for r in REGIONS}
    mfr_of_med = {m[0]: MANUFACTURERS[i // 2][0] for i, m in enumerate(MEDICINES)}
    verified_sup = [s[0] for s in SUPPLIERS if s[3] == "Verified"]
    lot_n = [0]

    def make_batch(bid, med, mfg: date, expiry: date, qty, region, lot=None, status="Released"):
        lot_n[0] += 1
        batch = {"batchId": bid, "lotNumber": lot or f"LOT-{lot_n[0]:04d}",
                 "manufacturingDate": mfg.isoformat(), "expiryDate": expiry.isoformat(),
                 "quantity": qty, "status": status, "intendedRegion": region}
        d["batches"].append(batch)
        b.rel("HAS_BATCH", "Medicine", med, "Batch", bid)
        b.rel("MANUFACTURES", "Organization", mfr_of_med[med], "Batch", bid)
        return batch

    def supply(bid, sup, material="Active ingredient"):
        b.rel("SUPPLIES_TO", "Organization", sup, "Batch", bid, material=material)

    def mfr_loc(med):
        return "LOC-" + mfr_of_med[med][4:]

    def std(bid, med_idx, k, region, mfg, qty=None, dest_n=None, sup=None):
        med = MEDICINES[med_idx][0]
        qty = qty or rng.choice([6000, 8000, 10000, 12000])
        batch = make_batch(bid, med, mfg, mfg.replace(year=mfg.year + 2), qty, region)
        for s in (sup or [rng.choice(verified_sup)]):
            supply(bid, s)
        whs = wh_by_region[region]
        wh = whs[k % len(whs)]
        phs = ph_by_region[region]
        n = min(dest_n or (2 + k % 2), len(phs))  # never target one pharmacy twice
        dests = [phs[(k + j) % len(phs)] for j in range(n)]
        dist = DISTRIBUTORS[(k + wh) % len(DISTRIBUTORS)][0]
        _route(b, batch, mfr_loc(med), wh, dests, _split(qty, n), dist)

    # S1: valid route (fixed id for demos)
    std("BATCH-VALID-001", 0, 0, "North", date(2026, 3, 2), qty=10000, dest_n=3, sup=["ORG-S01"])
    # 30 regular batches (all consistent)
    for n in range(1, 31):
        std(f"BATCH-{n:03d}", n % len(MEDICINES), n, REGIONS[n % 5], date(2026, 1 + (n % 8), 3 + (n % 20)))

    # S2: intended North, but one leg delivered to a South pharmacy
    batch = make_batch("BATCH-UNEXP-001", "MED-002", date(2026, 4, 6), date(2028, 4, 6), 8000, "North")
    supply("BATCH-UNEXP-001", "ORG-S01")
    _route(b, batch, mfr_loc("MED-002"), 0, [ph_by_region["North"][0], ph_by_region["South"][0]],
           [4000, 4000], DISTRIBUTORS[0][0])
    # S3: unverified supplier
    batch = make_batch("BATCH-UNVER-001", "MED-003", date(2026, 5, 4), date(2028, 5, 4), 6000, "Central")
    supply("BATCH-UNVER-001", "ORG-S05", "Excipient")
    supply("BATCH-UNVER-001", "ORG-S03")
    _route(b, batch, mfr_loc("MED-003"), 7, ph_by_region["Central"][:2], [3000, 3000], DISTRIBUTORS[4][0])
    # S4: expired batch (expiry before AS_OF)
    batch = make_batch("BATCH-EXPIRED-001", "MED-004", date(2024, 3, 10), date(2026, 3, 10), 6000, "South",
                       status="Expired")
    supply("BATCH-EXPIRED-001", "ORG-S02")
    _route(b, batch, mfr_loc("MED-004"), 2, ph_by_region["South"][:2], [3000, 3000], DISTRIBUTORS[1][0])
    # S5: same lotNumber on two different batches/manufacturers
    for bid, med, wh, rgn in [("BATCH-DUP-001", "MED-005", 4, "East"), ("BATCH-DUP-002", "MED-007", 5, "West")]:
        batch = make_batch(bid, med, date(2026, 6, 8), date(2028, 6, 8), 5000, rgn, lot="LOT-CONFLICT-77")
        supply(bid, "ORG-S03")
        _route(b, batch, mfr_loc(med), wh, ph_by_region[rgn][:1], [5000], DISTRIBUTORS[2][0])
    # S6: downstream legs total 800 more than the inbound shipment
    batch = make_batch("BATCH-QTY-001", "MED-006", date(2026, 6, 15), date(2028, 6, 15), 10000, "West")
    supply("BATCH-QTY-001", "ORG-S04")
    _route(b, batch, mfr_loc("MED-006"), 5, ph_by_region["West"][:2], [5400, 5400], DISTRIBUTORS[3][0])
    # S7: two recalled batches sharing a supplier lot; each stays inside its intended region,
    #     so the recall reaches 6 pharmacies across 2 regions without any routing anomaly.
    for bid, wh_i, rgn, k in [("BATCH-RECALL-001", 2, "South", 0), ("BATCH-RECALL-002", 7, "Central", 1)]:
        batch = make_batch(bid, "MED-001", date(2026, 5, 20 + k), date(2028, 5, 20 + k), 12000, rgn,
                           status="Recalled")
        supply(bid, "ORG-S02", "Active ingredient (lot SUP-LOT-9917)")
        dests = ph_by_region[rgn]
        _route(b, batch, mfr_loc("MED-001"), wh_i, dests, _split(12000, len(dests)), DISTRIBUTORS[1 + k][0])
    d["recalls"].append({"recallId": "RCL-001", "status": "Active", "issuedAt": "2026-09-20T10:00:00",
                         "reason": "Simulated: suspected contamination in supplier ingredient lot SUP-LOT-9917"})
    d["recalls"].append({"recallId": "RCL-002", "status": "Closed", "issuedAt": "2026-02-01T10:00:00",
                         "reason": "Simulated: labelling error, resolved"})
    for bid in SCENARIOS["S7_RECALLED_MULTI_DESTINATION"]:
        b.rel("AFFECTED_BY", "Batch", bid, "Recall", "RCL-001")
    b.rel("AFFECTED_BY", "Batch", "BATCH-004", "Recall", "RCL-002")
    # S8: missing RECEIVED event + last downstream leg has no destination
    batch = make_batch("BATCH-INCOMPLETE-001", "MED-008", date(2026, 7, 7), date(2028, 7, 7), 6000, "East")
    supply("BATCH-INCOMPLETE-001", "ORG-S03")
    _route(b, batch, mfr_loc("MED-008"), 4, ph_by_region["East"][:2], [3000, 3000], DISTRIBUTORS[5][0],
           skip_received=True, open_last_leg=True)
    return d


def summary(d: dict) -> dict:
    keys = ["medicines", "organizations", "locations", "pharmacies", "batches", "shipments", "recalls", "events"]
    return {"nodes": {k: len(d[k]) for k in keys},
            "totalNodes": sum(len(d[k]) for k in keys),
            "relationships": dict(sorted(Counter(r["type"] for r in d["rels"]).items())),
            "totalRelationships": len(d["rels"])}


if __name__ == "__main__":
    import json
    print(json.dumps(summary(build_dataset()), indent=2))
