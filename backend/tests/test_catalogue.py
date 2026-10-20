import re
import pytest
from app.services import lab

CAT = lab.catalogue()
READ = [q for q in CAT.values() if q["kind"] != "write"]
WRITE = [q for q in CAT.values() if q["kind"] == "write"]


def test_at_least_twelve_queries():
    assert len(CAT) >= 12 and len(READ) >= 12 and len(WRITE) >= 5


@pytest.mark.parametrize("q", CAT.values(), ids=lambda q: q["id"])
def test_declared_params_match_cypher(q):
    used = set(re.findall(r"\$(\w+)", q["cypher"]))
    assert used == set(q["params"]), (used, set(q["params"]))


@pytest.mark.parametrize("q", CAT.values(), ids=lambda q: q["id"])
def test_defaults_validate(q):
    lab.validate_params(q["params"], {})


@pytest.mark.parametrize("q", WRITE, ids=lambda q: q["id"])
def test_write_templates_are_test_scoped(q):
    c = q["cypher"]
    assert "isTestRecord" in c
    assert q["params"]["batchId"]["pattern"].startswith("^TEST-")


@pytest.mark.parametrize("q", READ, ids=lambda q: q["id"])
def test_read_templates_have_no_write_clauses(q):
    assert not re.search(r"\b(CREATE|MERGE|DELETE|SET|REMOVE|DROP|CALL)\b(?! INDEX| CONSTRAINT)", q["cypher"].replace("SHOW CONSTRAINTS", "").replace("SHOW INDEXES", "")), q["id"]


def test_param_validation_rejects_bad_input():
    spec = CAT["create_test_batch"]["params"]
    for bad in [{"batchId": "BATCH-001"}, {"batchId": "TEST-X'); MATCH (n) DETACH DELETE n //"}, {"quantity": 0},
                {"quantity": "abc"}, {"medicineId": "x"}, {"hacker": 1}]:
        with pytest.raises(lab.ParamError):
            lab.validate_params(spec, bad)


def test_enum_param():
    with pytest.raises(lab.ParamError):
        lab.validate_params(CAT["set_test_status"]["params"], {"status": "Hacked"})
