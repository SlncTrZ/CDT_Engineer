"""A frozen specified source exercises all architectural feature families."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from execution.plan_compiler import compile_plan_spec
from execution.plan_review import review_plan_spec

FIXTURES = Path(__file__).resolve().parents[1] / "domains" / "building-architecture" / "acceptance-fixtures"


def spec():
    return json.loads((FIXTURES / "full-floor-plan.planspec.json").read_text())


def test_native_fixture_source_identity_and_planning():
    plan = spec()
    assert plan["source_inventory"]["source_sha256"] == hashlib.sha256(
        (FIXTURES / "full-floor-plan.source.json").read_bytes()).hexdigest()
    families = {i["semantic_family"]: i for i in plan["source_inventory"]["items"]}
    assert len(families) == 10
    assert all(i["required"] and i["feature_refs"] for i in families.values())
    assert review_plan_spec(plan, {"release_target": "design_review"}).approved
    assert compile_plan_spec(plan, {"release_target": "design_review"}).ok


@pytest.mark.parametrize("key", ["axes", "walls", "columns", "openings", "spaces", "fixtures", "dimensions"])
def test_native_fixture_cannot_omit_a_required_family(key):
    plan = copy.deepcopy(spec())
    plan["payload"][key] = []
    result = compile_plan_spec(plan, {"release_target": "design_review"})
    assert not result.ok
    assert result.chunks == []
