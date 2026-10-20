"""Safe CRUD: only TEST-* batches flagged isTestRecord may be created, changed or deleted."""
from __future__ import annotations
from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field, model_validator
from neo4j.exceptions import ConstraintError
from ..db import Neo4jClient
from ..deps import get_client, require_writes

router = APIRouter(prefix="/api/crud", tags=["crud"], dependencies=[Depends(require_writes)])
TestId = Path(pattern=r"^TEST-[A-Z0-9\-]{3,30}$")
Status = Literal["Quarantined", "Released", "Recalled", "Expired"]


class BatchCreate(BaseModel):
    batchId: str = Field(pattern=r"^TEST-[A-Z0-9\-]{3,30}$")
    medicineId: str = Field(pattern=r"^MED-[0-9]{3}$")
    quantity: int = Field(gt=0, le=1_000_000)
    manufacturingDate: date
    expiryDate: date
    status: Status = "Quarantined"

    @model_validator(mode="after")
    def dates_ok(self):
        if self.expiryDate <= self.manufacturingDate:
            raise ValueError("expiryDate must be after manufacturingDate")
        return self


class BatchUpdate(BaseModel):
    status: Status | None = None
    quantity: int | None = Field(default=None, gt=0, le=1_000_000)

    @model_validator(mode="after")
    def nonempty(self):
        if self.status is None and self.quantity is None:
            raise ValueError("Provide status and/or quantity")
        return self


class LinkSupplier(BaseModel):
    organizationId: str = Field(pattern=r"^ORG-[A-Z][0-9]{2}$")
    material: str = Field(default="Demo material", pattern=r"^[A-Za-z0-9 \-]{1,40}$")


@router.post("/batches", status_code=201)
def create_batch(body: BatchCreate, client: Neo4jClient = Depends(get_client)):
    try:
        rows, c = client.write("""MATCH (m:Medicine {medicineId: $medicineId})
            CREATE (m)-[:HAS_BATCH]->(b:Batch {batchId: $batchId, lotNumber: 'LOT-TEST', manufacturingDate: date($mfg),
                expiryDate: date($exp), quantity: $quantity, status: $status, isTestRecord: true})
            RETURN b""", batchId=body.batchId, medicineId=body.medicineId, quantity=body.quantity,
                               mfg=body.manufacturingDate.isoformat(), exp=body.expiryDate.isoformat(), status=body.status)
    except ConstraintError:
        raise HTTPException(409, detail=f"Batch {body.batchId} already exists (unique constraint).") from None
    if not rows:
        raise HTTPException(404, detail=f"Medicine {body.medicineId} not found; nothing created.")
    return {"created": rows[0]["b"], "counters": c}


@router.get("/batches/{batch_id}")
def read_batch(batch_id: str = TestId, client: Neo4jClient = Depends(get_client)):
    rows = client.rows("MATCH (b:Batch {batchId: $id}) WHERE b.isTestRecord = true RETURN b", id=batch_id)
    if not rows:
        raise HTTPException(404, detail="Test batch not found")
    return {"batch": rows[0]["b"]}


@router.patch("/batches/{batch_id}")
def update_batch(body: BatchUpdate, batch_id: str = TestId, client: Neo4jClient = Depends(get_client)):
    rows, c = client.write("""MATCH (b:Batch {batchId: $id}) WHERE b.isTestRecord = true
        SET b.status = coalesce($status, b.status), b.quantity = coalesce($quantity, b.quantity) RETURN b""",
                           id=batch_id, status=body.status, quantity=body.quantity)
    if not rows:
        raise HTTPException(404, detail="Test batch not found (only TEST-* records can be modified).")
    return {"updated": rows[0]["b"], "counters": c}


@router.post("/batches/{batch_id}/suppliers", status_code=201)
def link_supplier(body: LinkSupplier, batch_id: str = TestId, client: Neo4jClient = Depends(get_client)):
    rows, c = client.write("""MATCH (b:Batch {batchId: $id}) WHERE b.isTestRecord = true
        MATCH (o:Organization {organizationId: $org})
        MERGE (o)-[r:SUPPLIES_TO {material: $material}]->(b) RETURN o.name AS supplier""",
                           id=batch_id, org=body.organizationId, material=body.material)
    if not rows:
        raise HTTPException(404, detail="Test batch or organization not found.")
    return {"linked": rows[0]["supplier"], "counters": c}


@router.delete("/batches/{batch_id}")
def delete_batch(batch_id: str = TestId, client: Neo4jClient = Depends(get_client)):
    rows, c = client.write("""MATCH (b:Batch {batchId: $id}) WHERE b.isTestRecord = true
        WITH b, b.batchId AS id DETACH DELETE b RETURN id""", id=batch_id)
    if not rows:
        raise HTTPException(404, detail="Test batch not found (only TEST-* records can be deleted).")
    return {"deleted": rows[0]["id"], "counters": c}
