from __future__ import annotations
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import PlainTextResponse
from ..config import Settings, get_settings
from ..db import Neo4jClient
from ..deps import get_client
from ..services import graphs
from ..services.risk import compute_findings, REQUIRED_EVENTS

router = APIRouter(prefix="/api/traceability", tags=["traceability"])
BatchId = Path(pattern=r"^[A-Za-z0-9\-]{3,40}$")


def _details(client: Neo4jClient, batch_id: str) -> dict | None:
    head = client.rows("""MATCH (b:Batch {batchId: $id})
        OPTIONAL MATCH (m:Medicine)-[:HAS_BATCH]->(b) OPTIONAL MATCH (o:Organization)-[:MANUFACTURES]->(b)
        RETURN b, m, collect(DISTINCT o) AS manufacturers""", id=batch_id)
    if not head:
        return None
    suppliers = client.rows("""MATCH (o:Organization)-[r:SUPPLIES_TO]->(b:Batch {batchId: $id})
        RETURN o, r.material AS material""", id=batch_id)
    shipments = client.rows("""MATCH (b:Batch {batchId: $id})-[:TRANSPORTED_IN]->(s:Shipment)
        OPTIONAL MATCH (s)-[:SHIPPED_FROM]->(f) OPTIONAL MATCH (s)-[:DELIVERED_TO]->(t) OPTIONAL MATCH (s)-[:HANDLED_BY]->(d)
        OPTIONAL MATCH (prev:Shipment)-[:FOLLOWED_BY]->(s)
        RETURN s, f.name AS origin, labels(t)[0] AS destinationType, t.name AS destination, t.region AS destinationRegion,
               d.name AS carrier, prev.shipmentId AS previousLeg ORDER BY s.departureTime""", id=batch_id)
    events = client.rows("""MATCH (b:Batch {batchId: $id})-[:HAS_EVENT]->(e:TraceabilityEvent)
        OPTIONAL MATCH (e)-[:RECORDED_AT]->(x)
        RETURN e, x.name AS location ORDER BY e.timestamp""", id=batch_id)
    recalls = client.rows("MATCH (b:Batch {batchId: $id})-[:AFFECTED_BY]->(r:Recall) RETURN r", id=batch_id)
    h = head[0]
    return {"batch": h["b"], "medicine": h["m"], "manufacturers": h["manufacturers"], "suppliers": suppliers,
            "shipments": shipments, "events": events, "recalls": recalls}


@router.get("/{batch_id}")
def trace(batch_id: str = BatchId, direction: Literal["both", "upstream", "downstream"] = "both",
          client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    d = _details(client, batch_id)
    if d is None:
        raise HTTPException(404, detail=f"Batch '{batch_id}' was not found in the database.")
    issues = [f for f in compute_findings(client, s.as_of_date)["findings"] if f["batchId"] == batch_id]
    events_have = {e["e"]["properties"]["eventType"] for e in d["events"]}
    gaps = [f"Missing event: {t}" for t in REQUIRED_EVENTS if t not in events_have]
    gaps += [f"Shipment {x['s']['properties']['shipmentId']} has no recorded destination"
             for x in d["shipments"] if not x["destination"]]
    graph = graphs.trace_graph(client, batch_id, direction, True, s.max_graph_nodes)
    return {**d, "issues": issues, "gaps": gaps, "graph": graph, "direction": direction,
            "note": "No relationships are inferred: gaps are reported, not filled in."}


@router.get("/{batch_id}/report", response_class=PlainTextResponse)
def report(batch_id: str = BatchId, client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    d = trace(batch_id, "both", client, s)
    b = d["batch"]["properties"]
    L = [f"# Traceability report: {batch_id}", "",
         "_Synthetic dataset. Findings are indicators, not proof of misconduct._", "",
         f"- Medicine: {d['medicine']['properties']['name'] if d['medicine'] else 'UNKNOWN'}",
         f"- Manufacturer(s): {', '.join(m['properties']['name'] for m in d['manufacturers']) or 'UNKNOWN'}",
         f"- Manufactured: {b.get('manufacturingDate')}  Expires: {b.get('expiryDate')}",
         f"- Quantity: {b.get('quantity')}  Status: {b.get('status')}", "", "## Suppliers"]
    L += [f"- {x['o']['properties']['name']} ({x['o']['properties']['verificationStatus']}) - {x['material']}" for x in d["suppliers"]] or ["- none recorded"]
    L += ["", "## Shipments"]
    L += [f"- {x['s']['properties']['shipmentId']}: {x['origin']} -> {x['destination'] or 'NO DESTINATION RECORDED'} "
          f"(qty {x['s']['properties']['quantity']}, carrier {x['carrier']})" for x in d["shipments"]]
    L += ["", "## Events"]
    L += [f"- {x['e']['properties']['timestamp']} {x['e']['properties']['eventType']} @ {x['location']}" for x in d["events"]]
    L += ["", "## Gaps and findings"] + [f"- {g}" for g in d["gaps"]] + [f"- [{i['severity']}] {i['ruleTitle']}: {i['explanation']}" for i in d["issues"]]
    if not d["gaps"] and not d["issues"]:
        L.append("- none")
    return PlainTextResponse("\n".join(L), headers={"Content-Disposition": f'attachment; filename="trace_{batch_id}.md"'})
