
from __future__ import annotations

from typing import Annotated, Literal
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import Settings, get_settings
from ..db import Neo4jClient, merge_graphs
from ..deps import get_client

router = APIRouter(prefix="/api/medicines", tags=["medicines"])

LIST_Q = """MATCH (m:Medicine)
OPTIONAL MATCH (m)-[:HAS_BATCH]->(b:Batch)
WHERE coalesce(b.isTestRecord, false) = false
OPTIONAL MATCH (o:Organization)-[:MANUFACTURES]->(b)
OPTIONAL MATCH (b)-[:AFFECTED_BY]->(r:Recall)
WITH m, collect(DISTINCT b) AS bs,
     collect(DISTINCT o.name) AS mfrs,
     collect(DISTINCT r.status) AS recalls
RETURN m, size(bs) AS batchCount,
       [x IN bs | x.status] AS statuses,
       size([x IN bs WHERE x.expiryDate < date($asOf)]) AS expired,
       size([x IN bs WHERE x.expiryDate >= date($asOf)
             AND x.expiryDate < date($asOf) + duration('P6M')]) AS expiringSoon,
       mfrs, recalls"""


@router.get("")
def list_medicines(
    q: Annotated[str | None, Query(max_length=60)] = None,
    category: str | None = None,
    manufacturer: str | None = None,
    batchStatus: str | None = None,
    expiry: Literal["expired", "expiring", "ok"] | None = None,
    recall: Literal["active", "none"] | None = None,
    sort: Literal["name", "code", "category", "batches"] = "name",
    client: Neo4jClient = Depends(get_client),
    s: Settings = Depends(get_settings),
):
    items = []

    for r in client.rows(LIST_Q, asOf=s.as_of_date):
        m = r["m"]["properties"]

        medicine_name = m.get("name") or "Unknown Medicine"
        drug_code = m.get("drugCode") or ""
        medicine_category = m.get("category") or "Other"
        statuses = [status for status in r["statuses"] if status]

        items.append({
            "medicineId": m.get("medicineId", ""),
            "name": medicine_name,
            "drugCode": drug_code,
            "category": medicine_category,
            "form": m.get("form") or "Tablet",
            "manufacturers": r["mfrs"],
            "batchCount": r["batchCount"],
            "batchStatus": dict(Counter(statuses)),
            "expiredBatches": r["expired"],
            "expiringSoonBatches": r["expiringSoon"],
            "expiryStatus": (
                "expired" if r["expired"]
                else "expiring" if r["expiringSoon"]
                else "ok"
            ),
            "recallStatus": (
                "active" if "Active" in r["recalls"] else "none"
            ),
        })

    ql = (q or "").lower()

    items = [
        item for item in items
        if (
            not ql
            or ql in item["name"].lower()
            or ql in item["drugCode"].lower()
        )
        and (not category or item["category"] == category)
        and (not manufacturer or manufacturer in item["manufacturers"])
        and (
            not batchStatus
            or batchStatus in item["batchStatus"]
        )
        and (not expiry or item["expiryStatus"] == expiry)
        and (not recall or item["recallStatus"] == recall)
    ]

    if sort == "batches":
        items.sort(key=lambda item: -item["batchCount"])
    elif sort == "code":
        items.sort(key=lambda item: item["drugCode"].lower())
    elif sort == "category":
        items.sort(key=lambda item: item["category"].lower())
    else:
        items.sort(key=lambda item: item["name"].lower())

    return {
        "medicines": items,
        "count": len(items),
        "note": (
            "Medicine names and product illustrations are fictional "
            "and illustrative only."
        ),
    }


@router.get("/{medicine_id}/graph")
def medicine_graph(
    medicine_id: str,
    client: Neo4jClient = Depends(get_client),
    s: Settings = Depends(get_settings),
):
    if not client.rows(
        "MATCH (m:Medicine {medicineId: $id}) RETURN 1 AS x",
        id=medicine_id,
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Medicine {medicine_id} not found",
        )

    parts = [
        client.graph(q, id=medicine_id)
        for q in [
            """
            MATCH p = (m:Medicine {medicineId: $id})-[:HAS_BATCH]->(b:Batch)
            WHERE coalesce(b.isTestRecord, false) = false
            RETURN p
            """,
            """
            MATCH p = (:Medicine {medicineId: $id})-[:HAS_BATCH]->(b:Batch)
            <-[:MANUFACTURES|SUPPLIES_TO]-(o)
            RETURN p LIMIT 150
            """,
            """
            MATCH p = (:Medicine {medicineId: $id})-[:HAS_BATCH]->(b:Batch)
            -[:AFFECTED_BY]->(r:Recall)
            RETURN p
            """,
            """
            MATCH p = (:Medicine {medicineId: $id})-[:HAS_BATCH]->(b:Batch)
            -[:STORED_AT]->(l:Location)
            RETURN p LIMIT 100
            """,
        ]
    ]

    return {
        "medicineId": medicine_id,
        **merge_graphs(*parts, limit=s.max_graph_nodes),
    }
