from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from neo4j.exceptions import ClientError, ConstraintError
from ..config import Settings, get_settings
from ..db import Neo4jClient
from ..deps import get_client
from ..services import lab

router = APIRouter(prefix="/api/lab", tags=["database-lab"])


class RunRequest(BaseModel):
    queryId: str = Field(pattern=r"^[a-z0-9_]{3,60}$")
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("/queries")
def queries(s: Settings = Depends(get_settings)):
    return {"queries": lab.public_catalogue(), "writesEnabled": s.enable_writes,
            "note": "Only these allowlisted, parameterized templates can run. Write templates touch TEST-* records only."}


@router.post("/run")
def run(body: RunRequest, client: Neo4jClient = Depends(get_client), s: Settings = Depends(get_settings)):
    try:
        return lab.run_template(client, body.queryId, body.params, s.enable_writes)
    except KeyError:
        raise HTTPException(404, detail=f"Unknown query template '{body.queryId}'") from None
    except lab.ParamError as e:
        raise HTTPException(422, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(403, detail=str(e)) from None
    except ConstraintError as e:
        raise HTTPException(409, detail=f"Constraint violation: {e.message}") from None
    except ClientError as e:
        raise HTTPException(400, detail=f"Cypher error: {e.message}") from None
