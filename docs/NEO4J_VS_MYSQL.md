# Neo4j vs MySQL
> **This is a conceptual and query-level comparison, not an executed benchmark.** MySQL was not installed or measured in this project and no timings are reported. Neo4j is not universally faster; the right choice depends on the workload.

| Aspect | Neo4j (property graph) | MySQL (relational) |
|---|---|---|
| Data model | Nodes, typed directed relationships, properties | Tables, rows, foreign keys |
| Relationships | First-class stored records, traversed from a node | Implied by keys, resolved with joins |
| Multi-hop traversal | Path patterns; hop count is part of the pattern (`*0..3`, `shortestPath`) | Self/multi-joins or `WITH RECURSIVE` (MySQL 8+); complexity grows with hops |
| Query language | Cypher (declarative patterns) | SQL (mature, standardised) |
| Indexing | Range/text/etc. indexes find start nodes; uniqueness constraints | B-tree indexes on columns; PK/FK/unique constraints |
| Transactions | ACID | ACID (InnoDB) |
| Schema | Flexible labels/properties; constraints optional | Strict schema, strong typing, rich constraint set (NOT NULL, CHECK, FK) |
| Aggregation/reporting | Supported but not its main strength | Excellent; large ecosystem (BI tools) |
| Scalability | Single instance (Community); clustering in Enterprise/Aura | Replication, read replicas, various sharding approaches; very widely operated |
| Security | Auth built in; RBAC fine-grained in Enterprise | Users/roles/grants, TLS, mature tooling |
| Cost/licensing | Community: GPL; Enterprise: commercial; Aura: paid cloud | Community: GPL; Enterprise: commercial; widely hosted, many free tiers |
| Best fit | Highly connected data, variable-depth traversal, path/impact analysis | Well-defined tabular transactions, reporting, wide tooling needs |

## Equivalent examples (written, not benchmarked)
Assume a relational layout: `batch(batch_id,…)`, `shipment(shipment_id, batch_id, from_shipment_id, dest_type, dest_id, quantity)`, `pharmacy(pharmacy_id,…)`, `recall_batch(recall_id,batch_id)`.

**1. Recall impact: pharmacies and units reached by recall RCL-001**
```cypher
MATCH (r:Recall {recallId:'RCL-001'})<-[:AFFECTED_BY]-(b:Batch)-[:TRANSPORTED_IN]->(s:Shipment)-[:DELIVERED_TO]->(p:Pharmacy)
RETURN p.name, sum(s.quantity) AS units
```
```sql
SELECT p.name, SUM(s.quantity) AS units
FROM recall_batch rb JOIN shipment s ON s.batch_id = rb.batch_id
JOIN pharmacy p ON s.dest_type='Pharmacy' AND s.dest_id = p.pharmacy_id
WHERE rb.recall_id='RCL-001' GROUP BY p.name;
```
One hop depth here: both are straightforward; SQL is arguably equally clear.

**2. Variable-depth downstream legs (0..3 hops)**
```cypher
MATCH p=(:Batch {batchId:$id})-[:TRANSPORTED_IN]->(:Shipment)-[:FOLLOWED_BY*0..3]->(s:Shipment)-[:DELIVERED_TO]->(d) RETURN p
```
```sql
WITH RECURSIVE legs AS (
  SELECT shipment_id, 0 AS depth FROM shipment WHERE batch_id=@id AND from_shipment_id IS NULL
  UNION ALL
  SELECT s.shipment_id, l.depth+1 FROM shipment s JOIN legs l ON s.from_shipment_id = l.shipment_id WHERE l.depth < 3)
SELECT s.* FROM legs l JOIN shipment s USING (shipment_id) WHERE s.dest_id IS NOT NULL;
```
**3. Shortest connection between a batch and a pharmacy** — Cypher: one `shortestPath((b)-[*..8]-(p))`. SQL: no built-in shortest-path; needs a recursive CTE with cycle control or application code.

**4. Duplicate lot detection** — equivalent in both (`GROUP BY lot HAVING COUNT(*)>1`); SQL is natural here.

## When MySQL may be preferable
Fixed schema with heavy reporting, strict typed constraints (CHECK, NOT NULL, FKs enforced by the engine), team familiarity, BI integration, or when most queries are 1–2 joins.

## Why Neo4j suits this project
Traceability is dominated by variable-depth path questions and "what is connected to X" investigations, and the results are naturally visualised as graphs. Whether Neo4j is faster for a given dataset must be measured; see `PERFORMANCE.md` for how to measure the Neo4j side.
