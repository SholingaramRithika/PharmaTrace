# Neo4j Overview

> Facts here are stated conservatively. Verify any date or licensing detail against the official sources listed at the end before quoting it.

## Classification and model
Neo4j is a **graph database** that implements the **labelled property graph** model:
* **Nodes** represent entities and carry one or more **labels** (e.g. `Batch`).
* **Relationships** are directed, typed connections between two nodes (e.g. `(:Medicine)-[:HAS_BATCH]->(:Batch)`).
* Both nodes and relationships can hold **properties** (key–value pairs).
It is queried with **Cypher**, a declarative pattern-matching language developed by Neo4j and later opened as the openCypher project.
It is ACID-compliant (see `TRANSACTIONS_AND_CONCURRENCY.md`).

## Origin and ownership (high level)
Neo4j was created by the founders of what became Neo4j, Inc. (formerly Neo Technology): Emil Eifrem, Johan Svensson and Peter Neubauer.
The company maintains the database, offers the open-source **Community Edition**, the commercial **Enterprise Edition**, the managed cloud
service **Aura**, and the desktop tool **Neo4j Desktop**. Version 5 (the line this project targets) is the current major generation at the time of writing.
Exact first-release dates and funding/ownership history are intentionally not asserted here; see <https://neo4j.com/company/>.

## Why it fits traceability
| Need | Graph property used |
|---|---|
| Follow a batch through unknown numbers of hops | Variable-length path patterns |
| Ask "what is connected to X?" | Relationships stored as first-class records, traversed from a starting node |
| Evolving questions and attributes | Schema-flexible properties; new relationship types need no table redesign |
| Explain results visually | Query results are naturally nodes and edges |

## Where it is a weaker fit (be honest in evaluation)
Heavy tabular aggregation/reporting, very simple fixed-schema CRUD, and workloads with no relationship traversal are typically served as well or better by relational databases. See `NEO4J_VS_MYSQL.md`.

## Storage (conceptual)
Neo4j's documentation describes a native graph store in which nodes, relationships and properties are kept in separate store files of fixed-size
records, with each node referencing its relationships so a traversal moves from a node to its neighbours without a global lookup
(often called *index-free adjacency*). Indexes are used to find the **starting** nodes. This project does not inspect store files; read
the Operations/Store format pages in the official docs for details.

## References (official)
* Neo4j documentation home: <https://neo4j.com/docs/>
* Cypher Manual: <https://neo4j.com/docs/cypher-manual/current/>
* Operations Manual (security, backup, clustering): <https://neo4j.com/docs/operations-manual/current/>
* Python driver manual: <https://neo4j.com/docs/python-manual/current/>
* Graph Data Science (not used in this project): <https://neo4j.com/docs/graph-data-science/current/>
* openCypher: <https://opencypher.org/>
* Neo4j downloads / Desktop / Aura: <https://neo4j.com/download/> · <https://neo4j.com/cloud/platform/aura-graph-database/>
* Course context: "Instructions for Case Study & PPT Presentation on Databases" (provided PDF).
