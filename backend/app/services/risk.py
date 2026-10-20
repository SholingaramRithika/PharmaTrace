"""Rule-based, explainable risk findings (SIMULATED indicators; not proof of fraud).

Score: each finding carries a severity weight (High=3, Medium=2, Low=1). A batch's
riskScore is the sum of its findings' weights; bands: 0 none, 1-2 low, 3-4 elevated, >=5 high.
"""
from __future__ import annotations
from collections import Counter

WEIGHT = {"High": 3, "Medium": 2, "Low": 1}
REQUIRED_EVENTS = ["MANUFACTURED", "QC_RELEASED", "SHIPPED", "RECEIVED"]
NOT_TEST = "coalesce(b.isTestRecord, false) = false"
DISCLAIMER = ("All findings are rule-based indicators computed on a SYNTHETIC dataset. "
              "An indicator is a prompt to investigate, not proof of fraud or misconduct.")


def _bid(b): return f"Batch:{b}"


RULES = [
 {"rule": "DUPLICATE_LOT", "title": "Conflicting lot identifier", "severity": "High",
  "cypher": f"""MATCH (b:Batch) WHERE {NOT_TEST} AND b.lotNumber IS NOT NULL
WITH b.lotNumber AS lot, collect(b) AS bs WHERE size(bs) > 1
UNWIND bs AS b
OPTIONAL MATCH (m:Organization)-[:MANUFACTURES]->(b)
RETURN b.batchId AS batchId, lot AS lotNumber, [x IN bs | x.batchId] AS batches,
       collect(DISTINCT m.organizationId) AS manufacturers""",
  "build": lambda r: dict(
      evidence={"lotNumber": r["lotNumber"], "batchesSharingLot": r["batches"], "manufacturers": r["manufacturers"]},
      nodes=[_bid(x) for x in r["batches"]] + [f"Organization:{m}" for m in r["manufacturers"]],
      explanation=f"Lot {r['lotNumber']} is attached to {len(r['batches'])} different batches ({', '.join(r['batches'])}). "
                  "A lot number should map to one production run.",
      action="Compare batch records and manufacturer documents for each batch sharing the lot; quarantine until reconciled.")},
 {"rule": "UNVERIFIED_SUPPLIER", "title": "Unverified supplier in batch lineage", "severity": "High",
  "cypher": f"""MATCH (o:Organization)-[r:SUPPLIES_TO]->(b:Batch)
WHERE o.verificationStatus <> 'Verified' AND {NOT_TEST}
RETURN b.batchId AS batchId, o.organizationId AS orgId, o.name AS supplier,
       o.verificationStatus AS status, r.material AS material""",
  "build": lambda r: dict(
      evidence={"supplier": r["supplier"], "verificationStatus": r["status"], "material": r["material"]},
      nodes=[_bid(r["batchId"]), f"Organization:{r['orgId']}"],
      explanation=f"Supplier {r['supplier']} (status: {r['status']}) supplied '{r['material']}' used in this batch.",
      action="Request supplier credentials and certificates of analysis; hold the batch until the supplier is verified.")},
 {"rule": "UNEXPECTED_ROUTE", "title": "Delivery outside intended region", "severity": "Medium",
  "cypher": f"""MATCH (b:Batch)-[:TRANSPORTED_IN]->(s:Shipment)-[:DELIVERED_TO]->(p:Pharmacy)
WHERE p.region <> b.intendedRegion AND {NOT_TEST}
RETURN b.batchId AS batchId, b.intendedRegion AS intended, p.pharmacyId AS pharmacyId,
       p.name AS pharmacy, p.region AS actual, s.shipmentId AS shipmentId""",
  "build": lambda r: dict(
      evidence={"intendedRegion": r["intended"], "deliveredRegion": r["actual"], "pharmacy": r["pharmacy"], "shipment": r["shipmentId"]},
      nodes=[_bid(r["batchId"]), f"Shipment:{r['shipmentId']}", f"Pharmacy:{r['pharmacyId']}"],
      explanation=f"Batch was intended for {r['intended']} but shipment {r['shipmentId']} was delivered to {r['pharmacy']} in {r['actual']}.",
      action="Review distributor routing records and authorisation for the out-of-region transfer.")},
 {"rule": "EXPIRED_BATCH", "title": "Batch past expiry date", "severity": "High",
  "params": lambda ctx: {"asOf": ctx["asOf"]},
  "cypher": f"""MATCH (b:Batch) WHERE b.expiryDate < date($asOf) AND {NOT_TEST}
OPTIONAL MATCH (b)-[:DISPENSED_AT]->(p:Pharmacy)
RETURN b.batchId AS batchId, toString(b.expiryDate) AS expiry, b.status AS status,
       collect(p.pharmacyId) AS pharmacies""",
  "build": lambda r: dict(
      evidence={"expiryDate": r["expiry"], "status": r["status"], "pharmaciesHoldingStock": r["pharmacies"]},
      nodes=[_bid(r["batchId"])] + [f"Pharmacy:{p}" for p in r["pharmacies"]],
      explanation=f"Expiry date {r['expiry']} is before the reference date; stock was delivered to {len(r['pharmacies'])} pharmacies.",
      action="Confirm withdrawal of remaining stock from the listed pharmacies and record disposal.")},
 {"rule": "QUANTITY_MISMATCH", "title": "Shipment quantity inconsistency", "severity": "Medium",
  "cypher": f"""MATCH (b:Batch)-[:TRANSPORTED_IN]->(s1:Shipment)
WHERE NOT ()-[:FOLLOWED_BY]->(s1) AND {NOT_TEST}
OPTIONAL MATCH (s1)-[:FOLLOWED_BY]->(s2:Shipment)
WITH b, s1, coalesce(sum(s2.quantity), 0) AS downstream
WHERE downstream > s1.quantity OR s1.quantity > b.quantity
RETURN b.batchId AS batchId, s1.shipmentId AS shipmentId, s1.quantity AS inbound,
       downstream, b.quantity AS batchQuantity""",
  "build": lambda r: dict(
      evidence={"inboundShipmentQty": r["inbound"], "downstreamQtySum": r["downstream"], "batchQty": r["batchQuantity"]},
      nodes=[_bid(r["batchId"]), f"Shipment:{r['shipmentId']}"],
      explanation=f"Downstream legs total {r['downstream']} units but the inbound shipment carried {r['inbound']} (batch size {r['batchQuantity']}).",
      action="Reconcile shipment manifests and goods-receipt records for each leg.")},
 {"rule": "MISSING_EVENT", "title": "Missing traceability event", "severity": "Medium",
  "params": lambda ctx: {"required": REQUIRED_EVENTS},
  "cypher": f"""MATCH (b:Batch) WHERE {NOT_TEST}
OPTIONAL MATCH (b)-[:HAS_EVENT]->(e:TraceabilityEvent)
WITH b, collect(DISTINCT e.eventType) AS types
WITH b, types, [t IN $required WHERE NOT t IN types] AS missing
WHERE size(missing) > 0
RETURN b.batchId AS batchId, missing, types""",
  "build": lambda r: dict(
      evidence={"missingEventTypes": r["missing"], "recordedEventTypes": r["types"]},
      nodes=[_bid(r["batchId"])],
      explanation=f"Expected lifecycle events not recorded: {', '.join(r['missing'])}.",
      action="Ask the responsible party to supply the missing scan/event record or document why it is absent.")},
 {"rule": "INCOMPLETE_PATH", "title": "Incomplete supply chain path", "severity": "Medium",
  "cypher": f"""MATCH (b:Batch) WHERE {NOT_TEST}
OPTIONAL MATCH (b)-[:TRANSPORTED_IN]->(s:Shipment) WHERE NOT (s)-[:DELIVERED_TO]->()
WITH b, collect(s.shipmentId) AS openShipments
OPTIONAL MATCH (m:Organization)-[:MANUFACTURES]->(b)
OPTIONAL MATCH (med:Medicine)-[:HAS_BATCH]->(b)
WITH b, openShipments, count(DISTINCT m) AS mfrs, count(DISTINCT med) AS meds
WHERE size(openShipments) > 0 OR mfrs = 0 OR meds = 0
RETURN b.batchId AS batchId, openShipments, mfrs, meds""",
  "build": lambda r: dict(
      evidence={"shipmentsWithoutDestination": r["openShipments"], "manufacturerLinks": r["mfrs"], "medicineLinks": r["meds"]},
      nodes=[_bid(r["batchId"])] + [f"Shipment:{s}" for s in r["openShipments"]],
      explanation=("Shipment(s) " + ", ".join(r["openShipments"]) + " have no recorded destination. ") if r["openShipments"]
                  else "Batch lacks a manufacturer or medicine link.",
      action="Locate the destination for the open shipment(s) or confirm they were lost/returned.")},
]


def band(score: int) -> str:
    return "none" if score == 0 else "low" if score <= 2 else "elevated" if score <= 4 else "high"


def compute_findings(client, as_of: str) -> dict:
    findings = []
    ctx = {"asOf": as_of}
    for rule in RULES:
        params = rule.get("params", lambda c: {})(ctx)
        for r in client.rows(rule["cypher"], **params):
            b = rule["build"](r)
            ent = r["batchId"]
            findings.append({
                "findingId": f"RF-{rule['rule']}-{r['batchId']}" + (f"-{r['pharmacyId']}" if r.get("pharmacyId") and rule["rule"] == "UNEXPECTED_ROUTE" else "")
                             + (f"-{r['orgId']}" if r.get("orgId") else ""),
                "rule": rule["rule"], "ruleTitle": rule["title"], "severity": rule["severity"],
                "batchId": ent, "affectedEntity": {"label": "Batch", "id": ent},
                "evidence": b["evidence"], "evidenceNodeIds": sorted(set(b["nodes"])),
                "explanation": b["explanation"], "recommendedAction": b["action"], "synthetic": True})
    scores: Counter = Counter()
    for f in findings:
        scores[f["batchId"]] += WEIGHT[f["severity"]]
    for f in findings:
        f["batchRiskScore"] = scores[f["batchId"]]
        f["batchRiskBand"] = band(scores[f["batchId"]])
    order = {"High": 0, "Medium": 1, "Low": 2}
    findings.sort(key=lambda f: (order[f["severity"]], f["batchId"], f["rule"]))
    return {"findings": findings, "disclaimer": DISCLAIMER,
            "summary": {"total": len(findings), "bySeverity": dict(Counter(f["severity"] for f in findings)),
                        "byRule": dict(Counter(f["rule"] for f in findings)),
                        "batchesWithFindings": len(scores)},
            "scoring": {"weights": WEIGHT, "bands": {"none": 0, "low": "1-2", "elevated": "3-4", "high": ">=5"}}}
