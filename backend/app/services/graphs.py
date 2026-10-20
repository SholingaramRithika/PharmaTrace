"""Bounded graph builders shared by routers."""
from __future__ import annotations
from ..db import Neo4jClient, build_graph, merge_graphs

build = build_graph


def trace_graph(client: Neo4jClient, batch_id: str, direction: str = "both", events: bool = True, limit: int = 300) -> dict:
    parts = []
    if direction in ("both", "upstream"):
        parts += [
            client.graph("MATCH p = (x)-[:HAS_BATCH|MANUFACTURES|SUPPLIES_TO]->(b:Batch {batchId: $id}) RETURN p", id=batch_id),
            client.graph("MATCH p = (l:Location)-[:OPERATED_BY]->(:Organization)-[:MANUFACTURES]->(b:Batch {batchId: $id}) RETURN p", id=batch_id),
        ]
    if direction in ("both", "downstream"):
        parts += [
            client.graph("MATCH p = (b:Batch {batchId: $id})-[:TRANSPORTED_IN]->(s:Shipment)-[:SHIPPED_FROM|DELIVERED_TO|HANDLED_BY]->(x) RETURN p LIMIT 200", id=batch_id),
            client.graph("MATCH p = (b:Batch {batchId: $id})-[:TRANSPORTED_IN]->(s1:Shipment)-[:FOLLOWED_BY]->(s2:Shipment) RETURN p LIMIT 100", id=batch_id),
            client.graph("MATCH p = (b:Batch {batchId: $id})-[:STORED_AT]->(l:Location) RETURN p", id=batch_id),
            client.graph("MATCH p = (b:Batch {batchId: $id})-[:AFFECTED_BY]->(r:Recall) RETURN p", id=batch_id),
        ]
    if events:
        parts.append(client.graph("MATCH p = (b:Batch {batchId: $id})-[:HAS_EVENT]->(e:TraceabilityEvent)-[:RECORDED_AT]->(x) RETURN p LIMIT 100", id=batch_id))
    if direction == "upstream":
        parts.append(client.graph("MATCH p = (b:Batch {batchId: $id})-[:AFFECTED_BY]->(r:Recall) RETURN p", id=batch_id))
    g = merge_graphs(*parts, limit=limit)
    if not any(n["id"] == f"Batch:{batch_id}" for n in g["nodes"]):
        return {"nodes": [], "edges": [], "truncated": False}
    return g
