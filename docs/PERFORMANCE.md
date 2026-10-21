# Performance
**No benchmark results are claimed.** No timing was measured in the authoring environment (no Neo4j server was available), and no MySQL comparison was run. Numbers appear only where the application measures them live on *your* machine.

## What the application measures for you
* **Database Lab** shows, per run: rows, `resultAvailableAfter` and `resultConsumedAfter` (ms, from the driver's result summary), and — for `PROFILE` templates — per-operator rows and **db hits**.
* **Database Insights** runs three `PROFILE` queries live (unique-index lookup, two-hop downstream traversal, filter on `expiryDate`) and shows total db hits and timing.
Timings vary with hardware, cache warmth and driver/server version; repeat runs and report medians if you cite them.

## Design choices that affect performance (reasoned, to be confirmed with PROFILE)
| Choice | Why |
|---|---|
| Start every traversal from a uniquely indexed key (`batchId`, `recallId`) | Cheap anchor, then local expansion |
| Bounded patterns (`*0..3`, `shortestPath ≤ 8–10`, `LIMIT`) | Prevents combinatorial path explosion |
| Directed, typed relationships in patterns | Lets the planner skip irrelevant relationships |
| Aggregation done in Cypher, shaping in Python | Fewer round trips for rules; some endpoints issue several queries (e.g. risk = 7) |
| Text search scans all nodes | Acceptable at ~485 nodes; would need a text index at scale |
| Degree analysis scans all nodes | Same caveat |

## Factors that would matter at larger scale
Page-cache size vs graph size, supernodes (e.g. a warehouse linked to thousands of batches), index selectivity, number of hops, and result sizes returned to the browser.

## How to produce a benchmark honestly
1. Record environment (CPU, RAM, Neo4j version/edition, driver version).
2. Run each Lab template ≥ 30 times after a warm-up; record median and p95.
3. For a MySQL comparison, load the *same logical dataset* (export `database/dataset.py` output), use the SQL in `NEO4J_VS_MYSQL.md`, same machine, warm cache.
4. Report both, including cases where MySQL wins.
