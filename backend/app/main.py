from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j.exceptions import AuthError, ConstraintError, ServiceUnavailable, SessionExpired, ClientError

from .config import get_settings
from .db import Neo4jClient
from .routers import crud, graph, insights, lab, medicines, recall, risk, system, traceability

log = logging.getLogger("pharmatrace")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    if not hasattr(app.state, "client"):
        app.state.client = Neo4jClient(s)
        # Log host only; never log credentials.
        log.info("Neo4j target: %s (db=%s)", s.neo4j_uri, s.neo4j_database)
    yield
    app.state.client.close()


def err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="PharmaTrace API", version="1.0.0", lifespan=lifespan,
                  description="Graph-first pharmaceutical traceability API over Neo4j (synthetic data).",
                  docs_url="/docs" if s.app_env != "production" else None,
                  redoc_url=None, openapi_url="/openapi.json" if s.app_env != "production" else None)
    app.add_middleware(CORSMiddleware, allow_origins=s.cors_list, allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Content-Type", "X-Admin-Token"], allow_credentials=False)
    for r in (system, graph, medicines, traceability, risk, recall, crud, lab, insights):
        app.include_router(r.router)

    @app.exception_handler(HTTPException)
    async def http_exc(_: Request, e: HTTPException):
        code = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 409: "CONFLICT", 422: "INVALID_INPUT"}.get(e.status_code, "ERROR")
        return err(e.status_code, code, str(e.detail))

    @app.exception_handler(RequestValidationError)
    async def validation(_: Request, e: RequestValidationError):
        first = e.errors()[0]
        loc = ".".join(str(x) for x in first["loc"] if x not in ("body", "query", "path"))
        return err(422, "INVALID_INPUT", f"{loc}: {first['msg']}")

    @app.exception_handler(ServiceUnavailable)
    @app.exception_handler(SessionExpired)
    async def unavailable(_: Request, e: Exception):
        return err(503, "DATABASE_UNAVAILABLE", "Cannot reach Neo4j. Is the database started and the URI correct?")

    @app.exception_handler(AuthError)
    async def auth(_: Request, e: AuthError):
        return err(503, "DATABASE_AUTH_FAILED", "Neo4j rejected the configured credentials.")

    @app.exception_handler(ConstraintError)
    async def constraint(_: Request, e: ConstraintError):
        return err(409, "CONSTRAINT_VIOLATION", "A database constraint was violated.")

    @app.exception_handler(ClientError)
    async def client_err(_: Request, e: ClientError):
        log.warning("Cypher client error: %s", e.code)
        return err(400, "QUERY_ERROR", "The database rejected the query.")

    @app.exception_handler(Exception)
    async def unhandled(_: Request, e: Exception):
        log.exception("Unhandled error")
        return err(500, "INTERNAL_ERROR", "Unexpected server error.")

    return app


app = create_app()
