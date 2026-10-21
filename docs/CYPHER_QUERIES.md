# Cypher Query Catalogue

24 parameterized templates (18 read/plan, 6 write). Generated from `database/queries/catalogue.json`, which is the same file the Database Lab API executes.

> **Verification status:** parameter declarations, write-guards and input validation are covered by executed offline tests. Execution of the Cypher itself requires Neo4j and is covered by `backend/tests/test_integration.py`, which has **not yet been run** (no Neo4j server was available in the authoring sandbox). Run it on your machine and record results in `TESTING.md`.

## Q1. Look up a batch with medicine and manufacturer
`id: match_batch` · category: **MATCH** · kind: **read** · concept: MATCH, index seek

Anchors on the unique batchId (index seek) then follows two relationships.

```cypher
MATCH (m:Medicine)-[:HAS_BATCH]->(b:Batch {batchId: $batchId})
OPTIONAL MATCH (o:Organization)-[:MANUFACTURES]->(b)
RETURN b.batchId AS batchId, m.name AS medicine, o.name AS manufacturer,
       toString(b.manufacturingDate) AS manufactured, toString(b.expiryDate) AS expires,
       b.quantity AS quantity, b.status AS status
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `BATCH-VALID-001` | `^[A-Za-z0-9\-]{3,40}$` |

## Q2. Batches per medicine (aggregation)
`id: batch_counts` · category: **Aggregation** · kind: **read** · concept: Aggregation

Counts batches and sums quantity per medicine. Implicit grouping by the non-aggregated column.

```cypher
MATCH (m:Medicine)-[:HAS_BATCH]->(b:Batch)
WHERE coalesce(b.isTestRecord, false) = false
RETURN m.name AS medicine, m.category AS category, count(b) AS batches, sum(b.quantity) AS totalUnits
ORDER BY batches DESC, medicine
```

## Q3. Upstream: who supplied and made a batch
`id: upstream_suppliers` · category: **Traversal** · kind: **read** · concept: Upstream traversal

Walks relationships backwards (incoming direction) from a batch to its upstream parties.

```cypher
MATCH p = (x)-[:MANUFACTURES|SUPPLIES_TO|HAS_BATCH]->(b:Batch {batchId: $batchId})
RETURN p
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `BATCH-UNVER-001` | `^[A-Za-z0-9\-]{3,40}$` |

## Q4. Downstream destinations (variable-length path)
`id: downstream_varlen` · category: **Traversal** · kind: **read** · concept: Variable-length path

Follows 0..3 FOLLOWED_BY hops between shipment legs, then DELIVERED_TO. Bounded to avoid unbounded expansion.

```cypher
MATCH p = (b:Batch {batchId: $batchId})-[:TRANSPORTED_IN]->(:Shipment)
           -[:FOLLOWED_BY*0..3]->(s:Shipment)-[:DELIVERED_TO]->(dest)
RETURN p
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `BATCH-RECALL-001` | `^[A-Za-z0-9\-]{3,40}$` |

## Q5. Shortest path from batch to pharmacy
`id: shortest_path` · category: **Path analysis** · kind: **read** · concept: shortestPath

shortestPath over any relationship type, ignoring direction, bounded to 8 hops.

```cypher
MATCH (b:Batch {batchId: $batchId}), (p:Pharmacy {pharmacyId: $pharmacyId})
MATCH path = shortestPath((b)-[*..8]-(p))
RETURN path, length(path) AS hops
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `BATCH-VALID-001` | `^[A-Za-z0-9\-]{3,40}$` |
| `pharmacyId` | string | `PH-01` | `^PH-[0-9]{2}$` |

## Q6. Recall propagation: affected pharmacies and units
`id: recall_propagation` · category: **Recall** · kind: **read** · concept: Recall propagation

From a recall, traverse to affected batches, then every shipment that reached a pharmacy.

```cypher
MATCH (r:Recall {recallId: $recallId})<-[:AFFECTED_BY]-(b:Batch)
      -[:TRANSPORTED_IN]->(s:Shipment)-[:DELIVERED_TO]->(p:Pharmacy)
RETURN p.pharmacyId AS pharmacyId, p.name AS pharmacy, p.region AS region,
       collect(DISTINCT b.batchId) AS batches, sum(s.quantity) AS unitsDelivered
ORDER BY unitsDelivered DESC
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `recallId` | string | `RCL-001` | `^RCL-[0-9]{3}$` |

## Q7. Recall impact subgraph
`id: recall_graph` · category: **Recall** · kind: **read** · concept: Graph result

Returns the recall, affected batches and their downstream shipments as a graph.

```cypher
MATCH p = (r:Recall {recallId: $recallId})<-[:AFFECTED_BY]-(b:Batch)-[:TRANSPORTED_IN]->(s:Shipment)
          -[:DELIVERED_TO]->(:Pharmacy)
RETURN p LIMIT 100
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `recallId` | string | `RCL-001` | `^RCL-[0-9]{3}$` |

## Q8. Conflicting lot numbers
`id: dup_lots` · category: **Risk rule** · kind: **read** · concept: Duplicate detection

Groups batches by lotNumber; more than one batch per lot is flagged. (batchId itself is protected by a unique constraint.)

```cypher
MATCH (b:Batch)
WITH b.lotNumber AS lot, collect(b.batchId) AS batches
WHERE size(batches) > 1
RETURN lot, batches
```

## Q9. Batches supplied by non-verified organizations
`id: unverified_suppliers` · category: **Risk rule** · kind: **read** · concept: Unexpected relationship

Finds SUPPLIES_TO relationships whose source is not Verified.

```cypher
MATCH (o:Organization)-[r:SUPPLIES_TO]->(b:Batch)
WHERE o.verificationStatus <> 'Verified'
RETURN o.name AS supplier, o.verificationStatus AS status, r.material AS material, b.batchId AS batchId
```

## Q10. Expired batches as of a date
`id: expired_batches` · category: **Risk rule** · kind: **read** · concept: Expiry analysis

Temporal comparison on an indexed date property.

```cypher
MATCH (b:Batch)
WHERE b.expiryDate < date($asOf)
RETURN b.batchId AS batchId, toString(b.expiryDate) AS expiry, b.status AS status
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `asOf` | string | `2026-10-18` | `^\d{4}-\d{2}-\d{2}$` |

## Q11. Shipment quantity consistency
`id: quantity_check` · category: **Risk rule** · kind: **read** · concept: Quantity consistency

Compares the inbound shipment quantity with the sum of the downstream legs.

```cypher
MATCH (b:Batch)-[:TRANSPORTED_IN]->(s1:Shipment)
WHERE NOT ()-[:FOLLOWED_BY]->(s1)
OPTIONAL MATCH (s1)-[:FOLLOWED_BY]->(s2:Shipment)
WITH b, s1, coalesce(sum(s2.quantity), 0) AS downstream
WHERE downstream <> s1.quantity
RETURN b.batchId AS batchId, s1.quantity AS inbound, downstream, downstream - s1.quantity AS difference
```

## Q12. Most connected entities
`id: high_degree` · category: **Graph analytics** · kind: **read** · concept: Degree centrality

Degree centrality computed with a COUNT subquery.

```cypher
MATCH (n)
WITH n, COUNT { (n)--() } AS degree
RETURN labels(n)[0] AS label, coalesce(n.name, n.batchId, n.shipmentId, n.eventId) AS entity, degree
ORDER BY degree DESC LIMIT 10
```

## Q13. Warehouse concentration (bottleneck view)
`id: warehouse_bottlenecks` · category: **Graph analytics** · kind: **read** · concept: Bottleneck identification

Counts distinct batches stored at each warehouse location.

```cypher
MATCH (b:Batch)-[:STORED_AT]->(l:Location)
RETURN l.name AS warehouse, l.region AS region, count(DISTINCT b) AS batches
ORDER BY batches DESC
```

## Q14. Shipments with no destination (missing links)
`id: orphan_check` · category: **Graph analytics** · kind: **read** · concept: Orphan / missing-link detection

Pattern predicate NOT (s)-[:DELIVERED_TO]->() finds incomplete paths.

```cypher
MATCH (b:Batch)-[:TRANSPORTED_IN]->(s:Shipment)
WHERE NOT (s)-[:DELIVERED_TO]->()
RETURN b.batchId AS batchId, s.shipmentId AS shipmentId, s.status AS status
```

## Q15. Inspect indexes
`id: show_indexes` · category: **Schema** · kind: **read** · concept: Index inspection

Lists indexes and their state.

```cypher
SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state
RETURN name, type, entityType, labelsOrTypes, properties, state ORDER BY name
```

## Q16. Inspect constraints
`id: show_constraints` · category: **Schema** · kind: **read** · concept: Constraint inspection

Lists constraints.

```cypher
SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties
RETURN name, type, entityType, labelsOrTypes, properties ORDER BY name
```

## Q17. EXPLAIN: batch lookup by id
`id: explain_lookup` · category: **Query plan** · kind: **explain** · concept: EXPLAIN

EXPLAIN shows the plan without executing. Expect a NodeUniqueIndexSeek.

```cypher
EXPLAIN MATCH (b:Batch {batchId: $batchId}) RETURN b
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `BATCH-VALID-001` | `^[A-Za-z0-9\-]{3,40}$` |

## Q18. PROFILE: downstream traversal
`id: profile_traversal` · category: **Query plan** · kind: **profile** · concept: PROFILE

PROFILE executes and reports db hits and rows per operator.

```cypher
PROFILE MATCH (b:Batch {batchId: $batchId})-[:TRANSPORTED_IN]->(:Shipment)-[:DELIVERED_TO]->(p:Pharmacy)
RETURN p.name AS pharmacy, count(*) AS shipments
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `BATCH-RECALL-001` | `^[A-Za-z0-9\-]{3,40}$` |

## Q19. CREATE a test batch
`id: create_test_batch` · category: **CREATE** · kind: **write** · concept: CREATE + unique constraint

Creates a TEST-* batch linked to a medicine. Re-running with the same id fails on the unique constraint.

```cypher
MATCH (m:Medicine {medicineId: $medicineId})
CREATE (m)-[:HAS_BATCH]->(b:Batch {batchId: $batchId, lotNumber: 'LOT-TEST', manufacturingDate: date('2026-09-01'),
       expiryDate: date('2028-09-01'), quantity: $quantity, status: 'Quarantined', isTestRecord: true})
RETURN b.batchId AS batchId, b.status AS status, b.quantity AS quantity
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `TEST-DEMO-1` | `^TEST-[A-Z0-9\-]{3,30}$` |
| `medicineId` | string | `MED-001` | `^MED-[0-9]{3}$` |
| `quantity` | int | `500` | `1..1000000` |

## Q20. MERGE a test batch (idempotent)
`id: merge_test_batch` · category: **MERGE** · kind: **write** · concept: MERGE ON CREATE / ON MATCH

MERGE matches or creates; running twice never duplicates.

```cypher
MERGE (b:Batch {batchId: $batchId})
ON CREATE SET b.isTestRecord = true, b.status = 'Quarantined', b.quantity = $quantity, b.createdAt = datetime()
ON MATCH SET b.lastSeenAt = datetime()
WITH b WHERE b.isTestRecord = true
RETURN b.batchId AS batchId, b.status AS status, b.createdAt IS NOT NULL AS created
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `TEST-DEMO-2` | `^TEST-[A-Z0-9\-]{3,30}$` |
| `quantity` | int | `250` | `1..1000000` |

## Q21. SET a property on a test batch
`id: set_test_status` · category: **SET** · kind: **write** · concept: SET

Updates status; guarded so only isTestRecord nodes can change.

```cypher
MATCH (b:Batch {batchId: $batchId}) WHERE b.isTestRecord = true
SET b.status = $status, b.note = 'status changed in Database Lab'
RETURN b.batchId AS batchId, b.status AS status, b.note AS note
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `TEST-DEMO-1` | `^TEST-[A-Z0-9\-]{3,30}$` |
| `status` | string | `Released` | `['Quarantined', 'Released', 'Recalled', 'Expired']` |

## Q22. REMOVE a property
`id: remove_test_note` · category: **REMOVE** · kind: **write** · concept: REMOVE

REMOVE deletes one property (not the node).

```cypher
MATCH (b:Batch {batchId: $batchId}) WHERE b.isTestRecord = true
REMOVE b.note
RETURN b.batchId AS batchId, b.note IS NULL AS noteRemoved
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `TEST-DEMO-1` | `^TEST-[A-Z0-9\-]{3,30}$` |

## Q23. Create a relationship
`id: create_test_relationship` · category: **CREATE** · kind: **write** · concept: Relationship creation

MERGE a SUPPLIES_TO relationship from an organization to a test batch.

```cypher
MATCH (b:Batch {batchId: $batchId}) WHERE b.isTestRecord = true
MATCH (o:Organization {organizationId: $organizationId})
MERGE (o)-[r:SUPPLIES_TO {material: $material}]->(b)
RETURN o.name AS supplier, type(r) AS rel, b.batchId AS batchId
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `TEST-DEMO-1` | `^TEST-[A-Z0-9\-]{3,30}$` |
| `organizationId` | string | `ORG-S01` | `^ORG-[A-Z][0-9]{2}$` |
| `material` | string | `Demo material` | `^[A-Za-z0-9 \-]{1,40}$` |

## Q24. Safe DELETE of a test batch
`id: delete_test_batch` · category: **DELETE** · kind: **write** · concept: DELETE

DETACH DELETE removes the node and its relationships. Guarded to isTestRecord nodes only.

```cypher
MATCH (b:Batch {batchId: $batchId}) WHERE b.isTestRecord = true
WITH b, b.batchId AS id
DETACH DELETE b
RETURN id AS deleted
```

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `batchId` | string | `TEST-DEMO-1` | `^TEST-[A-Z0-9\-]{3,30}$` |
