# Testing
Only results marked **Executed** were actually run (authoring sandbox: Python 3.12, Node 22, **no Neo4j server, no browser**).

## Executed
| Suite | Command | Result |
|---|---|---|
| Backend offline (dataset, catalogue, API contract) | `cd backend && python -m pytest -q` | **106 passed, 12 skipped** (skips = live-DB tests) |
| Frontend (jsdom, API mocked, Cytoscape mocked) | `cd frontend && npm test` | **28 passed** |
| Frontend production build | `cd frontend && npm run build` | **Succeeds** (tsc + vite); product SVGs emitted to `dist/products` |
| Clean-extract check | unzip → `npm ci` → tests → build; backend tests | Repeated on the delivered ZIP: passed |
| Contrast (WCAG) | computed for both themes | All text pairs ≥ 4.5:1 after fixes (light accent on card 6.60, coral 5.92; dark ≥ 4.98) |
| Visual check of product art | SVGs rasterised and viewed | Rendered correctly on the dark tile used in both themes |

### What the offline tests prove
* **Dataset** (10): deterministic; target counts; unique IDs; no dangling or duplicate relationships; valid dates/quantities; all 8 scenarios exist; a pure-Python reference of the 7 rules flags **exactly** the seeded batches; recall reaches 6 pharmacies / 24,000 units.
* **Catalogue** (75): 24 templates; declared params == used `$params`; defaults validate; write templates are `TEST-` + `isTestRecord` scoped; read templates contain no write clauses; injection-style params rejected.
* **API** (21, fake DB client): honest disconnected health; 503 envelope; id validation (400/422); unknown batch → 404; writes disabled by default; admin token; CRUD validation (quantity, dates, prefix); Lab allowlist; CORS restriction; docs hidden in production; no secret leakage.
* **Frontend** (28): nine routes by direct URL; nav links; theme default/toggle/persist/restore on every route; connected/disconnected/offline status; no fabricated stats when API is down; five product images map to bundled files (+fallback, alt text, detail view); assets exist; Command Center, Traceability (404 empty state, gaps, export), Risk (filters, disclaimer), Lab (writes blocked), Recall (affected vs unaffected, limitations), Insights render backend data.

## Defects found by testing and fixed
1. Dataset: duplicate `DISPENSED_AT` edges in a 2-pharmacy region (would break live count validation).
2. Dataset: recall scenario accidentally triggered `UNEXPECTED_ROUTE`.
3. Backend: DB outage hung requests ~30 s (driver retry) → capped at 3 s.
4. Frontend: Command Center crashed to blank when API down.
5. Frontend: light-theme accent/coral text and white-on-coral buttons failed AA.
6. Frontend: React key warning in `PropTable`.

## NOT executed (needs your machine) — please run and report
| What | How |
|---|---|
| Cypher syntax/semantics for every query, rules, routers | `python database\setup_db.py all`, then `python tests\smoke_live.py` |
| 12 live-DB pytest tests (rules == reference, CRUD round-trip, every read template, PROFILE plan) | `cd backend; $env:NEO4J_PASSWORD="…"; python -m pytest -q -m neo4j` |
| Browser behaviour: graph layout, tooltips, drag/zoom, theme restyle, both-theme visuals, responsiveness | Follow `DEMO_GUIDE.md` |
| Plan parsing against real EXPLAIN/PROFILE output | Lab → *PROFILE: downstream traversal* |
| Deployment | `DEPLOYMENT.md` checklist |
| Dependency audit | `pip-audit`, `npm audit` |

Every visible control is covered by a render/behaviour test only where listed above; controls that depend on Cytoscape canvas interaction (drag, wheel zoom, hover) are **unverified**.
