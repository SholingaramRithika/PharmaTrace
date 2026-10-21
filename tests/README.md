# Tests overview
| Where | Command | Needs Neo4j | Executed in authoring sandbox |
|---|---|---|---|
| `backend/tests/` | `cd backend && python -m pytest -q` | No (12 live tests auto-skip) | Yes: 106 passed, 12 skipped |
| `backend/tests/test_integration.py` | `cd backend && python -m pytest -q -m neo4j` (set `NEO4J_PASSWORD`) | **Yes** | **No** |
| `frontend/src/app.test.tsx` | `cd frontend && npm test` | No (API mocked) | Yes: 28 passed |
| `tests/smoke_live.py` | `python tests/smoke_live.py` (backend + Neo4j running, data loaded) | **Yes** | **No** (verified only that it fails gracefully with no server) |
