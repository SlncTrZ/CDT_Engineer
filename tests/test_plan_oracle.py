"""Independent plan-execution oracle tests (ENG-R03).
Wing: code | Topic: building-plan-oracle | Updated: 2026-09-17

Coverage:
- every ``e2e-fixtures/*.json`` satisfies the CDT-SketchUp ``create_mesh``
  native validity bounds (unique vertices, face budgets, distinct face sets);
- every fixture recipe reproduces byte-identical output when its recorded
  planner inputs are re-executed (fixtures come from the real planner);
- oracle verdicts: pass / blocked / reduced_scope over envelope, counts,
  edge-manifold, Euler, manifold agreement, volume and deviation checks.

NOTE: simulated native receipts below prove oracle mathematics only. They
are explicitly labeled and never presented as native execution evidence;
the live planner -> create_mesh -> get_entity_state run remains the final
ENG-R03 acceptance step (see benchmark-pack §E2E).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from domains.building_architecture.geometry_planner import (
    plan_loft_mesh,
    plan_profile_sweep,
    sample_circular_arc,
)
from domains.building_architecture.plan_oracle import (
    assess_plan_execution,
    evaluate_edge_manifold,
    evaluate_envelope,
    evaluate_euler,
    evaluate_volume,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "domains" / "building-architecture" / "e2e-fixtures"
CASE_IDS = [
    "straight-rect-sweep",
    "tapered-quad-loft",
    "concave-c-sweep",
    "curved-rect-sweep",
    "four-section-loft",
]


def _load(case_id: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{case_id}.json").read_text(encoding="utf-8"))


def _replan(fixture: dict) -> dict:
    inputs = fixture["planner_inputs"]
    if fixture["planner"] == "plan_profile_sweep":
        if "arc" in inputs:
            arc_spec = inputs["arc"]
            arc = sample_circular_arc(
                center=arc_spec["center"],
                radius=arc_spec["radius"],
                start_angle_deg=arc_spec["start_angle_deg"],
                end_angle_deg=arc_spec["end_angle_deg"],
                max_chord_error=arc_spec["max_chord_error"],
            )
            path = arc["points"]
            allowed = arc_spec["max_chord_error"]
            observed = arc["max_chord_error_bound"]
        else:
            path = inputs["path"]
            allowed = 0.0
            observed = 0.0
        return plan_profile_sweep(
            profile=inputs["profile"],
            path=path,
            max_path_deviation=allowed,
            observed_path_deviation=observed,
        )
    return plan_loft_mesh(inputs["sections"])


def _simulated_receipt(fixture: dict, **overrides) -> dict:
    """Build a synthetic executor read-back mirroring get_entity_state.

    Synthetic only: proves oracle math, never native execution evidence.
    """
    expected = fixture["expected"]
    receipt = {
        "bbox": {
            "min": list(expected["bounds"]["min"]),
            "max": list(expected["bounds"]["max"]),
        },
        "vertex_count": expected["vertex_count"],
        "face_count": expected["face_count"],
        "manifold": True,
        "volume": expected["expected_volume"],
        "unit": "mm",
    }
    receipt.update(overrides)
    return receipt


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_fixture_satisfies_create_mesh_native_bounds(case_id):
    fixture = _load(case_id)
    points = fixture["recipe"]["points"]
    faces = fixture["recipe"]["faces"]
    assert 3 <= len(points) <= 2048
    assert 1 <= len(faces) <= 4096
    assert len({tuple(point) for point in points}) == len(points)
    seen = set()
    for face in faces:
        assert 3 <= len(face) <= 16
        assert len(set(face)) == len(face)
        assert all(0 <= index < len(points) for index in face)
        key = tuple(sorted(face))
        assert key not in seen
        seen.add(key)
    refs = sum(len(face) for face in faces)
    assert refs <= 32768
    payload = fixture["create_mesh"]
    assert payload["expect"]["vertex_count"] == len(points)
    assert payload["expect"]["face_count"] == len(faces)


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_fixture_recipe_reproduces_from_recorded_inputs(case_id):
    fixture = _load(case_id)
    fresh = _replan(fixture)
    assert fresh["points"] == fixture["recipe"]["points"]
    assert fresh["faces"] == fixture["recipe"]["faces"]
    assert fresh["bounds"] == fixture["recipe"]["bounds"]


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_fixture_recipe_is_edge_manifold_with_euler_two(case_id):
    fixture = _load(case_id)
    recipe = fixture["recipe"]
    manifold = evaluate_edge_manifold(recipe["faces"])
    assert manifold["result"] == "pass"
    euler = evaluate_euler(
        recipe["vertex_count"], manifold["edge_count"], recipe["face_count"]
    )
    assert euler == {"result": "pass", "characteristic": 2}


def test_oracle_passes_exact_straight_sweep_receipt():
    fixture = _load("straight-rect-sweep")
    result = assess_plan_execution(
        fixture["recipe"], fixture["expected"],
        _simulated_receipt(fixture),
    )
    assert result["verdict"] == "pass"
    assert all(check["result"] == "pass" for check in result["checks"].values())


def test_oracle_blocks_envelope_mismatch():
    fixture = _load("straight-rect-sweep")
    receipt = _simulated_receipt(fixture)
    receipt["bbox"]["max"] = [101.0, 10.0, 20.0]
    result = assess_plan_execution(fixture["recipe"], fixture["expected"], receipt)
    assert result["verdict"] == "blocked"
    assert result["checks"]["envelope"]["result"] == "fail"


def test_oracle_blocks_volume_mismatch():
    fixture = _load("tapered-quad-loft")
    receipt = _simulated_receipt(fixture, volume=20000.0)
    result = assess_plan_execution(fixture["recipe"], fixture["expected"], receipt)
    assert result["verdict"] == "blocked"
    assert result["checks"]["volume"]["result"] == "fail"


def test_oracle_blocks_count_and_manifold_disagreement():
    fixture = _load("straight-rect-sweep")
    receipt = _simulated_receipt(fixture, face_count=7, manifold=False)
    result = assess_plan_execution(fixture["recipe"], fixture["expected"], receipt)
    assert result["verdict"] == "blocked"
    assert result["checks"]["counts"]["result"] == "fail"
    assert result["checks"]["manifold_agreement"]["result"] == "fail"


def test_oracle_reduced_scope_without_native_receipt():
    fixture = _load("straight-rect-sweep")
    result = assess_plan_execution(fixture["recipe"], fixture["expected"], None)
    assert result["verdict"] == "reduced_scope"
    assert result["checks"]["envelope"]["result"] == "unknown"


def test_oracle_volume_unknown_for_curved_sweep():
    fixture = _load("curved-rect-sweep")
    assert fixture["expected"]["expected_volume"] is None
    receipt = _simulated_receipt(fixture)
    receipt["volume"] = 999.0
    result = assess_plan_execution(fixture["recipe"], fixture["expected"], receipt)
    assert result["checks"]["volume"]["result"] == "unknown"
    assert result["verdict"] == "reduced_scope"


def test_oracle_accepts_native_inches_via_unit_conversion():
    fixture = _load("concave-c-sweep")
    expected = dict(fixture["expected"])
    receipt = _simulated_receipt(fixture)
    factor = 1.0 / 25.4
    receipt["bbox"] = {
        "min": [value * factor for value in expected["bounds"]["min"]],
        "max": [value * factor for value in expected["bounds"]["max"]],
    }
    receipt["unit"] = "in"
    receipt["volume"] = expected["expected_volume"] * factor**3
    result = assess_plan_execution(fixture["recipe"], expected, receipt)
    assert result["checks"]["envelope"]["result"] == "pass"
    assert result["checks"]["volume"]["result"] == "pass"


def test_open_single_quad_is_not_manifold():
    result = evaluate_edge_manifold([[0, 1, 2, 3]])
    assert result["result"] == "fail"
    assert "boundary" in result["reason"]


def test_euler_rejects_open_counts():
    assert evaluate_euler(4, 4, 1)["result"] == "fail"


def test_envelope_rejects_negative_tolerance():
    fixture = _load("straight-rect-sweep")
    bounds = fixture["expected"]["bounds"]
    with pytest.raises(ValueError, match="nonnegative"):
        evaluate_envelope(bounds, bounds, tolerance_mm=-1.0)


def test_volume_rejects_unknown_unit():
    with pytest.raises(ValueError, match="unsupported length unit"):
        evaluate_volume(1.0, 1.0, planner_unit="lightyear")


def test_expected_fixture_volumes_are_exact():
    assert _load("straight-rect-sweep")["expected"]["expected_volume"] == 20000.0
    assert math.isclose(
        _load("tapered-quad-loft")["expected"]["expected_volume"],
        70000.0 / 3.0,
        rel_tol=1e-12,
    )
    assert _load("concave-c-sweep")["expected"]["expected_volume"] == 70.0


def test_assess_honors_case_volume_tolerance():
    fixture = _load("concave-c-sweep")
    expected = dict(fixture["expected"])
    assert expected["volume_tolerance"] == 2e-4
    # Measured live native value (SketchUp 2024, re-entrant caps).
    receipt = _simulated_receipt(fixture, volume=70.005537408)
    result = assess_plan_execution(fixture["recipe"], expected, receipt)
    assert result["checks"]["volume"]["result"] == "pass"
    strict = dict(expected, volume_tolerance=1e-6)
    blocked = assess_plan_execution(fixture["recipe"], strict, receipt)
    assert blocked["checks"]["volume"]["result"] == "fail"
    assert blocked["verdict"] == "blocked"


def test_deviation_vacuous_pass_for_loft_recipes():
    fixture = _load("tapered-quad-loft")
    result = assess_plan_execution(
        fixture["recipe"], fixture["expected"],
        _simulated_receipt(fixture),
    )
    assert result["checks"]["deviation"] == {
        "result": "pass",
        "reason": "no path deviation in recipe scope",
    }
    assert result["verdict"] == "pass"
