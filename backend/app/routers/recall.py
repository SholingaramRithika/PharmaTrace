from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import PlainTextResponse
from ..config import Settings, get_settings
from ..db import Neo4jClient, merge_graphs
from ..deps import get_client

router = APIRouter(prefix="/api/recall", tags=["recall"])
RecallId = Path(pattern=r"^RCL-[0-9]{3}$")


@router.get("")
def list_recalls(client: Neo4jClient = Depends(get_client)):
    rows = client.rows("""MATCH (r:Recall) OPTIONAL MATCH (r)<-[:AFFECTED_BY]-(b:Batch)
        RETURN r, count(b) AS batches ORDER BY r.issuedAt DESC""")
    return {"recalls": [{**x["r"]["properties"], "batches": x["batches"]} for x in rows]}


def _impact(client: Neo4jClient, rid: str, limit: int) -> dict:
    head = client.rows("MATCH (r:Recall {recallId: $id}) RETURN r", id=rid)
    if not head:
        raise HTTPException(404, detail=f"Recall {rid} not found")
    batches = client.rows("""MATCH (r:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch)
        RETURN b.batchId AS batchId, b.quantity AS quantity, b.status AS status, toString(b.expiryDate) AS expiry ORDER BY b.batchId""", id=rid)
    dest = client.rows("""MATCH (r:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch)-[:TRANSPORTED_IN]->(s:Shipment)-[:DELIVERED_TO]->(p:Pharmacy)
        RETURN p.pharmacyId AS pharmacyId, p.name AS name, p.region AS region,
               collect(DISTINCT b.batchId) AS batches, sum(s.quantity) AS units ORDER BY units DESC""", id=rid)
    whs = client.rows("""MATCH (:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch)-[:STORED_AT]->(l:Location)
        RETURN l.locationId AS locationId, l.name AS name, collect(DISTINCT b.batchId) AS batches""", id=rid)
    dists = client.rows("""MATCH (:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch)-[:TRANSPORTED_IN]->(:Shipment)-[:HANDLED_BY]->(d:Organization)
        RETURN d.organizationId AS organizationId, d.name AS name, collect(DISTINCT b.batchId) AS batches""", id=rid)
    open_legs = client.rows("""MATCH (:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch)-[:TRANSPORTED_IN]->(s:Shipment)
        WHERE NOT (s)-[:DELIVERED_TO]->() RETURN b.batchId AS batchId, s.shipmentId AS shipmentId, s.quantity AS quantity""", id=rid)
    ids = [d["pharmacyId"] for d in dest]
    unaffected = client.rows("MATCH (p:Pharmacy) WHERE NOT p.pharmacyId IN $ids RETURN p.pharmacyId AS pharmacyId, p.name AS name, p.region AS region ORDER BY p.pharmacyId", ids=ids)
    graph = merge_graphs(*[client.graph(q, id=rid) for q in [
        "MATCH p = (r:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch) RETURN p",
        "MATCH p = (:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch)-[:TRANSPORTED_IN]->(s:Shipment)-[:DELIVERED_TO|HANDLED_BY|SHIPPED_FROM]->(x) RETURN p LIMIT 250",
        "MATCH p = (:Recall {recallId: $id})<-[:AFFECTED_BY]-(b:Batch)-[:STORED_AT]->(l:Location) RETURN p"]], limit=limit)
    return {"recall": head[0]["r"]["properties"], "affectedBatches": batches, "affectedPharmacies": dest,
            "affectedWarehouses": whs, "distributors": dists, "unaffectedPharmacies": unaffected,
            "totals": {"batches": len(batches), "batchUnits": sum(b["quantity"] or 0 for b in batches),
                       "unitsDeliveredToPharmacies": sum(d["units"] or 0 for d in dest),
                       "pharmacies": len(dest), "warehouses": len(whs), "distributors": len(dists)},
            "limitations": ([f"{len(open_legs)} shipment leg(s) have no recorded destination, so some stock may be untraced: "
                             + ", ".join(o["shipmentId"] for o in open_legs)] if open_legs else [])
                           + ["Units delivered = sum of shipment quantities to pharmacies; dispensed/sold units are not modelled."],
            "graph": graph, "highlight": [n["id"] for n in graph["nodes"]]}


@router.get("/{recall_id}/impact")
def impact(recall_id: str = RecallId, client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    return _impact(client, recall_id, s.max_graph_nodes)


@router.get("/{recall_id}/report", response_class=PlainTextResponse)
def report(recall_id: str = RecallId, client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    i = _impact(client, recall_id, s.max_graph_nodes)
    r, t = i["recall"], i["totals"]
    L = [f"# Recall impact report: {recall_id}", "", "_Synthetic dataset._", "",
         f"- Reason: {r['reason']}", f"- Status: {r['status']}  Issued: {r['issuedAt']}",
         f"- Affected batches: {t['batches']} ({t['batchUnits']} units manufactured)",
         f"- Units delivered to pharmacies: {t['unitsDeliveredToPharmacies']} across {t['pharmacies']} pharmacies",
         "", "## Affected pharmacies"] + [f"- {p['name']} ({p['region']}): {p['units']} units, batches {', '.join(p['batches'])}" for p in i["affectedPharmacies"]]
    L += ["", "## Limitations"] + [f"- {x}" for x in i["limitations"]]
    return PlainTextResponse("\n".join(L), headers={"Content-Disposition": f'attachment; filename="recall_{recall_id}.md"'})
