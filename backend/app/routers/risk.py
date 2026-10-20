from __future__ import annotations
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from ..config import Settings, get_settings
from ..db import Neo4jClient
from ..deps import get_client
from ..services import graphs
from ..services.risk import compute_findings

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/findings")
def findings(severity: Literal["High", "Medium", "Low"] | None = None, rule: str | None = None,
             q: Annotated[str | None, Query(max_length=60)] = None,
             client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    r = compute_findings(client, s.as_of_date)
    items = [f for f in r["findings"] if (not severity or f["severity"] == severity) and (not rule or f["rule"] == rule)
             and (not q or q.lower() in (f["batchId"] + f["ruleTitle"] + f["explanation"]).lower())]
    return {**r, "findings": items, "count": len(items), "asOf": s.as_of_date}


@router.get("/findings/{finding_id}")
def finding_detail(finding_id: str, client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    match = next((f for f in compute_findings(client, s.as_of_date)["findings"] if f["findingId"] == finding_id), None)
    if match is None:
        raise HTTPException(404, detail="Finding not found")
    g = graphs.trace_graph(client, match["batchId"], "both", False, s.max_graph_nodes)
    return {"finding": match, "graph": g, "highlight": match["evidenceNodeIds"]}
