# Limitations and Future Scope
## Current limitations (honest list)
* Cypher/endpoints have not yet been run against a live Neo4j by the author of this code; `tests/smoke_live.py` and `pytest -m neo4j` exist to do so. Expect possible small query fixes.
* Not seen in a real browser: Cytoscape layout/tooltips/drag, theme restyling on canvas, responsiveness. Frontend tests mock Cytoscape and the API.
* Synthetic data only; supply chain is a fixed 2–3 leg pattern; no multi-tier supplier chains; "dispensed" means stock reached the pharmacy, not individual sales.
* No user authentication; no rate limiting; Community-edition constraints only.
* Risk rules are simple, threshold-free pattern checks; the score is a weighted count, not a statistical model.
* Text search and degree analysis scan all nodes.
* Bundled product illustrations are generic, one per package type (not per product).
* No animated particle background (omitted for performance/clarity).
## Possible extensions
Multi-tier suppliers and serialisation (GS1-style identifiers), temporal validation of event order, Graph Data Science (centrality/community detection, only after verifying availability), full-text indexes, authentication and roles, streaming event ingestion, Aura-hosted demo with read-only user, a MySQL benchmark per `PERFORMANCE.md`, accessibility audit with assistive technology, e2e browser tests (Playwright).
