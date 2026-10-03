"""Regression: unsafe numbers and excessive review work never reach CAD."""
import copy
import math
from unittest.mock import patch

import pytest

from execution.planspec import validate_plan_spec
from execution.plan_review import review_plan_spec
from execution.plan_compiler import compile_plan_spec
from execution.source_calibration import calibrate_plan_source
from test_plan_review_gates_20260917 import _valid_arch_spec


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("path", [
    ("payload", "spaces", 0, "boundary_polygon", 2, 0),
    ("coordinate_system", "origin", 0),
    ("coordinate_system", "scale", "horizontal"),
    ("payload", "dimensions", 0, "witness_points", 1, 0),
    ("payload", "walls", 0, "height"),
    ("provenance_ledger", "space_living", "confidence"),
])
def test_nonfinite_input_is_rejected_before_review_and_compile(value, path):
    spec = _valid_arch_spec()
    target = spec
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert not validate_plan_spec(spec).valid
    assert not review_plan_spec(spec).approved
    result = compile_plan_spec(spec)
    assert not result.ok
    assert result.chunks == []


@pytest.mark.parametrize("value", [1e200, 10 ** 400])
def test_unrepresentable_numeric_magnitude_is_rejected(value):
    spec = _valid_arch_spec()
    spec["payload"]["spaces"][0]["boundary_polygon"][2][0] = value
    assert not validate_plan_spec(spec).valid
    assert not compile_plan_spec(spec).ok


def test_cyclic_python_input_returns_rejection_instead_of_recursion_error():
    spec = _valid_arch_spec()
    spec["metadata"] = spec
    assert not validate_plan_spec(spec).valid


def test_oversized_polygon_never_reaches_quadratic_geometry():
    spec = _valid_arch_spec()
    spec["payload"]["spaces"][0]["boundary_polygon"] = [
        [2500 + 1000 * math.cos(i / 300 * 2 * math.pi),
         2000 + 1000 * math.sin(i / 300 * 2 * math.pi)] for i in range(300)]
    with patch("execution.plan_review._polygon_self_intersects",
               side_effect=AssertionError("quadratic geometry was entered")):
        result = review_plan_spec(spec)
    assert not result.approved
    assert any("review_budget" in r for f in result.findings for r in f["reason_codes"])


def test_many_walls_never_reach_pairwise_join_gate():
    spec = _valid_arch_spec()
    spec["payload"]["walls"] = [
        dict(spec["payload"]["walls"][0], wall_id=f"wall_{i}") for i in range(300)]
    for wall in spec["payload"]["walls"]:
        spec["provenance_ledger"][wall["wall_id"]] = {
            "status": "specified", "source_id": "test-source"}
    with patch("execution.plan_review._gate_g5_wall_joins",
               side_effect=AssertionError("pairwise gate was entered")):
        result = review_plan_spec(spec)
    assert not result.approved
    assert any("review_budget" in r for f in result.findings for r in f["reason_codes"])


def test_overflow_after_calibration_does_not_claim_derived_coordinates():
    result = calibrate_plan_source(
        source={"source_id": "overflow", "pixel_width": 100, "pixel_height": 100},
        anchors=[{"anchor_id": "a", "pixel_from": [0, 0], "pixel_to": [1, 0],
                  "real_length": 1e307, "unit": "mm"}],
        pixel_features=[{"feature_id": "p", "kind": "point", "pixels": [100, 0]}])
    assert result.verdict == "INVALID_SOURCE"
    assert result.features == []
    assert result.provenance_ledger.get("p", {}).get("status") != "derived"
    assert result.errors


def test_valid_plan_and_calibration_preserve_inputs():
    spec = _valid_arch_spec()
    before = copy.deepcopy(spec)
    assert review_plan_spec(spec).approved
    assert compile_plan_spec(spec).ok
    assert spec == before
    result = calibrate_plan_source(
        source={"source_id": "ordinary", "pixel_width": 100, "pixel_height": 100},
        anchors=[{"anchor_id": "a", "pixel_from": [0, 0], "pixel_to": [100, 0],
                  "real_length": 5, "unit": "m"}],
        pixel_features=[{"feature_id": "p", "kind": "point", "pixels": [100, 0]}])
    assert result.verdict == "CALIBRATED"
    assert result.features[0]["coords_mm"] == [5000, 5000]

@pytest.mark.parametrize("field", ["pixel_width", "pixel_height"])
def test_huge_integer_source_dimension_is_invalid_not_an_exception(field):
    source = {"source_id": "s", "pixel_width": 100, "pixel_height": 100}
    source[field] = 10 ** 400
    assert calibrate_plan_source(source=source).verdict == "INVALID_SOURCE"


def test_huge_integer_review_requirement_is_a_typed_input_error():
    with pytest.raises(ValueError, match="finite numeric"):
        review_plan_spec(_valid_arch_spec(), {"min_space_area": 10 ** 400})


def test_deep_input_is_rejected_before_recursive_schema():
    spec = _valid_arch_spec()
    nested = []
    cursor = nested
    for _ in range(60):
        child = []
        cursor.append(child)
        cursor = child
    spec["metadata"] = nested
    with patch("execution.planspec._VALIDATOR") as validator:
        validator.iter_errors.side_effect = AssertionError("schema recursion was entered")
        assert not validate_plan_spec(spec).valid


def test_duplicate_space_id_cannot_hide_an_oversized_polygon():
    spec = _valid_arch_spec()
    original = copy.deepcopy(spec["payload"]["spaces"][0])
    spec["payload"]["spaces"][0]["boundary_polygon"] = [[i, i % 2] for i in range(300)]
    spec["payload"]["spaces"].append(original)
    result = review_plan_spec(spec)
    assert not result.approved
    assert any("review_budget" in r for f in result.findings for r in f["reason_codes"])


def test_malformed_chunk_dependencies_is_rejected_without_type_error():
    spec = _valid_arch_spec()
    spec["chunk_dependencies"] = 3
    assert not validate_plan_spec(spec).valid
