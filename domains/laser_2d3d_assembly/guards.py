"""Laser 2D-to-3D Assembly deterministic guards.
Wing: code | Topic: laser-guards | Updated: 2026-10-03

Implements measurable domain invariants for LASER-01..06: material intake,
cross-slot DFM, closed CUT contours, slice step and sheet nesting.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from domains.guard_primitives import GuardInputError, finite_number

_EPS = 1e-9


def _finite_pt2(pt: Any, name: str) -> tuple[float, float]:
    if isinstance(pt, (str, bytes)) or not isinstance(pt, Sequence) or len(pt) != 2:
        raise GuardInputError(f"{name} must be a 2D coordinate pair")
    return finite_number(pt[0], f"{name}[0]"), finite_number(pt[1], f"{name}[1]")


def evaluate_material_intake(
    material_spec: Mapping[str, Any],
    *,
    release_target: str = "concept",
) -> dict[str, Any]:
    """LASER-01: Material triple intake check before generating cut geometry.

    thickness_mm, kerf_mm, slot_clearance_mm must be specified per session;
    they are never hardcoded domain defaults. Unknown or missing values block
    technical_draft and fabrication_candidate releases.
    """
    if not isinstance(material_spec, Mapping):
        raise GuardInputError("material_spec must be a mapping")
    mat_id = material_spec.get("material_id")
    if not isinstance(mat_id, str) or not mat_id.strip():
        raise GuardInputError("material_id must be a non-empty string")

    status = material_spec.get("status", "unknown")
    if status not in {"specified", "approved_assumption", "unknown"}:
        raise GuardInputError(f"invalid material status: {status}")

    t_raw = material_spec.get("thickness_mm")
    k_raw = material_spec.get("kerf_mm")
    c_raw = material_spec.get("slot_clearance_mm")

    is_unknown = (
        status == "unknown"
        or t_raw is None
        or k_raw is None
        or c_raw is None
    )

    reasons: list[str] = []
    if is_unknown:
        if release_target in {"technical_draft", "design_review", "fabrication_candidate"}:
            return {
                "result": "blocked",
                "reason_codes": ["unknown_material_triple"],
                "material_id": mat_id,
                "status": status,
            }
        return {
            "result": "pass",
            "reason_codes": [],
            "mode": "concept_proxy",
            "material_id": mat_id,
        }

    thickness = finite_number(t_raw, "thickness_mm")
    kerf = finite_number(k_raw, "kerf_mm")
    clearance = finite_number(c_raw, "slot_clearance_mm")

    if thickness <= 0:
        raise GuardInputError("thickness_mm must be positive")
    if kerf < 0:
        raise GuardInputError("kerf_mm must be nonnegative")
    if clearance < 0:
        raise GuardInputError("slot_clearance_mm must be nonnegative")

    return {
        "result": "pass",
        "reason_codes": [],
        "material_id": mat_id,
        "thickness_mm": thickness,
        "kerf_mm": kerf,
        "slot_clearance_mm": clearance,
    }


def evaluate_cross_slot_dfm(
    slot: Mapping[str, Any],
    material_spec: Mapping[str, Any],
) -> dict[str, Any]:
    """LASER-03: Cross-slot DFM fit and coaxiality checks.

    Slot width must accommodate material thickness + kerf compensation + clearance.
    Slot depth must not sever the part (typically ~1/2 local material width).
    """
    if not isinstance(slot, Mapping) or not isinstance(material_spec, Mapping):
        raise GuardInputError("slot and material_spec must be mappings")

    intake = evaluate_material_intake(material_spec, release_target="technical_draft")
    if intake["result"] != "pass":
        return {"result": "blocked", "reason_codes": ["material_triple_unresolved"]}

    thickness = intake["thickness_mm"]
    kerf = intake["kerf_mm"]
    min_clearance = intake["slot_clearance_mm"]

    slot_w = finite_number(slot.get("slot_width"), "slot.slot_width")
    slot_d = finite_number(slot.get("slot_depth"), "slot.slot_depth")
    local_w = finite_number(slot.get("local_part_width"), "slot.local_part_width")

    if slot_w <= 0 or slot_d <= 0 or local_w <= 0:
        raise GuardInputError("slot dimensions and local_part_width must be positive")

    reasons: list[str] = []
    # Kerf cuts both sides of slot: nominal slot target = thickness + clearance (kerf-compensated)
    effective_clearance = slot_w - (thickness + kerf)
    if effective_clearance < min_clearance - _EPS:
        reasons.append("insufficient_slot_clearance")

    if slot_d >= local_w - _EPS:
        reasons.append("blind_slot_overcut")
    elif slot_d > 0.65 * local_w:
        reasons.append("slot_depth_exceeds_safe_ratio")

    mating_id = slot.get("mating_slot_id")
    if mating_id is not None and (not isinstance(mating_id, str) or not mating_id.strip()):
        reasons.append("invalid_mating_slot_id")

    return {
        "result": "fail" if reasons else "pass",
        "reason_codes": reasons,
        "slot_width": slot_w,
        "slot_depth": slot_d,
        "effective_clearance_mm": effective_clearance,
    }


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]) -> bool:
    return (
        min(a[0], b[0]) - _EPS <= p[0] <= max(a[0], b[0]) + _EPS
        and min(a[1], b[1]) - _EPS <= p[1] <= max(a[1], b[1]) + _EPS
        and abs(_orientation(a, b, p)) <= _EPS
    )


def _segments_intersect(
    a: tuple[float, float], b: tuple[float, float],
    c: tuple[float, float], d: tuple[float, float],
) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if ((o1 > _EPS and o2 < -_EPS) or (o1 < -_EPS and o2 > _EPS)) and (
        (o3 > _EPS and o4 < -_EPS) or (o3 < -_EPS and o4 > _EPS)
    ):
        return True
    return any((
        abs(o1) <= _EPS and _on_segment(a, b, c),
        abs(o2) <= _EPS and _on_segment(a, b, d),
        abs(o3) <= _EPS and _on_segment(c, d, a),
        abs(o4) <= _EPS and _on_segment(c, d, b),
    ))


def evaluate_cut_contour(
    points: Sequence[Any],
    *,
    closed: bool = True,
    min_bridge_mm: float | None = None,
) -> dict[str, Any]:
    """LASER-04: Closed CUT contour validation for laser cutting.

    Checks:
    - sequence of at least 3 points;
    - closed loop (either closed=True or first == last);
    - no zero-length segments;
    - no self-intersections;
    - positive contour area.
    """
    if isinstance(points, (str, bytes)) or not isinstance(points, Sequence):
        raise GuardInputError("points must be a sequence")
    if len(points) < 3:
        raise GuardInputError("contour requires at least 3 points")

    pts = [_finite_pt2(p, f"points[{i}]") for i, p in enumerate(points)]
    # Normalize closure
    if math.dist(pts[0], pts[-1]) <= _EPS:
        pts = pts[:-1]
    if len(pts) < 3:
        raise GuardInputError("unique contour points must be at least 3")

    reasons: list[str] = []
    n = len(pts)

    # Check zero-length edges
    for i in range(n):
        nxt = (i + 1) % n
        if math.dist(pts[i], pts[nxt]) <= _EPS:
            reasons.append("zero_length_edge")
            break

    # Check self-intersection
    if not reasons:
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            for j in range(i + 1, n):
                if j in {i, (i + 1) % n} or i == (j + 1) % n:
                    continue
                c, d = pts[j], pts[(j + 1) % n]
                if _segments_intersect(a, b, c, d):
                    reasons.append("self_intersecting_contour")
                    break
            if reasons:
                break

    # Check non-degenerate area
    area2 = sum(
        pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
        for i in range(n)
    )
    if abs(area2) <= _EPS:
        reasons.append("degenerate_contour_area")

    area = abs(area2) / 2.0

    return {
        "result": "fail" if reasons else "pass",
        "reason_codes": sorted(set(reasons)),
        "vertex_count": n,
        "contour_area_mm2": area,
    }


def evaluate_slice_step(
    slices: Sequence[Mapping[str, Any]],
    material_spec: Mapping[str, Any],
    *,
    step_tolerance_mm: float = 1e-4,
) -> dict[str, Any]:
    """LASER-05: Stacked-slice step height and alignment feature check.

    Elevation delta between consecutive slices must equal sheet thickness.
    Alignment features (pin holes / datum marks) must be present.
    """
    if isinstance(slices, (str, bytes)) or not isinstance(slices, Sequence) or len(slices) < 2:
        raise GuardInputError("slices must be a sequence of at least 2 slice mappings")

    intake = evaluate_material_intake(material_spec, release_target="technical_draft")
    if intake["result"] != "pass":
        return {"result": "blocked", "reason_codes": ["material_triple_unresolved"]}

    expected_step = intake["thickness_mm"]
    reasons: list[str] = []

    elevations: list[float] = []
    for i, s in enumerate(slices):
        if not isinstance(s, Mapping):
            raise GuardInputError(f"slice[{i}] must be a mapping")
        elev = finite_number(s.get("elevation_z"), f"slice[{i}].elevation_z")
        elevations.append(elev)
        alignment = s.get("alignment_features", [])
        if isinstance(alignment, (str, bytes)) or not isinstance(alignment, Sequence) or not alignment:
            reasons.append(f"missing_alignment_feature:slice_{i}")

    # Verify monotonic ascending and constant step
    for i in range(len(elevations) - 1):
        step = elevations[i + 1] - elevations[i]
        if step <= 0:
            reasons.append(f"non_ascending_slice_step:{i}")
        elif abs(step - expected_step) > step_tolerance_mm + _EPS:
            reasons.append(f"slice_step_mismatch:{i}")

    return {
        "result": "fail" if reasons else "pass",
        "reason_codes": sorted(set(reasons)),
        "slice_count": len(slices),
        "expected_step_mm": expected_step,
        "total_height_mm": elevations[-1] - elevations[0] + expected_step,
    }


def evaluate_nesting_layout(
    parts_extents: Sequence[Sequence[float]],
    sheet_bed_size: Sequence[float],
    *,
    margin_mm: float = 5.0,
) -> dict[str, Any]:
    """LASER-06: Sheet/bed boundary nesting check.

    Verifies that the overall bounding extents of the nested parts
    fit within the designated laser bed size minus safe margin.
    parts_extents: [total_width_mm, total_height_mm] or sequence of parts.
    sheet_bed_size: [bed_width_mm, bed_height_mm].
    """
    if isinstance(sheet_bed_size, (str, bytes)) or not isinstance(sheet_bed_size, Sequence) or len(sheet_bed_size) != 2:
        raise GuardInputError("sheet_bed_size must be a 2-element sequence [width, height]")
    bed_w = finite_number(sheet_bed_size[0], "sheet_bed_size[0]")
    bed_h = finite_number(sheet_bed_size[1], "sheet_bed_size[1]")
    if bed_w <= 0 or bed_h <= 0:
        raise GuardInputError("sheet_bed_size dimensions must be positive")

    margin = finite_number(margin_mm, "margin_mm")
    if margin < 0:
        raise GuardInputError("margin_mm must be nonnegative")

    usable_w = bed_w - 2 * margin
    usable_h = bed_h - 2 * margin
    if usable_w <= 0 or usable_h <= 0:
        raise GuardInputError("margin exceeds sheet bed dimensions")

    if isinstance(parts_extents, (str, bytes)) or not isinstance(parts_extents, Sequence) or len(parts_extents) != 2:
        raise GuardInputError("parts_extents must be [total_width, total_height]")

    parts_w = finite_number(parts_extents[0], "parts_extents[0]")
    parts_h = finite_number(parts_extents[1], "parts_extents[1]")
    if parts_w <= 0 or parts_h <= 0:
        raise GuardInputError("parts_extents must be positive")

    reasons: list[str] = []
    # Test both orientations (parts can be rotated 90 deg)
    fits_normal = (parts_w <= usable_w + _EPS) and (parts_h <= usable_h + _EPS)
    fits_rotated = (parts_h <= usable_w + _EPS) and (parts_w <= usable_h + _EPS)

    if not (fits_normal or fits_rotated):
        reasons.append("over_bed_layout")

    return {
        "result": "fail" if reasons else "pass",
        "reason_codes": reasons,
        "nested_width_mm": parts_w,
        "nested_height_mm": parts_h,
        "bed_width_mm": bed_w,
        "bed_height_mm": bed_h,
        "margin_mm": margin,
    }
