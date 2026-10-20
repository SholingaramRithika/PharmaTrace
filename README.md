# PharmaTrace — Pharmaceutical Supply Chain Traceability & Risk Intelligence (Neo4j)

University DBMS case study. Graph-first traceability, risk and recall analysis on **Neo4j**, with a FastAPI backend.
All data is **synthetic**; all organizations and medicines are fictional; seeded anomalies are simulated test scenarios.

## Status (honest)
Website project only: no presentation files are included.
| Area | State |
|---|---|
| Neo4j schema, deterministic dataset (485 nodes / 1,394 relationships, 8 seeded scenarios), 24 Cypher templates | Done. Offline-verified; **Cypher not yet run on a live Neo4j** |
| FastAPI backend (25 endpoints) | Done. 106 offline tests pass (12 live-DB tests skipped) |
| React frontend, all 9 routes, dark/light theme, Cytoscape graphs, bundled product illustrations | Done. 28 jsdom tests + production build pass. **Not yet seen in a real browser** |
| Docs (20 documents incl. rubric mapping, demo guide, deployment) | Done; see `docs/` |
| Online deployment | Config prepared (`render.yaml`, `vercel.json`); **not deployed** |
Run `python tests/smoke_live.py` after setup to verify the live parts, then see `docs/TESTING.md`.

## Quick start (Windows, Neo4j Desktop) — full details in `docs/LOCAL_SETUP.md`
```powershell
copy .env.example .env                 # set NEO4J_PASSWORD
python -m venv backend\.venv ; backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python database\setup_db.py all        # schema + data + validation
cd backend ; python -m uvicorn app.main:app --reload --port 8000
# new terminal (frontend):
cd frontend
copy .env.example .env
npm install
npm run dev                            # http://localhost:5173

# tests
cd backend ; python -m pytest -q       # backend
cd frontend ; npm test                 # frontend
```

## Layout
```
database/   schema.cypher · dataset.py (seeded generator) · setup_db.py (schema|load|validate|reset)
            queries/catalogue.json (Lab templates) · validation/ (reference rules, report generator)
backend/    app/ (config, db, routers/, services/) · tests/ · requirements.txt
frontend/   src/ (App, Layout, theme, api, components, pages/) · public/products/*.svg (bundled illustrations) · vercel.json
docs/       20 documents: INTRODUCTION … FUTURE_SCOPE (start with LOCAL_SETUP, DEMO_GUIDE, RUBRIC_COMPLIANCE)
tests/      smoke_live.py (live end-to-end check) · README.md
render.yaml Render blueprint for the API (frontend/vercel.json for Vercel)
```

## Security notes
No credentials in code; `.env` is git-ignored. Cypher is parameterized; labels/relationship types come from allowlists.
The Database Lab runs only allowlisted templates; writes are limited to `TEST-*` batches flagged `isTestRecord`, are off unless `ENABLE_WRITES=true`,
and can require `X-Admin-Token`. CORS is restricted to `CORS_ORIGINS`; `/docs` is disabled when `APP_ENV=production`.
A public deployment needs a separate hosted Neo4j (e.g. Aura) and backend; never expose the laptop's Neo4j Desktop.

## Visual design layer
The animated navy/cyan background (particle network, molecule/DNA motifs, glass panels) is purely visual. See `docs/BACKGROUND.md`.
