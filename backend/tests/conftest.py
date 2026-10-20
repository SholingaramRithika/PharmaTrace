import os
import pytest
from fastapi.testclient import TestClient
from app.config import get_settings
from app.main import create_app


class FakeClient:
    """Stands in for Neo4jClient so API contract/validation logic is testable offline."""
    def __init__(self, up=True, rows=None):
        self.up, self._rows, self.calls = up, rows or [], []
    def verify(self):
        if not self.up:
            from neo4j.exceptions import ServiceUnavailable
            raise ServiceUnavailable("down")
    def rows(self, q, **p):
        self.calls.append((q, p)); self.verify(); return self._rows
    def graph(self, q, **p):
        self.calls.append((q, p)); self.verify(); return {"nodes": [], "edges": []}
    def read_raw(self, q, **p): return []
    def write(self, q, **p):
        self.calls.append((q, p)); return [], {}
    def run_lab(self, q, p, write):
        self.calls.append((q, p, write)); return {"columns": [], "rows": [], "graph": {"nodes": [], "edges": []},
                                                   "timing": {}, "counters": {}, "plan": None, "profiled": False}
    def close(self): pass


@pytest.fixture
def make_client(monkeypatch):
    def _make(fake=None, **env):
        for k, v in env.items():
            monkeypatch.setenv(k, str(v))
        get_settings.cache_clear()
        app = create_app()
        app.state.client = fake or FakeClient()
        return TestClient(app, raise_server_exceptions=False), app.state.client
    yield _make
    get_settings.cache_clear()


def neo4j_available():
    if not os.environ.get("NEO4J_PASSWORD"):
        return False
    try:
        from neo4j import GraphDatabase
        d = GraphDatabase.driver(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                                 auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]))
        d.verify_connectivity(); d.close(); return True
    except Exception:
        return False
