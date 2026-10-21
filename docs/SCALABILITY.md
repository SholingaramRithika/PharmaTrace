# Scalability and Replication
Statements reflect Neo4j's documented edition split; no scaling test was run in this project.

| Topic | Community (used locally) | Enterprise / Aura |
|---|---|---|
| Deployment | Single server instance | Clustering for availability and read scaling (documented in the Operations Manual); Aura is managed |
| Replication | None built in | Cluster members replicate via a consensus protocol (see Operations Manual: Clustering) |
| Scale-up | Add RAM/CPU/fast disk; page cache sizing matters for traversals | Same, plus cluster topology options |
| Backup | Offline dump/load | Online backup |

**Vertical vs horizontal:** graph traversals benefit from the working set being in memory; horizontal scaling of a single large connected graph is harder than for key-based data because relationships cross partitions. Consult current Neo4j documentation for the product's present sharding/partitioning offerings before making claims.

**This project:** ~485 nodes / ~1.4k relationships; a single local instance is more than sufficient. Application-level scaling levers already present: bounded queries, `LIMIT`s, node caps in the UI, connection pooling (20), stateless API (can run multiple instances).
Limits to expect on larger data: the degree analysis and text search endpoints scan all nodes; they would need indexes/sampling at scale (see `FUTURE_SCOPE.md`).
