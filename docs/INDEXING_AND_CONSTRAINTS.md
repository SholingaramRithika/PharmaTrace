# Indexing and Constraints
Defined in `database/schema.cypher` (17 idempotent statements, `IF NOT EXISTS`, Neo4j 5.x syntax).

## Uniqueness constraints (8)
One per label key (`batch_id`, `medicine_id`, `organization_id`, `location_id`, `shipment_id`, `pharmacy_id`, `recall_id`, `event_id`).
A uniqueness constraint (a) rejects duplicate keys with a constraint-violation error and (b) is backed by an index, so lookups by key are index seeks.
Demonstration: Database Lab → *CREATE a test batch* twice → second run fails with a constraint violation (HTTP 409 in the CRUD API).

## Secondary indexes (9)
`batch_lot`, `batch_expiry`, `batch_status`, `medicine_name`, `medicine_code`, `org_role`, `org_verification`, `event_type`, `shipment_status` — range indexes on properties used in filters.
Whether the planner *chooses* an index for a given query must be checked with EXPLAIN/PROFILE (Lab templates `explain_lookup`, `profile_traversal`; Insights page runs three PROFILEs live).
Expected for a `batchId` lookup: a unique index seek operator, small db hits. This is an expectation to confirm in your environment, not a recorded result.

## What is *not* enforced by the database (and why)
Property-existence and node-key constraints are Enterprise-only, so required fields, `quantity > 0`, `expiry > manufacture`, `TEST-` prefix and enum values are enforced in Pydantic models (`routers/crud.py`) and the Lab parameter validator (`services/lab.py`).
The unique constraint on `batchId` makes literal duplicate batch IDs impossible; "conflicting identifier" is therefore modelled as the same `lotNumber` on different batches.

## Integrity at load time
`setup_db.py load` uses `MERGE` on key properties, so re-running never duplicates nodes or relationships; `validate` compares live counts with the generator.
Offline tests prove: unique IDs per label, no dangling relationships, no duplicate relationships, positive quantities, valid date order.

## Inspecting
`SHOW INDEXES` / `SHOW CONSTRAINTS` via Lab templates `show_indexes`, `show_constraints` and the Insights page.
