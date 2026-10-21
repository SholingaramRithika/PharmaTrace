# Data Dictionary
Types are the Neo4j types as loaded by `database/setup_db.py` (dates as `Date`, timestamps as `DateTime`). All values are synthetic.

| Label | Property | Type | Meaning / rule |
|---|---|---|---|
| Medicine | medicineId | String, unique | e.g. `MED-001` |
| | name, drugCode, category | String | Fictional product name, code, therapeutic category |
| | form | String | Tablet / Capsule / Bottle / Vial / Box (selects the bundled illustration) |
| Batch | batchId | String, unique | e.g. `BATCH-001`; `TEST-*` for demo-write records |
| | lotNumber | String, indexed | Production lot; sharing a lot across batches is flagged |
| | manufacturingDate / expiryDate | Date | Expiry must be after manufacture; expiry indexed |
| | quantity | Integer > 0 | Units produced |
| | status | String, indexed | Released / Recalled / Expired / Quarantined |
| | intendedRegion | String | Region the batch is meant for (defines "unexpected route") |
| | isTestRecord | Boolean | Only on `TEST-*` nodes; gates all demo writes/deletes |
| Organization | organizationId | String, unique | `ORG-M01` manufacturer, `S` supplier, `D` distributor, `W` warehouse operator |
| | name, region | String | |
| | role | String, indexed | Manufacturer / Supplier / Distributor / WarehouseOperator |
| | verificationStatus | String, indexed | Verified / Pending / Unverified |
| Location | locationId | String, unique | `LOC-M01…` plants, `LOC-W01…` warehouses |
| | name, region, locationType | String | ManufacturingSite / Warehouse |
| Shipment | shipmentId | String, unique | A transport leg |
| | departureTime, arrivalTime | DateTime | `arrivalTime` is absent while in transit |
| | quantity | Integer > 0 | Units on this leg |
| | status | String, indexed | Delivered / InTransit |
| Pharmacy | pharmacyId | String, unique | `PH-01…PH-14` |
| | name, region, verificationStatus | String | |
| Recall | recallId | String, unique | `RCL-001` (Active), `RCL-002` (Closed) |
| | reason, status | String | Reasons are labelled "Simulated" |
| | issuedAt | DateTime | |
| TraceabilityEvent | eventId | String, unique | |
| | eventType | String, indexed | MANUFACTURED, QC_RELEASED, SHIPPED, RECEIVED, DELIVERED |
| | timestamp | DateTime | |
| | description | String | |
| SUPPLIES_TO (rel) | material | String | Input material supplied to the batch |

Relationship definitions and directions: `GRAPH_SCHEMA.md`.
