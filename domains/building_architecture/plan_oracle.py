"""Independent plan-execution oracles for Building Architecture (ENG-R03).

Wing: code | Topic: building-plan-oracle | Updated: 2026-09-17

These oracles compare an Engineer recipe (produced by
:mod:`domains.building_architecture.geometry_planner`) against an executor
read-back receipt (e.g. CDT-SketchUp ``get_entity_state``). They are pure
deterministic functions: they never call native executors and never invent
missing native evidence. A missing native fact yields ``unknown``, which
fails closed for stronger releases per the Release Scope Policy.

Scope note (Rule of Two): this module is domain-scoped to
building-architecture. Extraction into shared runtime code requires a second
implemented consumer plus migration/version evidence.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

#: Public length units accepted by the CDT-SketchUp executor, mapped to mm.
UNIT_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "ft": 304.8,
}

_EPS = 1e-9


class PlanOracleError(ValueError):
    """Raised when oracle inputs are malformed (not an engineering verdict)."""


def _unit_factor(unit: str) -> float:
    try:
        return UNIT_TO_MM[unit]
    except KeyError:
        raise PlanOracleError(f"unsupported length unit: {unit!r}") from None


def _finite(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PlanOracleError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise PlanOracleError(f"{name} must be a finite number")
    return result


def evaluate_envelope(
    recipe_bounds: Mapping[str, Sequence[float]],
    native_bbox: Mapping[str, Sequence[float]],
    *,
    planner_unit: str = "mm",
    native_unit: str = "mm",
    tolerance_mm: float = 1e-6,
) -> dict:
    """Compare recipe bounds against the native bounding box in a common unit.

    Returns ``pass`` when every axis matches within ``tolerance_mm``,
    ``fail`` on mismatch, ``unknown`` when either box is absent.
    """
    if not recipe_bounds or not native_bbox:
        return {"result": "unknown", "reason": "envelope evidence missing"}
    try:
        planner_factor = _unit_factor(planner_unit)
        native_factor = _unit_factor(native_unit)
        tolerance = _finite(tolerance_mm, "tolerance_mm")
    except PlanOracleError as exc:
        raise PlanOracleError(str(exc)) from None
    if tolerance < 0:
        raise PlanOracleError("tolerance_mm must be nonnegative")
    try:
        recipe_min = [float(value) for value in recipe_bounds["min"]]
        recipe_max = [float(value) for value in recipe_bounds["max"]]
        native_min = [float(value) for value in native_bbox["min"]]
        native_max = [float(value) for value in native_bbox["max"]]
    except (KeyError, TypeError, ValueError):
        return {"result": "unknown", "reason": "envelope evidence malformed"}
    if not (len(recipe_min) == len(recipe_max) == len(native_min) == len(native_max) == 3):
        return {"result": "unknown", "reason": "envelope evidence malformed"}
    worst = 0.0
    for axis in range(3):
        for recipe_value, native_value in (
            (recipe_min[axis], native_min[axis]),
            (recipe_max[axis], native_max[axis]),
        ):
            delta = abs(recipe_value * planner_factor - native_value * native_factor)
            worst = max(worst, delta)
            if delta > tolerance:
                return {
                    "result": "fail",
                    "reason": "envelope mismatch beyond tolerance",
                    "worst_delta_mm": worst,
                    "tolerance_mm": tolerance,
                }
    return {"result": "pass", "worst_delta_mm": worst, "tolerance_mm": tolerance}


def evaluate_counts(
    recipe: Mapping,
    native_counts: Mapping | None,
) -> dict:
    """Compare recipe vertex/face counts against native read-back counts."""
    if not native_counts:
        return {"result": "unknown", "reason": "native count evidence missing"}
    try:
        expected_vertices = int(recipe["vertex_count"])
        expected_faces = int(recipe["face_count"])
        native_vertices = int(native_counts["vertex_count"])
        native_faces = int(native_counts["face_count"])
    except (KeyError, TypeError, ValueError):
        return {"result": "unknown", "reason": "count evidence malformed"}
    mismatches = []
    if native_vertices != expected_vertices:
        mismatches.append(f"vertices {native_vertices} != {expected_vertices}")
    if native_faces != expected_faces:
        mismatches.append(f"faces {native_faces} != {expected_faces}")
    if mismatches:
        return {"result": "fail", "reason": "; ".join(mismatches)}
    return {"result": "pass"}


def evaluate_edge_manifold(faces: Sequence[Sequence[int]]) -> dict:
    """Verify recipe-internal edge manifoldness and Euler characteristic.

    Every undirected edge must be shared by exactly two faces. For a single
    closed component this implies ``V - E + F == 2``; the vertex count must be
    supplied separately via :func:`evaluate_euler` since faces alone do not
    carry isolated vertices.
    """
    if not faces:
        return {"result": "unknown", "reason": "no faces to inspect"}
    edge_uses: dict[tuple[int, int], int] = {}
    for face in faces:
        if len(face) < 3:
            return {"result": "fail", "reason": "face has fewer than 3 vertices"}
        for cursor in range(len(face)):
            edge = (face[cursor], face[(cursor + 1) % len(face)])
            key = (min(edge), max(edge))
            edge_uses[key] = edge_uses.get(key, 0) + 1
    boundary = sum(1 for uses in edge_uses.values() if uses == 1)
    non_manifold = sum(1 for uses in edge_uses.values() if uses != 2)
    if non_manifold:
        return {
            "result": "fail",
            "reason": f"{non_manifold} non-manifold edges ({boundary} boundary)",
            "edge_count": len(edge_uses),
        }
    return {"result": "pass", "edge_count": len(edge_uses)}


def evaluate_euler(vertex_count: int, edge_count: int, face_count: int) -> dict:
    """Check the closed-solid Euler characteristic ``V - E + F == 2``."""
    try:
        characteristic = int(vertex_count) - int(edge_count) + int(face_count)
    except (TypeError, ValueError):
        return {"result": "unknown", "reason": "euler evidence malformed"}
    if characteristic == 2:
        return {"result": "pass", "characteristic": characteristic}
    return {
        "result": "fail",
        "reason": f"euler characteristic {characteristic} != 2",
        "characteristic": characteristic,
    }


def evaluate_volume(
    expected_volume: float | None,
    native_volume: float | None,
    *,
    planner_unit: str = "mm",
    native_unit: str = "mm",
    relative_tolerance: float = 1e-6,
) -> dict:
    """Compare an analytically expected volume against the native volume.

    Either side missing yields ``unknown`` (fail-closed): the oracle never
    substitutes a tessellation-dependent estimate for an exact expectation.
    Curved-sweep volumes are therefore ``unknown`` by construction.
    """
    if expected_volume is None or native_volume is None:
        return {"result": "unknown", "reason": "volume evidence missing"}
    try:
        expected = _finite(expected_volume, "expected_volume")
        native = _finite(native_volume, "native_volume")
        factor = _unit_factor(native_unit) / _unit_factor(planner_unit)
        tolerance = _finite(relative_tolerance, "relative_tolerance")
    except PlanOracleError as exc:
        raise PlanOracleError(str(exc)) from None
    if expected <= 0 or native <= 0:
        return {"result": "fail", "reason": "non-positive volume"}
    native_in_planner_unit = native * factor**3
    denominator = max(abs(expected), _EPS)
    deviation = abs(native_in_planner_unit - expected) / denominator
    if deviation <= tolerance:
        return {"result": "pass", "relative_deviation": deviation}
    return {
        "result": "fail",
        "reason": "volume deviation beyond tolerance",
        "relative_deviation": deviation,
        "tolerance": tolerance,
    }


def evaluate_deviation(plan: Mapping) -> dict:
    """Re-check the recipe's declared approximation deviation gate.

    Loft recipes carry no path-deviation fields; the gate is vacuous there
    and returns ``pass`` with an explicit reason (reviewed not-applicable),
    never a silent omission. Partially present fields yield ``unknown``.
    """
    allowed_present = "max_path_deviation_allowed" in plan
    observed_present = "max_path_deviation_observed" in plan
    if not allowed_present and not observed_present:
        return {"result": "pass", "reason": "no path deviation in recipe scope"}
    if not (allowed_present and observed_present):
        return {"result": "unknown", "reason": "deviation evidence missing"}
    try:
        allowed = float(plan["max_path_deviation_allowed"])
        observed = float(plan["max_path_deviation_observed"])
    except (TypeError, ValueError):
        return {"result": "unknown", "reason": "deviation evidence malformed"}
    if observed <= allowed + _EPS:
        return {
            "result": "pass",
            "approximation_state": plan.get("approximation_state", "unknown"),
        }
    return {
        "result": "fail",
        "reason": "observed deviation exceeds allowance",
    }


def assess_plan_execution(
    recipe: Mapping,
    expected: Mapping,
    native_receipt: Mapping | None,
    *,
    tolerance_mm: float = 1e-6,
) -> dict:
    """Aggregate envelope/counts/topology/volume/deviation oracles one verdict.

    ``expected`` carries ``planner_unit`` plus an optional analytic
    ``expected_volume``. ``native_receipt`` mirrors ``get_entity_state``
    fields (``bbox``, counts, ``manifold``, ``volume``, ``unit``) and may be
    ``None`` when no native read-back exists yet.
    """
    planner_unit = expected.get("planner_unit", "mm")
    native_unit = (native_receipt or {}).get("unit", "mm")
    envelope = evaluate_envelope(
        recipe.get("bounds", {}),
        (native_receipt or {}).get("bbox", {}),
        planner_unit=planner_unit,
        native_unit=native_unit,
        tolerance_mm=tolerance_mm,
    )
    counts = evaluate_counts(recipe, native_receipt)
    manifold = evaluate_edge_manifold(recipe.get("faces", []))
    edge_count = manifold.get("edge_count")
    euler: dict = {"result": "unknown", "reason": "edge count unavailable"}
    if edge_count is not None and native_receipt is not None:
        try:
            euler = evaluate_euler(
                recipe["vertex_count"], edge_count, recipe["face_count"]
            )
        except KeyError:
            euler = {"result": "unknown", "reason": "euler evidence malformed"}
    native_manifold = (native_receipt or {}).get("manifold")
    if native_manifold is None:
        manifold_agreement: dict = {
            "result": "unknown",
            "reason": "native manifold state missing",
        }
    elif bool(native_manifold) is (manifold["result"] == "pass"):
        manifold_agreement = {"result": "pass"}
    else:
        manifold_agreement = {
            "result": "fail",
            "reason": "recipe/native manifold disagreement",
        }
    volume = evaluate_volume(
        expected.get("expected_volume"),
        (native_receipt or {}).get("volume"),
        planner_unit=planner_unit,
        native_unit=native_unit,
        relative_tolerance=expected.get("volume_tolerance", 1e-6),
    )
    deviation = evaluate_deviation(recipe)
    checks = {
        "envelope": envelope,
        "counts": counts,
        "edge_manifold": manifold,
        "euler": euler,
        "manifold_agreement": manifold_agreement,
        "volume": volume,
        "deviation": deviation,
    }
    results = [check["result"] for check in checks.values()]
    if "fail" in results:
        verdict = "blocked"
    elif "unknown" in results:
        verdict = "reduced_scope"
    else:
        verdict = "pass"
    return {"verdict": verdict, "checks": checks}
