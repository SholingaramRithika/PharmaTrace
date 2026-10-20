from __future__ import annotations
from fastapi import APIRouter, Depends
from ..db import Neo4jClient, plan_to_dict, total_db_hits
from ..deps import get_client

router = APIRouter(prefix="/api/insights", tags=["insights"])

PROFILES = [
    ("Unique-index lookup", "PROFILE MATCH (b:Batch {batchId: 'BATCH-RECALL-001'}) RETURN b"),
    ("Two-hop downstream traversal", "PROFILE MATCH (b:Batch {batchId: 'BATCH-RECALL-001'})-[:TRANSPORTED_IN]->(:Shipment)-[:DELIVERED_TO]->(p:Pharmacy) RETURN count(p) AS c"),
    ("Property filter on indexed date", "PROFILE MATCH (b:Batch) WHERE b.expiryDate < date('2026-10-18') RETURN count(b) AS c"),
]


@router.get("")
def insights(client: Neo4jClient = Depends(get_client)):
    labels = client.rows("MATCH (n) UNWIND labels(n) AS l RETURN l AS label, count(*) AS count ORDER BY count DESC")
    rels = client.rows("MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY count DESC")
    schema = client.rows("MATCH (a)-[r]->(b) RETURN labels(a)[0] AS source, type(r) AS type, labels(b)[0] AS target, count(*) AS count ORDER BY source, type")
    degree = client.rows("""MATCH (n) WITH n, COUNT { (n)--() } AS degree
        RETURN labels(n)[0] AS label, coalesce(n.name, n.batchId, n.shipmentId, n.eventId) AS entity, degree ORDER BY degree DESC LIMIT 10""")
    dist = client.rows("""MATCH (n) WITH COUNT { (n)--() } AS d RETURN min(d) AS min, max(d) AS max, round(avg(d), 2) AS avg, count(*) AS nodes""")
    idx = client.rows("SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state RETURN name, type, entityType, labelsOrTypes, properties, state ORDER BY name")
    cons = client.rows("SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties RETURN name, type, entityType, labelsOrTypes, properties ORDER BY name")
    profiles = []
    for title, q in PROFILES:
        res = client.run_lab(q, {}, False)
        profiles.append({"title": title, "cypher": q, "plan": res["plan"], "totalDbHits": total_db_hits(res["plan"]),
                         "timing": res["timing"], "rows": len(res["rows"])})
    return {"nodesByLabel": labels, "relationshipsByType": rels, "totalNodes": sum(l["count"] for l in labels),
            "totalRelationships": sum(r["count"] for r in rels), "schemaTriples": schema, "topDegree": degree,
            "degreeStats": dist[0] if dist else None, "indexes": idx, "constraints": cons, "profiles": profiles,
            "note": "All figures are measured live from this Neo4j instance; timings depend on hardware and cache state."}
