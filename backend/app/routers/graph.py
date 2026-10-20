from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from ..config import Settings, get_settings
from ..db import ID_KEY, REL_TYPES, Neo4jClient, merge_graphs
from ..deps import get_client, node_id_or_400
from ..services import graphs

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/demo")
def demo(batchId: str = "BATCH-RECALL-001", client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    """Seeded demonstration graph used on the home page (real Neo4j data)."""
    g = graphs.trace_graph(client, batchId, "both", True, s.max_graph_nodes)
    if not g["nodes"]:
        raise HTTPException(404, detail=f"Batch {batchId} not found. Has the dataset been loaded?")
    return {"batchId": batchId, **g}


@router.get("/search")
def search(q: Annotated[str, Query(min_length=1, max_length=60)],
           labels: Annotated[list[str] | None, Query()] = None,
           limit: Annotated[int, Query(ge=1, le=50)] = 20,
           client: Neo4jClient = Depends(get_client)):
    use = labels or list(ID_KEY)
    bad = [l for l in use if l not in ID_KEY]
    if bad:
        raise HTTPException(400, detail=f"Unknown label(s): {bad}")
    rows = client.read_raw("""MATCH (n) WHERE any(l IN labels(n) WHERE l IN $labels)
        AND any(k IN ['name','batchId','medicineId','organizationId','locationId','shipmentId','pharmacyId','recallId','drugCode','lotNumber']
                WHERE toLower(toString(n[k])) CONTAINS toLower($q))
        RETURN n LIMIT $limit""", labels=use, q=q, limit=limit)
    g = graphs.build(rows)
    return {"results": g["nodes"], "count": len(g["nodes"])}


@router.get("/neighbors/{node_id}")
def neighbors(node_id: str, limit: Annotated[int, Query(ge=1, le=100)] = 25,
              relTypes: Annotated[list[str] | None, Query()] = None,
              client: Neo4jClient = Depends(get_client)):
    label, ident = node_id_or_400(node_id)
    types = relTypes or REL_TYPES
    if any(t not in REL_TYPES for t in types):
        raise HTTPException(400, detail="Unknown relationship type")
    g = client.graph(f"MATCH (n:{label} {{{ID_KEY[label]}: $id}})-[r]-(m) WHERE type(r) IN $types "
                     "RETURN n, r, m LIMIT $limit", id=ident, types=types, limit=limit)
    if not g["nodes"]:
        # distinguish "no neighbours" from "node does not exist"
        if not client.rows(f"MATCH (n:{label} {{{ID_KEY[label]}: $id}}) RETURN 1 AS x", id=ident):
            raise HTTPException(404, detail=f"{node_id} not found")
    return {"center": node_id, **g, "limit": limit}


@router.get("/node/{node_id}")
def node_detail(node_id: str, client: Neo4jClient = Depends(get_client)):
    label, ident = node_id_or_400(node_id)
    rows = client.rows(f"MATCH (n:{label} {{{ID_KEY[label]}: $id}}) RETURN n, COUNT {{ (n)--() }} AS degree", id=ident)
    if not rows:
        raise HTTPException(404, detail=f"{node_id} not found")
    conns = client.rows(f"MATCH (n:{label} {{{ID_KEY[label]}: $id}})-[r]-() "
                        "RETURN type(r) AS type, startNode(r) = n AS outgoing, count(*) AS count ORDER BY type", id=ident)
    return {"node": rows[0]["n"], "degree": rows[0]["degree"], "connections": conns}


@router.get("/relationship/{element_id:path}")
def relationship(element_id: str, client: Neo4jClient = Depends(get_client)):
    g = client.graph("MATCH (a)-[r]->(b) WHERE elementId(r) = $id RETURN a, r, b", id=element_id)
    if not g["edges"]:
        raise HTTPException(404, detail="Relationship not found")
    e = g["edges"][0]
    names = {n["id"]: n for n in g["nodes"]}
    return {"relationship": e, "source": names[e["source"]], "target": names[e["target"]]}


@router.get("/path")
def path(fromId: str, toId: str, maxHops: Annotated[int, Query(ge=1, le=10)] = 8,
         client: Neo4jClient = Depends(get_client)):
    la, ia = node_id_or_400(fromId)
    lb, ib = node_id_or_400(toId)
    g = client.graph(f"MATCH (a:{la} {{{ID_KEY[la]}: $a}}), (b:{lb} {{{ID_KEY[lb]}: $b}}) "
                     f"MATCH p = shortestPath((a)-[*..{int(maxHops)}]-(b)) RETURN p", a=ia, b=ib)
    if not g["nodes"]:
        raise HTTPException(404, detail="No path found within the hop limit (or an endpoint does not exist).")
    return {"fromId": fromId, "toId": toId, "hops": len(g["edges"]), **g}
