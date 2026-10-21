# Local Setup (Windows 10/11, Neo4j Desktop)

> Expected outputs below are derived from the code (counts come from the deterministic generator). They have **not** been captured from a live run
> in the authoring environment, so tick them off against your real output and note any difference.

Prerequisites: Windows 10/11, Python 3.11+ (`python --version`), Node.js 20+, Git optional.

## 1. Install and start Neo4j Desktop
1. Download Neo4j Desktop from <https://neo4j.com/download/> and install it (menu labels differ slightly between Desktop versions).
2. Create a **local** instance/DBMS: choose a name (e.g. `pharmatrace`), a **5.x** version, and set a password. Remember it.
3. Start the instance. Wait until it shows *Running*. Default Bolt URI: `bolt://localhost:7687`.

## 2. Configure credentials
```powershell
cd PharmaTrace
copy .env.example .env
notepad .env        # set NEO4J_PASSWORD to the password from step 1.2
```

## 3. Python environment
```powershell
python -m venv backend\.venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # only if activation is blocked
backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

## 4. Initialise schema, load data, validate
```powershell
python database\setup_db.py all
```
Expected:
```
Schema OK: 17 statements applied (constraints + indexes).
Load OK: {"medicines": 8, "organizations": 25, "locations": 12, "pharmacies": 14, "batches": 40, "shipments": 133, "recalls": 2, "events": 251} relationships: 1394
Label                expected    actual
...                  (every row ends with OK)
Scenario batches present: 10 / 10 missing: []
VALIDATION PASSED
```
Steps can be run separately: `schema`, `load`, `validate`. `reset --confirm` wipes the database (local use only). The load is idempotent (`MERGE`).

## 5. Run the backend
```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
Check: <http://localhost:8000/api/health> → `{"status":"ok","database":{"connected":true,"nodes":485}}` and interactive API docs at <http://localhost:8000/docs> (disabled when `APP_ENV=production`).

## 6. Run the tests
```powershell
cd backend
python -m pytest -q                      # offline tests; live-DB tests are skipped if NEO4J_PASSWORD is unset
$env:NEO4J_PASSWORD="<your password>"; python -m pytest -q -m neo4j   # live tests (use a test DB; creates/deletes TEST-* only)
```
Authoring-environment result (offline): **106 passed, 12 skipped** (the 12 are the live-DB tests).

## 6b. Run the frontend
```powershell
cd frontend
copy .env.example .env        # VITE_API_URL=http://localhost:8000
npm install
npm run dev                   # open http://localhost:5173
npm test                      # 28 jsdom tests (no backend needed)
npm run build                 # production build -> frontend/dist
```
Expected: header shows `NEO4J CONNECTED · 485 NODES` once Neo4j and the API are running; `API OFFLINE` / `NEO4J DISCONNECTED` otherwise.
The Home graph is the seeded recall scenario `BATCH-RECALL-001`. All nine pages are implemented. Run `python tests\smoke_live.py` (backend + Neo4j running) for an automatic end-to-end check of the seeded results.

## 7. Manual smoke checks (API)
```powershell
curl http://localhost:8000/api/overview
curl http://localhost:8000/api/traceability/BATCH-VALID-001
curl http://localhost:8000/api/risk/findings
curl http://localhost:8000/api/recall/RCL-001/impact
curl -X POST http://localhost:8000/api/lab/run -H "Content-Type: application/json" -d "{\"queryId\":\"match_batch\"}"
```
Expected highlights: 7 distinct rule types, 8 findings (BATCH-DUP-001 and -002, UNVER-001, UNEXP-001, EXPIRED-001, QTY-001, and INCOMPLETE-001 twice: MISSING_EVENT + INCOMPLETE_PATH);
RCL-001 impact: 2 batches, 6 pharmacies, 24000 units delivered.

You can also paste any query from `docs/CYPHER_QUERIES.md` into **Neo4j Browser** (replace `$params` with literals or use `:param`).

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| `Cannot connect to Neo4j ... Connection refused` | Instance not started, or wrong port. Start it in Neo4j Desktop; confirm `NEO4J_URI`. |
| `AuthError` / "rejected the configured credentials" | Wrong `NEO4J_PASSWORD` in `.env`. |
| `Unable to retrieve routing information` | Use `bolt://` (not `neo4j://`) for a single local instance. |
| `NEO4J_PASSWORD is not set` | `.env` missing or not in the repo root. |
| `ModuleNotFoundError` | Venv not activated or `pip install -r backend\requirements.txt` not run. |
| `Address already in use` (port 8000) | `python -m uvicorn app.main:app --port 8010` and update the frontend API URL later. |
| Browser CORS error | Add the frontend origin to `CORS_ORIGINS` and restart the backend. |
| Empty graph / counts 0 | Run `python database\setup_db.py all`. Check `validate`. |
| Cypher/constraint error during schema | Neo4j 4.x is unsupported (uses 5.x syntax); create a 5.x instance. |
| `/api/crud` returns 403 | Set `ENABLE_WRITES=true` in `.env` and restart. |
| Activation script blocked in PowerShell | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. |
