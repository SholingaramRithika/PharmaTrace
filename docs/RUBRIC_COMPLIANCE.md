# Rubric Compliance (website scope)
Source: "Instructions for Case Study & PPT Presentation on Databases" (provided PDF; authoritative). Marks as written: **A Conceptual Understanding 2 · B Critical Analysis 1 · C Applications & Relevance 1 · D Hands-on Demonstration 5 · E Presentation & Communication 1 = 10**.
Per instruction, **no presentation (PPT) deliverable is included**; items that exist only for the presentation are marked *Out of scope*. "Verified" means executed here; "Pending" means implemented but needs your live run (see `TESTING.md`).

## A. Conceptual Understanding (2) — Introduction, Database Type & Model, Architecture & Design, Core Features
| PDF requirement | Website / implementation | Document | Test | Status |
|---|---|---|---|---|
| Brief description; history/ownership; relevance | Home "Why Neo4j" | `INTRODUCTION`, `NEO4J_OVERVIEW` | – | Done (dates intentionally hedged; verify) |
| Category and data model; suitability | Insights schema graph; Graph Explorer | `NEO4J_OVERVIEW`, `GRAPH_SCHEMA`, `DATA_DICTIONARY` | dataset tests | Done |
| System architecture | Whole app | `ARCHITECTURE` | – | Done |
| Storage management | – (conceptual) | `NEO4J_OVERVIEW` | – | Done (conceptual) |
| Indexing mechanisms | Lab index inspect; Insights | `INDEXING_AND_CONSTRAINTS` | catalogue tests; integration (pending) | Done / live Pending |
| Query processing & optimisation | Lab EXPLAIN/PROFILE; Insights PROFILE | `PERFORMANCE`, `CYPHER_QUERIES` | integration `test_profile_returns_plan` (pending) | Done / live Pending |
| Transactions & concurrency (ACID) | Managed read/write transactions; CRUD | `TRANSACTIONS_AND_CONCURRENCY` | CRUD tests | Done (concurrency not tested) |
| Scalability & replication | – | `SCALABILITY` | – | Done (conceptual) |
| Query language (Cypher) | Database Lab | `CYPHER_QUERIES` (24) | catalogue tests (75) | Done |
| Security (auth, authz, encryption) | Allowlists, write guard, CORS, token | `SECURITY` | API security tests | Done (limits documented) |
| Backup & recovery | `setup_db.py reset/all` | `BACKUP_AND_RECOVERY` | – | Done (commands not executed) |
| Data integrity constraints | 8 unique constraints, validation | `INDEXING_AND_CONSTRAINTS` | dataset + CRUD tests | Done / constraint live Pending |
| Procedures/triggers/advanced | Not used (GDS not claimed) | `GRAPH_ANALYTICS`, `FUTURE_SCOPE` | – | Stated as not implemented |
| Integration with tools | FastAPI, Python driver, React, Cytoscape | `ARCHITECTURE` | – | Done |

## B. Critical Analysis (1) — Strengths & Limitations, Performance, Future Trends
| Requirement | Where | Status |
|---|---|---|
| Advantages, limitations, comparison with similar DBs | `NEO4J_VS_MYSQL`, `NEO4J_OVERVIEW` (weak fits), `FUTURE_SCOPE` | Done (comparison conceptual; no benchmark) |
| Performance considerations / benchmarks | `PERFORMANCE`; Lab and Insights measure live | Methodology done; **no benchmark results exist** |
| Future trends / roadmap (latest versions, upcoming features) | `FUTURE_SCOPE` (project extensions only) | Partial: product-roadmap claims deliberately not made without current sources |

## C. Applications & Relevance (1) — Use cases, real-world adoption, case-study examples
| Requirement | Where | Status |
|---|---|---|
| Domains/use cases | `INTRODUCTION`, `NEO4J_OVERVIEW`; the app itself is a pharma-traceability case study | Done |
| Real-world adoption / example organisations / success story | Not asserted | **Gap by design:** add verified, cited examples from <https://neo4j.com/customers/>; none were fabricated |

## D. Hands-on Demonstration (5) — Installation/setup, schema design, queries (CRUD, joins, indexing…)
| Requirement | Website / implementation | Document | Test | Status |
|---|---|---|---|---|
| Installation / setup | Scripts `setup_db.py`, `.env.example` | `LOCAL_SETUP`, `DEPLOYMENT` | – | Documented; live run Pending |
| Schema design | `schema.cypher`, graph model, Insights schema graph | `GRAPH_SCHEMA`, `DATA_DICTIONARY` | dataset tests | Done |
| CRUD | Lab write templates; `/api/crud`; TEST-* guard | `CYPHER_QUERIES` | API tests (offline) ; integration + smoke (Pending) | Offline Verified / live Pending |
| "Joins" (relationship traversal) | Traceability, Recall, Lab traversal/shortest path | `GRAPH_ANALYTICS`, `NEO4J_VS_MYSQL` | integration (Pending) | Live Pending |
| Indexing | Constraints/indexes + EXPLAIN/PROFILE | `INDEXING_AND_CONSTRAINTS` | integration (Pending) | Live Pending |
| Mini project | The PharmaTrace website | all | 106 + 28 tests | Done (live Pending) |
| Dataset & scenarios | 8 seeded scenarios, deterministic | `dataset_validation_report` | `test_dataset.py` | **Verified (offline)** |

## E. Presentation & Communication (1) — Slide quality, clarity, teamwork, references, conclusion
Slides, speaker notes and Q&A are **Out of scope** by instruction. Website-relevant parts: clear UI/documentation, references in `NEO4J_OVERVIEW`, conclusions in `FUTURE_SCOPE`. Teamwork is not assessable from code.

## The 11 required presentation components (for later reuse)
1 Introduction → `INTRODUCTION/NEO4J_OVERVIEW` · 2 Type & Model → `GRAPH_SCHEMA` · 3 Architecture → `ARCHITECTURE`+indexing/transactions/scalability docs · 4 Core Features → `CYPHER_QUERIES`, `SECURITY`, `BACKUP_AND_RECOVERY` · 5 Strengths & Limitations → `NEO4J_VS_MYSQL` · 6 Use Cases → `INTRODUCTION` (adoption examples to be added) · 7 Hands-on → `/database-lab` + `DEMO_GUIDE` · 8 Performance → `PERFORMANCE` · 9 Future → `FUTURE_SCOPE` · 10 Conclusion → write with your findings · 11 References → `NEO4J_OVERVIEW`.
