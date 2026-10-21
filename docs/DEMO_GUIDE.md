# Faculty Website Demonstration Guide
Expected values are derived from the seeded dataset (`database/dataset.py`) and asserted by offline tests; they have **not yet been observed on a live run**. Run `python tests\smoke_live.py` first; it checks most of them automatically.

**Prep:** Neo4j Desktop running → `python database\setup_db.py all` → backend `uvicorn` (with `ENABLE_WRITES=true`) → `npm run dev` → open <http://localhost:5173>. Header must say `NEO4J CONNECTED · 485 NODES`.

| # | Step | Do | Expected |
|---|---|---|---|
| 1 | Command Center | Open `/command-center` | 8 medicines · 40 batches · 25 orgs · 133 shipments · 14 pharmacies · 251 events · 1394 relationships · 2 recalls (+ `nodes 485` in header). Status chart: Released 37, Recalled 2, Expired 1. Risk summary: 8 findings (High 4, Medium 4) |
| 2 | Explain the model | Point at the recall graph; open Insights later for the schema | Medicine→Batch→Shipment→Pharmacy etc.; colours/shapes per label |
| 3 | Select a manufacturer | Graph Explorer → search `Aurelia` → click result → select node | Organization, role Manufacturer, Verified; connections include `MANUFACTURES` ×N, `OPERATED_BY` |
| 4 | Medicine Explorer | `/medicines`; filter Recall = Active | Cardiolix 50mg only (6 batches, recall: active), blister-pack image |
| 5 | Medicine graph | Click VIEW GRAPH on Cardiolix | Image beside properties; graph with 6 batches, manufacturer Aurelia Pharma Labs, suppliers, RCL-001 (its two batches); double-click a batch to expand |
| 6 | Search batch | `/traceability` → `BATCH-VALID-001` | Cardiolix 50mg by Aurelia Pharma Labs; supplier Evergreen Reagents (Verified); 10000 units; 4 shipments (10000, 3334, 3333, 3333); 7 events; no gaps/findings |
| 7 | Upstream / downstream | Toggle `upstream`, `downstream`; select PH-03 node → PATH FROM BATCH | Upstream: medicine, manufacturer, supplier, plant. Downstream: shipments, LOC-W01 warehouse, PH-01..03. Path highlighted in coral |
| 8 | Show Cypher | `/database-lab` → *Downstream destinations (variable-length path)* with `BATCH-VALID-001` → Run → Graph tab | Same destinations; query text visible; timing chips |
| 9 | Seeded anomaly | `/risk-intelligence` → select *Unverified supplier* (`BATCH-UNVER-001`) | Supplier Ionia Trading Co (Unverified) supplied "Excipient"; evidence nodes highlighted |
| 10 | Explain evidence | Read evidence panel, recommended action, scoring formula | Score 3 → band elevated; synthetic-data disclaimer shown |
| 11 | Recall | `/recall-analysis` → RCL-001 | 2 batches (RECALL-001/002), 24000 units made and delivered, 6 pharmacies (PH-04..06, PH-12..14) at 4000 each, 2 warehouses (LOC-W03, LOC-W08), 2 distributors (Keystone, Lumen); 8 unaffected pharmacies; only the generic note that units delivered ≠ units sold (no open-leg warning) |
| 12 | Affected destinations | Show tables and highlighted graph; Export report | `.md` downloads |
| 13 | Compare with incomplete batch | `/traceability?batch=BATCH-INCOMPLETE-001` | Gaps: Missing event RECEIVED; shipment without destination; nothing invented |
| 14 | Lab query | *Batches per medicine (aggregation)* → Run | 8 rows; Cardiolix 6 batches |
| 15 | Safe CRUD | Lab: *CREATE a test batch* (`TEST-DEMO-1`) → run; run again | 1st: `nodes_created 1`, `relationships_created 1`; 2nd: constraint-violation error |
| 16 | Verify change | Run *SET* (status Released), then *Look up a batch* with `TEST-DEMO-1`; finally *Safe DELETE* | Status updated; lookup shows it; delete returns `deleted TEST-DEMO-1` (`nodes_deleted 1`) |
| 17 | Indexes & constraints | Lab *Inspect constraints/indexes*; `/database-insights` | 8 constraints, 17 indexes listed (9 secondary + 8 constraint-backed; confirm the live list) ; PROFILE cards with db hits |
| 18 | Query plans | Lab *EXPLAIN: batch lookup* and *PROFILE* | Plan tree with operators; expect a unique-index seek for the lookup (confirm) |
| 19 | MySQL comparison | Open `docs/NEO4J_VS_MYSQL.md` | Conceptual comparison, equivalent SQL; state that no benchmark was run |
| 20 | Theme | Toggle Light/Dark on each page; refresh | Whole UI incl. graph, charts, product cards switches and persists |

Note on step 17: the exact index count is `8 constraint-backed + 9 secondary = 17`; the live `SHOW INDEXES` may also list system lookup indexes. Report what you see.
Clean-up: delete any remaining `TEST-*` batches with the Lab delete template or `python database\setup_db.py reset --confirm` then `all`.
