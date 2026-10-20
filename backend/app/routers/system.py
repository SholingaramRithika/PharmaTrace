from __future__ import annotations
from fastapi import APIRouter, Depends
from ..config import Settings, get_settings
from ..db import Neo4jClient
from ..deps import get_client
from ..services.risk import compute_findings

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health(client: Neo4jClient = Depends(get_client)):
    """Real connectivity check: never reports 'connected' unless the driver verified it."""
    try:
        client.verify()
        n = client.rows("MATCH (n) RETURN count(n) AS nodes")[0]["nodes"]
        return {"status": "ok", "database": {"connected": True, "nodes": n}}
    except Exception as e:  # noqa: BLE001
        return {"status": "degraded", "database": {"connected": False, "error": type(e).__name__}}


@router.get("/overview")
def overview(client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    labels = {r["l"]: r["c"] for r in client.rows("MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS c")}
    rels = {r["t"]: r["c"] for r in client.rows("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c")}
    status = client.rows("""MATCH (b:Batch) RETURN b.status AS status, count(*) AS count ORDER BY count DESC""")
    events = client.rows("""MATCH (b:Batch)-[:HAS_EVENT]->(e:TraceabilityEvent)
        RETURN e.eventId AS eventId, e.eventType AS eventType, e.timestamp AS timestamp,
               e.description AS description, b.batchId AS batchId ORDER BY e.timestamp DESC LIMIT 8""")
    recalls = client.rows("""MATCH (r:Recall) OPTIONAL MATCH (r)<-[:AFFECTED_BY]-(b:Batch)
        RETURN r.recallId AS recallId, r.status AS status, r.reason AS reason, r.issuedAt AS issuedAt,
               count(b) AS batches ORDER BY r.issuedAt DESC""")
    risk = compute_findings(client, s.as_of_date)
    return {"counts": {"medicines": labels.get("Medicine", 0), "batches": labels.get("Batch", 0),
                       "organizations": labels.get("Organization", 0), "shipments": labels.get("Shipment", 0),
                       "pharmacies": labels.get("Pharmacy", 0), "locations": labels.get("Location", 0),
                       "recalls": labels.get("Recall", 0), "events": labels.get("TraceabilityEvent", 0),
                       "relationships": sum(rels.values()), "nodes": sum(labels.values())},
            "byLabel": labels, "byRelationship": rels, "batchStatus": status, "recentEvents": events,
            "recalls": recalls, "riskSummary": risk["summary"], "asOf": s.as_of_date}
