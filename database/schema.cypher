// PharmaTrace schema — Neo4j 5.x (Community Edition compatible)
// Idempotent: safe to run repeatedly (IF NOT EXISTS).
// NOTE: property-existence constraints (IS NOT NULL) are Enterprise-only, so
// required-field checks are enforced in the application layer (Pydantic).

// ---- Uniqueness constraints (each also creates a backing range index) ----
CREATE CONSTRAINT medicine_id IF NOT EXISTS FOR (n:Medicine) REQUIRE n.medicineId IS UNIQUE;
CREATE CONSTRAINT batch_id IF NOT EXISTS FOR (n:Batch) REQUIRE n.batchId IS UNIQUE;
CREATE CONSTRAINT organization_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.organizationId IS UNIQUE;
CREATE CONSTRAINT location_id IF NOT EXISTS FOR (n:Location) REQUIRE n.locationId IS UNIQUE;
CREATE CONSTRAINT shipment_id IF NOT EXISTS FOR (n:Shipment) REQUIRE n.shipmentId IS UNIQUE;
CREATE CONSTRAINT pharmacy_id IF NOT EXISTS FOR (n:Pharmacy) REQUIRE n.pharmacyId IS UNIQUE;
CREATE CONSTRAINT recall_id IF NOT EXISTS FOR (n:Recall) REQUIRE n.recallId IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (n:TraceabilityEvent) REQUIRE n.eventId IS UNIQUE;

// ---- Secondary indexes for the lookups the application performs ----
CREATE INDEX batch_lot IF NOT EXISTS FOR (n:Batch) ON (n.lotNumber);
CREATE INDEX batch_expiry IF NOT EXISTS FOR (n:Batch) ON (n.expiryDate);
CREATE INDEX batch_status IF NOT EXISTS FOR (n:Batch) ON (n.status);
CREATE INDEX medicine_name IF NOT EXISTS FOR (n:Medicine) ON (n.name);
CREATE INDEX medicine_code IF NOT EXISTS FOR (n:Medicine) ON (n.drugCode);
CREATE INDEX org_role IF NOT EXISTS FOR (n:Organization) ON (n.role);
CREATE INDEX org_verification IF NOT EXISTS FOR (n:Organization) ON (n.verificationStatus);
CREATE INDEX event_type IF NOT EXISTS FOR (n:TraceabilityEvent) ON (n.eventType);
CREATE INDEX shipment_status IF NOT EXISTS FOR (n:Shipment) ON (n.status);
