from __future__ import annotations
from fastapi import Depends, Header, HTTPException, Request
from .config import Settings, get_settings
from .db import Neo4jClient, parse_node_id


def get_client(request: Request) -> Neo4jClient:
    return request.app.state.client


def require_writes(settings: Settings = Depends(get_settings),
                   x_admin_token: str | None = Header(default=None)) -> None:
    if not settings.enable_writes:
        raise HTTPException(403, detail="Writes are disabled on this deployment (ENABLE_WRITES=false).")
    if settings.admin_token and x_admin_token != settings.admin_token.get_secret_value():
        raise HTTPException(401, detail="Missing or invalid X-Admin-Token.")


def node_id_or_400(node_id: str) -> tuple[str, str]:
    try:
        return parse_node_id(node_id)
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from None
