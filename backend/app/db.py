"""Neo4j access layer: connection pooling, serialization and graph DTOs."""
from __future__ import annotations

import re
from typing import Any

from neo4j import GraphDatabase, Driver
from neo4j.graph import Node, Relationship, Path
from neo4j.time import Date, DateTime, Time, Duration

from .config import Settings

ID_KEY = {"Medicine": "medicineId", "Batch": "batchId", "Organization": "organizationId",
          "Location": "locationId", "Shipment": "shipmentId", "Pharmacy": "pharmacyId",
          "Recall": "recallId", "TraceabilityEvent": "eventId"}
NAME_KEY = {"Medicine": "name", "Batch": "batchId", "Organization": "name", "Location": "name",
            "Shipment": "shipmentId", "Pharmacy": "name", "Recall": "recallId",
            "TraceabilityEvent": "eventType"}
REL_TYPES = ["HAS_BATCH", "MANUFACTURES", "SUPPLIES_TO", "TRANSPORTED_IN", "FOLLOWED_BY", "SHIPPED_FROM",
             "DELIVERED_TO", "HANDLED_BY", "STORED_AT", "DISPENSED_AT", "AFFECTED_BY", "HAS_EVENT",
             "RECORDED_AT", "OPERATED_BY"]
SAFE_ID = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")


def parse_node_id(node_id: str) -> tuple[str, str]:
    """'Batch:BATCH-001' -> ('Batch', 'BATCH-001'); raises ValueError if not allowlisted."""
    label, _, ident = node_id.partition(":")
    if label not in ID_KEY or not SAFE_ID.match(ident):
        raise ValueError(f"Invalid node id: {node_id!r}")
    return label, ident


def to_py(v: Any) -> Any:
    if isinstance(v, (Date, DateTime, Time)):
        return v.iso_format()
    if isinstance(v, Duration):
        return str(v)
    if isinstance(v, Node):
        return node_dto(v)
    if isinstance(v, Relationship):
        return {"id": v.element_id, "type": v.type, "properties": to_py(dict(v))}
    if isinstance(v, Path):
        return {"nodes": [node_dto(n) for n in v.nodes],
                "relationships": [{"id": r.element_id, "type": r.type} for r in v.relationships]}
    if isinstance(v, dict):
        return {k: to_py(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [to_py(x) for x in v]
    return v


def node_dto(n: Node) -> dict:
    label = next((l for l in n.labels if l in ID_KEY), next(iter(n.labels), "Unknown"))
    props = to_py(dict(n))
    key = ID_KEY.get(label)
    ident = props.get(key, n.element_id) if key else n.element_id
    return {"id": f"{label}:{ident}", "elementId": n.element_id, "label": label,
            "name": str(props.get(NAME_KEY.get(label, "name"), ident)), "properties": props}


def _walk(v, nodes: dict, rels: dict):
    if isinstance(v, Node):
        nodes.setdefault(v.element_id, node_dto(v))
    elif isinstance(v, Relationship):
        rels.setdefault(v.element_id, v)
    elif isinstance(v, Path):
        for n in v.nodes:
            _walk(n, nodes, rels)
        for r in v.relationships:
            _walk(r, nodes, rels)
    elif isinstance(v, (list, tuple)):
        for x in v:
            _walk(x, nodes, rels)
    elif isinstance(v, dict):
        for x in v.values():
            _walk(x, nodes, rels)


def build_graph(records) -> dict:
    """Collect nodes/relationships from raw records into a de-duplicated graph DTO."""
    nodes: dict = {}
    rels: dict = {}
    for rec in records:
        for v in rec.values():
            _walk(v, nodes, rels)
    edges = []
    for r in rels.values():
        s, t = r.start_node.element_id, r.end_node.element_id
        if s in nodes and t in nodes:  # never emit dangling edges
            edges.append({"id": r.element_id, "source": nodes[s]["id"], "target": nodes[t]["id"],
                          "type": r.type, "properties": to_py(dict(r))})
    return {"nodes": list(nodes.values()), "edges": edges}


def merge_graphs(*graphs: dict, limit: int | None = None) -> dict:
    nodes, edges = {}, {}
    for g in graphs:
        for n in g["nodes"]:
            nodes.setdefault(n["id"], n)
        for e in g["edges"]:
            edges.setdefault(e["id"], e)
    node_list = list(nodes.values())
    truncated = bool(limit and len(node_list) > limit)
    if truncated:
        node_list = node_list[:limit]
        keep = {n["id"] for n in node_list}
        edge_list = [e for e in edges.values() if e["source"] in keep and e["target"] in keep]
    else:
        edge_list = list(edges.values())
    return {"nodes": node_list, "edges": edge_list, "truncated": truncated}


class Neo4jClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._driver: Driver | None = None

    def connect(self):
        s = self.settings
        pwd = s.neo4j_password.get_secret_value() if s.neo4j_password else ""
        self._driver = GraphDatabase.driver(
            s.neo4j_uri, auth=(s.neo4j_user, pwd), max_connection_pool_size=20,
            connection_acquisition_timeout=5, connection_timeout=3,
            max_transaction_retry_time=3)  # fail fast so the UI can show a disconnected state

    def close(self):
        if self._driver:
            self._driver.close()

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            self.connect()
        return self._driver  # type: ignore[return-value]

    def verify(self) -> None:
        self.driver.verify_connectivity()

    def _session(self):
        return self.driver.session(database=self.settings.neo4j_database)

    def read_raw(self, query: str, **params):
        with self._session() as s:
            return s.execute_read(lambda tx: list(tx.run(query, **params)))

    def rows(self, query: str, **params) -> list[dict]:
        return [to_py(dict(r)) for r in self.read_raw(query, **params)]

    def graph(self, query: str, **params) -> dict:
        return build_graph(self.read_raw(query, **params))

    def write(self, query: str, **params) -> tuple[list[dict], dict]:
        def work(tx):
            res = tx.run(query, **params)
            recs = [to_py(dict(r)) for r in res]
            return recs, res.consume().counters
        with self._session() as s:
            recs, c = s.execute_write(work)
        return recs, counters_dict(c)

    def run_lab(self, query: str, params: dict, write: bool) -> dict:
        """Execute an allowlisted template; returns rows, graph, timing, plan."""
        def work(tx):
            res = tx.run(query, **params)
            raw = list(res)
            return raw, res.consume()
        with self._session() as s:
            raw, summ = (s.execute_write if write else s.execute_read)(work)
        plan = summ.profile or summ.plan
        counters = counters_dict(summ.counters)
        return {"columns": list(raw[0].keys()) if raw else [],
                "rows": [to_py(dict(r)) for r in raw], "graph": build_graph(raw),
                "timing": {"resultAvailableAfterMs": summ.result_available_after,
                           "resultConsumedAfterMs": summ.result_consumed_after},
                "counters": counters, "plan": plan_to_dict(plan) if plan else None,
                "profiled": bool(summ.profile)}


def plan_to_dict(p) -> dict | None:
    """Convert the server's plan/profile metadata (a dict per Bolt protocol) to a compact tree."""
    if not p:
        return None
    args = p.get("args", {}) or {}
    return {"operator": p.get("operatorType"), "dbHits": p.get("dbHits"), "rows": p.get("rows"),
            "estimatedRows": args.get("EstimatedRows"), "identifiers": p.get("identifiers", []),
            "children": [plan_to_dict(c) for c in p.get("children", [])]}


def counters_dict(c) -> dict:
    names = ["nodes_created", "nodes_deleted", "relationships_created", "relationships_deleted",
             "properties_set", "labels_added", "labels_removed", "indexes_added", "constraints_added"]
    return {n: getattr(c, n) for n in names if getattr(c, n, 0)}


def total_db_hits(plan: dict | None) -> int:
    if not plan:
        return 0
    return (plan.get("dbHits") or 0) + sum(total_db_hits(c) for c in plan.get("children", []))
