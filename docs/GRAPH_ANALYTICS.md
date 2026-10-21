# Graph Analytics

Twelve operations are implemented as Cypher (no Graph Data Science plugin is used or required). "Graph-native" = relies on traversal/path
semantics of the graph engine; "Rule-based" = property/pattern checks wrapped in application logic.

| # | Operation | Type | Where | Purpose |
|---|---|---|---|---|
| 1 | Variable-length traversal | Graph-native | Lab `downstream_varlen` | Follow 0..3 `FOLLOWED_BY` hops to final destinations |
| 2 | Upstream reachability | Graph-native | `/api/traceability/{id}?direction=upstream`, Lab `upstream_suppliers` | Medicine, manufacturer, suppliers behind a batch |
| 3 | Downstream reachability | Graph-native | `/api/traceability/{id}?direction=downstream` | Shipments, warehouses, pharmacies reached |
| 4 | Shortest path | Graph-native | `/api/graph/path`, Lab `shortest_path` | Shortest connection between two entities (≤10 hops) |
| 5 | Recall propagation | Graph-native | `/api/recall/{id}/impact`, Lab `recall_propagation` | Recall → batches → shipments → pharmacies, with units |
| 6 | Unexpected-relationship detection | Rule-based on pattern | Risk `UNVERIFIED_SUPPLIER`, `UNEXPECTED_ROUTE` | Relationships that violate expectations |
| 7 | Duplicate/conflict detection | Rule-based | Risk `DUPLICATE_LOT` | Same lot on different batches |
| 8 | High-connectivity analysis | Graph-native (degree) | Lab `high_degree`, `/api/insights` | Most-connected entities |
| 9 | Bottleneck identification | Graph-native aggregation | Lab `warehouse_bottlenecks` | Warehouses concentrating batches |
| 10 | Missing-link / orphan detection | Pattern predicate | Risk `INCOMPLETE_PATH`, `MISSING_EVENT`, Lab `orphan_check` | Shipments without destination; absent lifecycle events |
| 11 | Expiry analysis | Rule-based | Risk `EXPIRED_BATCH`, `/api/medicines` | Expired / expiring-in-6-months batches |
| 12 | Shipment quantity consistency | Rule-based over graph | Risk `QUANTITY_MISMATCH` | Inbound qty vs sum of downstream legs |

## Per-operation notes
| # | Inputs → Outputs | Complexity | Assumptions / limitations |
|---|---|---|---|
| 1 | batchId → paths | Proportional to paths expanded; bounded by `*0..3` | Legs form a shallow chain; deeper chains need a larger bound |
| 2 | batchId → subgraph | Index seek + local expansion | Only direct upstream links are modelled (no multi-tier supplier chains) |
| 3 | batchId → subgraph (LIMIT 200/100) | Local, bounded | Truncation flagged via `truncated` |
| 4 | two ids → path | Breadth-first search; depth bounded by the hop limit | Ignores direction; shortest ≠ semantically meaningful |
| 5 | recallId → pharmacies, units | Linear in affected shipments | Units = delivered quantity, not sold; open legs listed as limitations |
| 6 | – → findings | Linear scan of SUPPLIES_TO / delivered shipments | `intendedRegion` is the only definition of "expected" |
| 7 | – → findings | Aggregation over all batches grouped by `lotNumber` (the `batch_lot` index helps point lookups, not this grouping) | Detects shared lot only, not fuzzy IDs |
| 8 | – → top-10 | Full node scan with degree count | Fine at this size (hundreds of nodes); needs sampling at scale |
| 9 | – → counts | Linear in STORED_AT edges | Counts batches, not throughput |
| 10 | – → findings | Pattern predicate per shipment | Required event list is `MANUFACTURED, QC_RELEASED, SHIPPED, RECEIVED` |
| 11 | asOf → batches | Single pass over batches; the planner may use the `batch_expiry` index (verify with PROFILE) | Fixed reference date for reproducibility |
| 12 | – → findings | Linear in shipments | Only two-leg chains assumed |

## Tests
* **Executed (offline):** `backend/tests/test_dataset.py` runs a pure-Python reference implementation of operations 5–7, 10–12 and asserts each flags exactly the seeded scenario batches.
* **Written, not yet executed (needs Neo4j):** `backend/tests/test_integration.py` asserts the Cypher rules return the same sets as the reference (`test_cypher_rules_match_reference`), plus traversal, recall totals, and that every read template runs.

Risk score (documented formula): `riskScore(batch) = Σ severityWeight(finding)`, weights High=3, Medium=2, Low=1; bands none=0, low=1–2, elevated=3–4, high≥5.
Findings are **synthetic indicators, not proof of fraud**.
