# Online Deployment
> **Not deployed.** No hosting accounts were available; everything below is prepared configuration and manual steps. Do not describe the site as online until you have completed and verified these steps.
> A public Vercel site can **never** reach Neo4j Desktop on your laptop. Use a separate hosted Neo4j and backend; never expose your local database.

## 1. Hosted Neo4j (Aura)
1. Create a free/paid AuraDB instance at <https://neo4j.com/cloud/platform/aura-graph-database/>; save the generated password (shown once).
2. Connection URI looks like `neo4j+s://<id>.databases.neo4j.io` (TLS). Username is usually `neo4j`; database `neo4j`.
3. Load data from your machine (temporary local `.env` pointing to Aura; **do not commit**):
```powershell
$env:NEO4J_URI="neo4j+s://<id>.databases.neo4j.io"; $env:NEO4J_USER="neo4j"; $env:NEO4J_PASSWORD="<aura password>"
python database\setup_db.py all
```
(setup_db reads environment variables before `.env`.) Expected: `VALIDATION PASSED`.

## 2. Backend on Render
Blueprint: `render.yaml` (web service, `uvicorn`, health check `/api/health`). Set in the Render dashboard:
`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `CORS_ORIGINS=https://<your-vercel-app>.vercel.app`; keep `APP_ENV=production`, `ENABLE_WRITES=false`.
Free-tier services may sleep and respond slowly on first request.

## 3. Frontend on Vercel
Import the repo, set **Root Directory = `frontend`**, framework Vite, build `npm run build`, output `dist`. Environment variable: `VITE_API_URL=https://<render-service>.onrender.com`.
`frontend/vercel.json` rewrites all paths to `index.html`, so direct URLs and refresh on every route work. After deploying, add the Vercel URL to `CORS_ORIGINS` and redeploy the backend.

## 4. Verification checklist (do each, tick honestly)
- [ ] `https://<api>/api/health` → `database.connected: true`
- [ ] Frontend loads; header shows `NEO4J CONNECTED`
- [ ] Home graph shows seeded recall scenario; stats are non-zero
- [ ] Medicines list with images; search works
- [ ] `/traceability?batch=BATCH-VALID-001` returns data; refresh the page directly
- [ ] Risk shows 8 findings; Recall `RCL-001` shows 6 pharmacies / 24000 units
- [ ] `python tests/smoke_live.py https://<api>` passes (CRUD step skipped as writes are off)
- [ ] Browser dev tools: no credentials in network responses or bundle; no CORS errors
- [ ] `https://<api>/docs` returns 404 in production

Local and online configurations are separate (`.env` vs dashboard variables); the local setup keeps working independently.
