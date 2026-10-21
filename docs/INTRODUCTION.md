# Introduction and Problem Statement

## Problem
Medicines move through a chain of manufacturers, ingredient suppliers, distributors, warehouses and pharmacies. When a quality issue appears,
investigators must answer connected questions quickly: *which suppliers fed this batch, which shipments carried it, where did it end up, and what
records are missing?* Those are questions about **relationships**, and the answers are multi-hop paths.

## Solution in this project
PharmaTrace is a graph-first traceability and risk-intelligence website built on **Neo4j**. It stores the supply chain as a property graph and
exposes it through a FastAPI backend and a React interface built around interactive graph visualisation:

| Capability | Where |
|---|---|
| Upstream / downstream batch tracing, event history, exportable report | `/traceability` |
| Seven explainable risk rules with evidence graphs | `/risk-intelligence` |
| Recall impact by graph traversal, affected quantity, report | `/recall-analysis` |
| Product exploration with bundled illustrations and relationship graphs | `/medicines` |
| Free graph exploration, filters, expansion, shortest path | `/graph-explorer` |
| Allowlisted Cypher lab: CRUD, traversal, EXPLAIN/PROFILE, schema | `/database-lab` |
| Live counts, schema, degree, indexes, constraints, profiling | `/database-insights`, `/command-center` |

## Scope and honesty statements
* All organisations, medicines and pharmacies are **fictional**; all data is **synthetic and seeded** (`database/dataset.py`, seed 42).
* Seeded anomalies are **simulated test scenarios**. A rule finding is an indicator to investigate, never proof of fraud or misconduct.
* Product images are **illustrative** local SVGs, not packaging of real medicines.
* Real-world relevance (documented use of graph databases): Neo4j's own materials describe graph use in fraud detection, recommendation,
  knowledge graphs and supply-chain/network analysis. This project does **not** claim any specific organisation's pharmaceutical
  deployment. Teams citing adoption examples should take them from <https://neo4j.com/customers/> and cite the exact page.
* Pharmaceutical track-and-trace is regulated in many jurisdictions; this project is an academic demonstration, not a compliant system.

## Document map
`NEO4J_OVERVIEW` · `ARCHITECTURE` · `GRAPH_SCHEMA` · `DATA_DICTIONARY` · `CYPHER_QUERIES` · `GRAPH_ANALYTICS` · `INDEXING_AND_CONSTRAINTS` ·
`TRANSACTIONS_AND_CONCURRENCY` · `SECURITY` · `BACKUP_AND_RECOVERY` · `SCALABILITY` · `NEO4J_VS_MYSQL` · `PERFORMANCE` · `TESTING` ·
`RUBRIC_COMPLIANCE` · `LOCAL_SETUP` · `DEPLOYMENT` · `DEMO_GUIDE` · `FUTURE_SCOPE`.
