"""Database Lab: allowlisted, parameterized Cypher templates only."""
from __future__ import annotations
import json, re
from functools import lru_cache
from pathlib import Path

CATALOGUE_PATH = Path(__file__).resolve().parents[3] / "database" / "queries" / "catalogue.json"


class ParamError(ValueError):
    pass


@lru_cache
def catalogue() -> dict[str, dict]:
    return {q["id"]: q for q in json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))}


def public_catalogue() -> list[dict]:
    return list(catalogue().values())


def validate_params(spec: dict, supplied: dict | None) -> dict:
    supplied = supplied or {}
    unknown = set(supplied) - set(spec)
    if unknown:
        raise ParamError(f"Unknown parameter(s): {', '.join(sorted(unknown))}")
    out = {}
    for name, rule in spec.items():
        v = supplied.get(name, rule.get("default"))
        if v is None or v == "":
            raise ParamError(f"Parameter '{name}' is required")
        if rule["type"] == "int":
            try:
                v = int(v)
            except (TypeError, ValueError):
                raise ParamError(f"'{name}' must be an integer") from None
            if not rule["min"] <= v <= rule["max"]:
                raise ParamError(f"'{name}' must be between {rule['min']} and {rule['max']}")
        else:
            v = str(v)
            if "pattern" in rule and not re.match(rule["pattern"], v):
                raise ParamError(f"'{name}' has invalid format (expected {rule['pattern']})")
            if "enum" in rule and v not in rule["enum"]:
                raise ParamError(f"'{name}' must be one of {rule['enum']}")
        out[name] = v
    return out


def run_template(client, query_id: str, params: dict | None, writes_enabled: bool) -> dict:
    q = catalogue().get(query_id)
    if q is None:
        raise KeyError(query_id)
    is_write = q["kind"] == "write"
    if is_write and not writes_enabled:
        raise PermissionError("Write templates are disabled (ENABLE_WRITES=false).")
    clean = validate_params(q["params"], params)
    result = client.run_lab(q["cypher"], clean, is_write)
    return {"queryId": query_id, "title": q["title"], "kind": q["kind"], "cypher": q["cypher"],
            "parameters": clean, **result}
