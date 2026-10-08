"""Pre-CAD professional review gates for PlanSpec IR (ENG-R08).
Wing: code | Topic: plan-review-gates | Updated: 2026-10-06 16:10 (Asia/Ho_Chi_Minh)
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from domains.building_structural.guards import evaluate_architecture_clashes
from execution.completeness_checker import assess_inventory
from execution.planspec import validate_plan_spec

_EPS = 1e-9
_FINDING_RESULTS = {"pass", "fail", "unknown", "not_applicable"}
_SEVERITIES = {"BLOCKER", "MAJOR", "MINOR", "OBSERVATION"}
_RELEASE_TARGETS = {"concept", "technical_draft", "design_review"}
_LOW_PROVENANCE = {"inferred", "unknown"}

_DEFAULT_REQUIREMENTS: dict[str, Any] = {
    "release_target": "technical_draft",
    "dimension_tolerance": 1e-6,
    "endpoint_snap_tolerance": 1e-6,
    "grade_tolerance_percent": 0.05,
}

_REQUIREMENT_KEYS = set(_DEFAULT_REQUIREMENTS) | {
    "min_door_width",
    "min_space_area",
    "min_clear_dimension",
    "max_grade_percent",
    "min_vertical_curve_radius",
    "max_cross_slope_percent",
    "min_opening_edge_distance",
    "strict_column_grid",
    "require_layers",
    "max_features_per_chunk",
    "max_chunk_payload_bytes",
    "spatial_cell_size",
    "batch_session_id",
}


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite numeric")
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise ValueError(f"{name} must be finite numeric") from None
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite numeric")
    return number


def _normalize_requirements(requirements: Mapping[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = dict(_DEFAULT_REQUIREMENTS)
    if requirements is None:
        return merged
    if not isinstance(requirements, Mapping):
        raise ValueError("requirements must be a mapping")
    for key, value in requirements.items():
        if key not in _REQUIREMENT_KEYS:
            raise ValueError(f"unknown planning requirement: {key}")
        merged[key] = value
    release = merged.get("release_target")
    if release not in _RELEASE_TARGETS:
        raise ValueError(f"invalid release_target: {release}")
    for key in (
        "dimension_tolerance",
        "endpoint_snap_tolerance",
        "grade_tolerance_percent",
        "min_door_width",
        "min_space_area",
        "min_clear_dimension",
        "max_grade_percent",
        "min_vertical_curve_radius",
        "max_cross_slope_percent",
        "min_opening_edge_distance",
    ):
        if key in merged and merged[key] is not None:
            if _finite(merged[key], f"requirements.{key}") < 0:
                raise ValueError(f"requirements.{key} must be nonnegative")
    if (
        "strict_column_grid" in merged
        and merged["strict_column_grid"] is not None
        and not isinstance(merged["strict_column_grid"], bool)
    ):
        raise ValueError("requirements.strict_column_grid must be bool")
    if (
        "require_layers" in merged
        and merged["require_layers"] is not None
        and not isinstance(merged["require_layers"], bool)
    ):
        raise ValueError("requirements.require_layers must be bool")
    return merged


def _finding(
    finding_id: str,
    gate: str,
    severity: str,
    result: str,
    reason_codes: Sequence[str],
    feature_refs: Sequence[str] = (),
) -> dict[str, Any]:
    if severity not in _SEVERITIES:
        raise ValueError(f"invalid severity: {severity}")
    if result not in _FINDING_RESULTS:
        raise ValueError(f"invalid result: {result}")
    return {
        "finding_id": finding_id,
        "gate": gate,
        "severity": severity,
        "result": result,
        "reason_codes": list(reason_codes),
        "feature_refs": list(feature_refs),
    }


def _na(finding_id: str, gate: str) -> dict[str, Any]:
    return _finding(
        finding_id, gate, "OBSERVATION", "not_applicable", ["gate_not_applicable_for_plan_type"]
    )


def _wall_length(wall: Mapping[str, Any]) -> float:
    start = wall.get("start", [])
    end = wall.get("end", [])
    return math.hypot(end[0] - start[0], end[1] - start[1])


def _orientation(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Sequence[float], b: Sequence[float], p: Sequence[float]) -> bool:
    return (
        min(a[0], b[0]) - _EPS <= p[0] <= max(a[0], b[0]) + _EPS
        and min(a[1], b[1]) - _EPS <= p[1] <= max(a[1], b[1]) + _EPS
        and abs(_orientation(a, b, p)) <= _EPS
    )


def _segments_intersect(
    a: Sequence[float], b: Sequence[float], c: Sequence[float], d: Sequence[float]
) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if ((o1 > _EPS and o2 < -_EPS) or (o1 < -_EPS and o2 > _EPS)) and (
        (o3 > _EPS and o4 < -_EPS) or (o3 < -_EPS and o4 > _EPS)
    ):
        return True
    return any(
        (
            abs(o1) <= _EPS and _on_segment(a, b, c),
            abs(o2) <= _EPS and _on_segment(a, b, d),
            abs(o3) <= _EPS and _on_segment(c, d, a),
            abs(o4) <= _EPS and _on_segment(c, d, b),
        )
    )


def _polygon_self_intersects(pts: Sequence[Sequence[float]]) -> bool:
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 1, n):
            if j in {i, (i + 1) % n} or i == (j + 1) % n:
                continue
            c, d = pts[j], pts[(j + 1) % n]
            if _segments_intersect(a, b, c, d):
                return True
    return False


def _polygon_area(pts: Sequence[Sequence[float]]) -> float:
    n = len(pts)
    return (
        abs(
            sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
        )
        / 2.0
    )


def _rect_clear_dimension(pts: Sequence[Sequence[float]]) -> float | None:
    if len(pts) != 4:
        return None
    xs = sorted({p[0] for p in pts})
    ys = sorted({p[1] for p in pts})
    if len(xs) != 2 or len(ys) != 2:
        return None
    expected = {(xs[0], ys[0]), (xs[0], ys[1]), (xs[1], ys[0]), (xs[1], ys[1])}
    if {(p[0], p[1]) for p in pts} != expected:
        return None
    return min(xs[1] - xs[0], ys[1] - ys[0])


# ---------------------------------------------------------------- gate checks


def _gate_g0_planspec_valid(spec: Mapping[str, Any]) -> dict[str, Any]:
    result = validate_plan_spec(spec)
    if result.valid:
        return _finding("R08-G0-planspec_valid", "planspec_valid", "BLOCKER", "pass", [])
    return _finding(
        "R08-G0-planspec_valid",
        "planspec_valid",
        "BLOCKER",
        "fail",
        [f"planspec_invalid:{e}" for e in result.errors[:8]],
    )


def _gate_g1_axes(payload: Mapping[str, Any], plan_type: str) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G1-axes_datum", "axes_datum")
    axes = payload.get("axes", [])
    reasons: list[str] = []
    refs: list[str] = []
    if (payload.get("walls") or payload.get("spaces")) and not axes:
        reasons.append("missing_axes_grid")
    labels: dict[str, str] = {}
    for ax in axes:
        aid = ax.get("axis_id", "?")
        refs.append(aid)
        label = ax.get("label")
        if label in labels:
            reasons.append(f"duplicate_axis_label:{label}")
        elif label is not None:
            labels[label] = aid
        start, end = ax.get("start", []), ax.get("end", [])
        if len(start) == 2 and len(end) == 2:
            if math.hypot(end[0] - start[0], end[1] - start[1]) <= _EPS:
                reasons.append(f"degenerate_axis:{aid}")
    return _finding(
        "R08-G1-axes_datum", "axes_datum", "MAJOR", "fail" if reasons else "pass", reasons, refs
    )


def _gate_g2_dimensions(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G2-dimensional_consistency", "dimensional_consistency")
    tol = float(req["dimension_tolerance"])
    reasons: list[str] = []
    refs: list[str] = []
    for dm in payload.get("dimensions", []):
        did = dm.get("dimension_id", "?")
        refs.append(did)
        w = dm.get("witness_points", [])
        if len(w) != 2:
            reasons.append(f"dimension_witness_points_invalid:{did}")
            continue
        span = math.hypot(w[1][0] - w[0][0], w[1][1] - w[0][1])
        measured = dm.get("measured_value")
        try:
            measured_f = _finite(measured, f"dimensions.{did}.measured_value")
        except ValueError:
            reasons.append(f"dimension_measured_non_numeric:{did}")
            continue
        if abs(span - measured_f) > tol + max(_EPS, abs(measured_f) * 1e-9):
            reasons.append(f"dimension_witness_mismatch:{did}")
    return _finding(
        "R08-G2-dimensional_consistency",
        "dimensional_consistency",
        "MAJOR",
        "fail" if reasons else "pass",
        reasons,
        refs,
    )


def _gate_g3_topology(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G3-room_topology", "room_topology")
    min_area = req.get("min_space_area")
    reasons: list[str] = []
    refs: list[str] = []
    for sp in payload.get("spaces", []):
        sid = sp.get("space_id", "?")
        refs.append(sid)
        poly = sp.get("boundary_polygon", [])
        if len(poly) < 3:
            reasons.append(f"space_boundary_too_few_points:{sid}")
            continue
        if _polygon_self_intersects(poly):
            reasons.append(f"self_intersecting_boundary:{sid}")
        area = _polygon_area(poly)
        if not math.isfinite(area):
            reasons.append(f"space_area_unrepresentable:{sid}")
        elif area <= _EPS:
            reasons.append(f"degenerate_space_zero_area:{sid}")
        elif min_area is not None and area + _EPS < float(min_area):
            reasons.append(f"space_below_minimum_area:{sid}")
    return _finding(
        "R08-G3-room_topology",
        "room_topology",
        "BLOCKER",
        "fail" if reasons else "pass",
        reasons,
        refs,
    )


def _gate_g4_openings(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G4-opening_placement", "opening_placement")
    walls = {w.get("wall_id"): w for w in payload.get("walls", []) if w.get("wall_id")}
    min_door = req.get("min_door_width")
    reasons: list[str] = []
    refs: list[str] = []
    for op in payload.get("openings", []):
        oid = op.get("opening_id", "?")
        refs.append(oid)
        host_id = op.get("host_wall_id")
        host = walls.get(host_id)
        if host is None:
            reasons.append(f"unresolved_host_wall:{oid}->{host_id}")
            continue
        wall_len = _wall_length(host)
        offset = op.get("offset_along_wall", 0.0)
        width = op.get("width", 0.0)
        if offset + width > wall_len + 1e-4:
            reasons.append(f"opening_exceeds_host_wall:{oid}")
        wall_h = host.get("height")
        if (
            wall_h is not None
            and op.get("sill_height", 0.0) + width * 0 + op.get("height", 0.0) > wall_h + 1e-4
        ):
            reasons.append(f"opening_head_exceeds_wall:{oid}")
        if (
            op.get("opening_type") == "door"
            and min_door is not None
            and width + _EPS < float(min_door)
        ):
            reasons.append(f"door_below_minimum_width:{oid}")
    return _finding(
        "R08-G4-opening_placement",
        "opening_placement",
        "BLOCKER",
        "fail" if reasons else "pass",
        reasons,
        refs,
    )


def _point_on_segment(
    pt: Sequence[float], a: Sequence[float], b: Sequence[float], tol: float
) -> bool:
    cross = abs(_orientation(a, b, pt))
    seg_len = math.hypot(b[0] - a[0], b[1] - a[1])
    if seg_len <= _EPS:
        return False
    if cross / seg_len > tol:
        return False
    dot = (pt[0] - a[0]) * (b[0] - a[0]) + (pt[1] - a[1]) * (b[1] - a[1])
    return -tol <= dot <= seg_len * seg_len + tol


def _gate_g5_wall_joins(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G5-wall_joins", "wall_joins")
    snap = max(float(req["endpoint_snap_tolerance"]), 1e-6)
    walls = [w for w in payload.get("walls", []) if w.get("wall_id")]
    reasons: list[str] = []
    refs: list[str] = [w.get("wall_id", "?") for w in walls]
    endpoints: list[tuple[str, str, list[float]]] = []
    for w in walls:
        endpoints.append((w["wall_id"], "start", list(w.get("start", []))))
        endpoints.append((w["wall_id"], "end", list(w.get("end", []))))

    def _snaps(p: Sequence[float], q: Sequence[float]) -> bool:
        return math.hypot(p[0] - q[0], p[1] - q[1]) <= snap + _EPS

    # A wall is connected when any of its endpoints snaps to another wall's
    # endpoint or lies on another wall's body. Free ends of a connected
    # network (e.g. an L of two walls) are legitimate and not flagged.
    for w in walls:
        wid = w["wall_id"]
        w_ends = [list(w.get("start", [])), list(w.get("end", []))]
        connected = False
        for pt in w_ends:
            if any(other_wid != wid and _snaps(pt, q) for other_wid, _, q in endpoints):
                connected = True
                break
            for other in walls:
                if other["wall_id"] == wid:
                    continue
                if _point_on_segment(
                    pt, list(other.get("start", [])), list(other.get("end", [])), snap
                ):
                    connected = True
                    break
            if connected:
                break
        if not connected:
            reasons.append(f"orphan_wall:{wid}")
    # Unjoined tee: an endpoint landing mid-span of another wall (not at its
    # endpoint) leaves a T-junction gap/overshoot in the join model.
    for wid, end_name, pt in endpoints:
        for other in walls:
            if other["wall_id"] == wid:
                continue
            o0, o1 = list(other.get("start", [])), list(other.get("end", []))
            if _point_on_segment(pt, o0, o1, snap) and not _snaps(pt, o0) and not _snaps(pt, o1):
                reasons.append(f"unjoined_tee:{wid}:{end_name}->midspan:{other['wall_id']}")
    # Colinear overlap detection (same line, overlapping spans)
    for i in range(len(walls)):
        for j in range(i + 1, len(walls)):
            a0, a1 = walls[i].get("start", []), walls[i].get("end", [])
            b0, b1 = walls[j].get("start", []), walls[j].get("end", [])
            if len(a0) != 2 or len(a1) != 2 or len(b0) != 2 or len(b1) != 2:
                continue
            if abs(_orientation(a0, a1, b0)) <= _EPS and abs(_orientation(a0, a1, b1)) <= _EPS:
                # project onto dominant axis
                axis = 0 if abs(a1[0] - a0[0]) >= abs(a1[1] - a0[1]) else 1
                a_lo, a_hi = sorted((a0[axis], a1[axis]))
                b_lo, b_hi = sorted((b0[axis], b1[axis]))
                if max(a_lo, b_lo) < min(a_hi, b_hi) - _EPS:
                    reasons.append(f"wall_overlap:{walls[i]['wall_id']}:{walls[j]['wall_id']}")
    seen: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.append(r)
    return _finding(
        "R08-G5-wall_joins", "wall_joins", "MAJOR", "fail" if seen else "pass", seen, refs
    )


def _gate_g6_clearance(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G6-circulation_clearance", "circulation_clearance")
    min_clear = req.get("min_clear_dimension")
    if min_clear is None:
        return _finding(
            "R08-G6-circulation_clearance",
            "circulation_clearance",
            "OBSERVATION",
            "pass",
            ["clearance_requirement_not_declared"],
        )
    reasons: list[str] = []
    refs: list[str] = []
    for sp in payload.get("spaces", []):
        sid = sp.get("space_id", "?")
        refs.append(sid)
        clear = _rect_clear_dimension(sp.get("boundary_polygon", []))
        if clear is None:
            reasons.append(f"clear_dimension_method_unresolved:{sid}")
        elif clear + _EPS < float(min_clear):
            reasons.append(f"clear_dimension_below_requirement:{sid}")
    return _finding(
        "R08-G6-circulation_clearance",
        "circulation_clearance",
        "MAJOR",
        "fail" if reasons else "pass",
        reasons,
        refs,
    )


def _gate_g7_provenance(spec: Mapping[str, Any], req: Mapping[str, Any]) -> dict[str, Any]:
    ledger = spec.get("provenance_ledger", {})
    release = req.get("release_target")
    weak = sorted(
        fid
        for fid, info in ledger.items()
        if isinstance(info, Mapping) and info.get("status") in _LOW_PROVENANCE
    )
    if not weak:
        return _finding("R08-G7-provenance_quality", "provenance_quality", "BLOCKER", "pass", [])
    if release == "design_review":
        return _finding(
            "R08-G7-provenance_quality",
            "provenance_quality",
            "BLOCKER",
            "fail",
            [f"low_provenance_blocks_release:{fid}" for fid in weak],
            weak,
        )
    return _finding(
        "R08-G7-provenance_quality",
        "provenance_quality",
        "OBSERVATION",
        "pass",
        [f"low_provenance_noted:{fid}" for fid in weak],
        weak,
    )


def _gate_g8_profile(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "civil_road_profile":
        return _na("R08-G8-profile_grade", "profile_grade")
    grade_tol = float(req["grade_tolerance_percent"])
    max_grade = req.get("max_grade_percent")
    min_radius = req.get("min_vertical_curve_radius")
    reasons: list[str] = []
    grade_line = payload.get("grade_line", [])
    for idx in range(len(grade_line) - 1):
        a, b = grade_line[idx], grade_line[idx + 1]
        run = b.get("station", 0.0) - a.get("station", 0.0)
        if run <= _EPS:
            reasons.append(f"grade_segment_non_positive_run:{idx}")
            continue
        computed = (b.get("elevation", 0.0) - a.get("elevation", 0.0)) / run * 100.0
        for decl_key in ("grade_out_percent",):
            declared = a.get(decl_key)
            if declared is not None and abs(float(declared) - computed) > grade_tol + 1e-9:
                reasons.append(
                    f"grade_declaration_mismatch:segment_{idx}({declared}%vs{computed:.3f}%)"
                )
        if max_grade is not None and abs(computed) > float(max_grade) + 1e-9:
            reasons.append(f"grade_exceeds_maximum:segment_{idx}({computed:.3f}%)")
    for idx, pvi in enumerate(grade_line):
        radius = pvi.get("curve_radius")
        if (
            radius is not None
            and min_radius is not None
            and float(radius) + _EPS < float(min_radius)
        ):
            reasons.append(f"vertical_curve_below_minimum_radius:pvi_{idx}")
    return _finding(
        "R08-G8-profile_grade",
        "profile_grade",
        "MAJOR",
        "fail" if reasons else "pass",
        reasons,
        [f"pvi_{i}" for i in range(len(grade_line))],
    )


def _gate_g9_cross_section(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "civil_road_cross_section":
        return _na("R08-G9-cross_section", "cross_section")
    max_slope = req.get("max_cross_slope_percent")
    reasons: list[str] = []
    minor: list[str] = []
    layers = payload.get("pavement_structure", [])
    orders = [ly.get("order") for ly in layers]
    if orders != sorted(orders) or sorted(orders) != list(range(1, len(orders) + 1)):
        reasons.append(f"pavement_order_not_sequential:{orders}")
    cw = payload.get("carriageway", {})
    for key in ("cross_slope_left_percent", "cross_slope_right_percent"):
        slope = cw.get(key)
        if (
            slope is not None
            and max_slope is not None
            and abs(float(slope)) > float(max_slope) + 1e-9
        ):
            reasons.append(f"cross_slope_exceeds_maximum:{key}({slope}%)")
    for side_key in ("left", "right"):
        side = (payload.get("side_slopes") or {}).get(side_key)
        if isinstance(side, Mapping) and side.get("is_cut") is True and not side.get("ditch"):
            minor.append(f"missing_ditch_in_cut:{side_key}")
    finding = _finding(
        "R08-G9-cross_section",
        "cross_section",
        "MAJOR",
        "fail" if reasons else "pass",
        reasons,
        [ly.get("layer_id", f"layer_{i}") for i, ly in enumerate(layers)],
    )
    if minor and not reasons:
        return _finding(
            "R08-G9-cross_section", "cross_section", "MINOR", "pass", minor, finding["feature_refs"]
        )
    finding["reason_codes"] = reasons + [f"minor:{m}" for m in minor]
    if reasons:
        return finding
    if minor:
        return _finding(
            "R08-G9-cross_section", "cross_section", "MINOR", "pass", minor, finding["feature_refs"]
        )
    return finding


def _point_segment_distance(pt: Sequence[float], a: Sequence[float], b: Sequence[float]) -> float:
    abx, aby = b[0] - a[0], b[1] - a[1]
    seg_len_sq = abx * abx + aby * aby
    if seg_len_sq <= _EPS * _EPS:
        return math.hypot(pt[0] - a[0], pt[1] - a[1])
    t = max(0.0, min(1.0, ((pt[0] - a[0]) * abx + (pt[1] - a[1]) * aby) / seg_len_sq))
    return math.hypot(pt[0] - (a[0] + t * abx), pt[1] - (a[1] + t * aby))


def _segments_cross(
    a0: Sequence[float], a1: Sequence[float], b0: Sequence[float], b1: Sequence[float]
) -> list[float] | None:
    dx_a, dy_a = a1[0] - a0[0], a1[1] - a0[1]
    dx_b, dy_b = b1[0] - b0[0], b1[1] - b0[1]
    denom = dx_a * dy_b - dy_a * dx_b
    if abs(denom) <= _EPS:
        return None
    t = ((b0[0] - a0[0]) * dy_b - (b0[1] - a0[1]) * dx_b) / denom
    u = ((b0[0] - a0[0]) * dy_a - (b0[1] - a0[1]) * dx_a) / denom
    if -_EPS <= t <= 1.0 + _EPS and -_EPS <= u <= 1.0 + _EPS:
        return [a0[0] + t * dx_a, a0[1] + t * dy_a]
    return None


def _point_in_polygon(pt: Sequence[float], poly: Sequence[Sequence[float]]) -> bool:
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > pt[1]) != (b[1] > pt[1]):
            xinters = (b[0] - a[0]) * (pt[1] - a[1]) / (b[1] - a[1]) + a[0]
            if pt[0] < xinters:
                inside = not inside
    return inside


def _column_bbox(column: Mapping[str, Any]) -> tuple[float, float, float, float] | None:
    center = column.get("center", [])
    dims = column.get("dimensions", [])
    if len(center) != 2 or not dims:
        return None
    try:
        cx, cy = _finite(center[0], "column.x"), _finite(center[1], "column.y")
    except ValueError:
        return None
    if column.get("shape") == "circle":
        try:
            r = _finite(dims[0], "column.diameter") / 2.0
        except ValueError:
            return None
        return (cx - r, cy - r, cx + r, cy + r)
    if len(dims) < 2:
        return None
    try:
        hw, hh = _finite(dims[0], "column.w") / 2.0, _finite(dims[1], "column.h") / 2.0
    except ValueError:
        return None
    return (cx - hw, cy - hh, cx + hw, cy + hh)


def _gate_g10_columns(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G10-column_placement", "column_placement")
    snap = max(float(req["endpoint_snap_tolerance"]), 1e-6)
    strict = bool(req.get("strict_column_grid", False))
    axes = [(ax.get("start", []), ax.get("end", [])) for ax in payload.get("axes", [])]
    axes = [(a, b) for a, b in axes if len(a) == 2 and len(b) == 2]
    intersections: list[list[float]] = []
    for i in range(len(axes)):
        for j in range(i + 1, len(axes)):
            hit = _segments_cross(axes[i][0], axes[i][1], axes[j][0], axes[j][1])
            if hit is not None:
                intersections.append(hit)
    columns = [c for c in payload.get("columns", []) if c.get("column_id")]
    columns_by_id = {c["column_id"]: c for c in columns}
    reasons: list[str] = []
    refs: list[str] = []
    boxes: list[tuple[str, tuple[float, float, float, float]]] = []
    for col in columns:
        cid = col.get("column_id", "?")
        refs.append(cid)
        center = col.get("center", [])
        if len(center) != 2:
            reasons.append(f"column_center_invalid:{cid}")
            continue
        on_axis = any(_point_segment_distance(center, a, b) <= snap + _EPS for a, b in axes)
        if not on_axis:
            reasons.append(f"column_off_grid:{cid}")
            continue
        if (
            strict
            and intersections
            and not any(
                math.hypot(center[0] - p[0], center[1] - p[1]) <= snap + _EPS for p in intersections
            )
        ):
            reasons.append(f"column_off_intersection:{cid}")
        box = _column_bbox(col)
        if box is None:
            reasons.append(f"column_bbox_unresolvable:{cid}")
        else:
            boxes.append((cid, box))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            if (
                a[0] < b[2] - _EPS
                and b[0] < a[2] - _EPS
                and a[1] < b[3] - _EPS
                and b[1] < a[3] - _EPS
            ) and _column_shapes_overlap(
                columns_by_id[boxes[i][0]],
                columns_by_id[boxes[j][0]],
            ):
                reasons.append(f"column_overlap:{boxes[i][0]}:{boxes[j][0]}")
    return _finding(
        "R08-G10-column_placement",
        "column_placement",
        "MAJOR",
        "fail" if reasons else "pass",
        reasons,
        refs,
    )


def _gate_g11_opening_clearances(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G11-opening_clearances", "opening_clearances")
    min_edge = req.get("min_opening_edge_distance")
    walls = {w.get("wall_id"): w for w in payload.get("walls", []) if w.get("wall_id")}
    reasons: list[str] = []
    refs: list[str] = []
    spans: dict[str, list[tuple[str, float, float]]] = {}
    for op in payload.get("openings", []):
        oid = op.get("opening_id", "?")
        refs.append(oid)
        host = walls.get(op.get("host_wall_id"))
        if host is None:
            continue  # unresolved host already fails G4
        wall_len = _wall_length(host)
        offset = op.get("offset_along_wall", 0.0)
        width = op.get("width", 0.0)
        if min_edge is not None:
            near = min(offset, wall_len - (offset + width))
            if near + _EPS < float(min_edge):
                reasons.append(f"opening_too_close_to_wall_end:{oid}")
        spans.setdefault(op.get("host_wall_id"), []).append((oid, offset, offset + width))
    for host_id, intervals in spans.items():
        ordered = sorted(intervals, key=lambda t: t[1])
        for (a_id, _a0, a1), (b_id, b0, _b1) in zip(ordered, ordered[1:], strict=False):
            if b0 < a1 - _EPS:
                reasons.append(f"opening_overlap:{a_id}:{b_id}@wall_{host_id}")
    seen: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.append(r)
    return _finding(
        "R08-G11-opening_clearances",
        "opening_clearances",
        "BLOCKER",
        "fail" if seen else "pass",
        seen,
        refs,
    )


def _gate_g12_fixture_containment(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any], angle_unit: str = "deg"
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G12-fixture_containment", "fixture_containment")
    spaces = {sp.get("space_id"): sp for sp in payload.get("spaces", []) if sp.get("space_id")}
    reasons: list[str] = []
    refs: list[str] = []
    for fx in payload.get("fixtures", []):
        fid = fx.get("fixture_id", "?")
        refs.append(fid)
        host_id = fx.get("host_space_id")
        if not host_id:
            reasons.append(f"fixture_host_space_missing:{fid}")
            continue
        space = spaces.get(host_id)
        if space is None:
            reasons.append(f"fixture_host_space_unresolved:{fid}->{host_id}")
            continue
        poly = space.get("boundary_polygon", [])
        pos = fx.get("position", [])
        if len(poly) < 3 or len(pos) != 2 or _polygon_self_intersects(poly):
            reasons.append(f"fixture_containment_unverifiable:{fid}")
            continue
        if not _inside_or_boundary(pos, poly):
            reasons.append(f"fixture_outside_host_space:{fid}->{host_id}")
            continue
        dims = fx.get("dimensions")
        if dims is None:
            reasons.append(f"fixture_envelope_unknown:{fid}")
            continue
        width = _finite(dims[0], f"fixtures.{fid}.width")
        depth = _finite(dims[1], f"fixtures.{fid}.depth")
        angle = _finite(fx.get("rotation", 0.0), f"fixtures.{fid}.rotation")
        if angle_unit == "deg":
            angle = math.radians(angle)
        footprint = _rectangle(pos, width, depth, angle)
        if not _footprint_contained(footprint, poly):
            reasons.append(f"fixture_envelope_outside_host_space:{fid}->{host_id}")
    return _finding(
        "R08-G12-fixture_containment",
        "fixture_containment",
        "MAJOR",
        "fail" if reasons else "pass",
        reasons,
        refs,
    )


def _rectangle(center, width, depth, angle=0.0):
    cs, sn = math.cos(angle), math.sin(angle)
    return [
        (center[0] + x * cs - y * sn, center[1] + x * sn + y * cs)
        for x, y in (
            (-width / 2, -depth / 2),
            (width / 2, -depth / 2),
            (width / 2, depth / 2),
            (-width / 2, depth / 2),
        )
    ]


def _polygon_bounds(points):
    return (
        min(p[0] for p in points),
        min(p[1] for p in points),
        max(p[0] for p in points),
        max(p[1] for p in points),
    )


def _circle_polygon_overlap(center, radius, polygon):
    return _inside_or_boundary(center, polygon) or any(
        _point_segment_distance(center, point, polygon[(i + 1) % len(polygon)]) < radius - _EPS
        for i, point in enumerate(polygon)
    )


def _column_shapes_overlap(a, b):
    if a["shape"] == "circle" and b["shape"] == "circle":
        return math.hypot(a["center"][0] - b["center"][0], a["center"][1] - b["center"][1]) < (
            (a["dimensions"][0] + b["dimensions"][0]) / 2 - _EPS
        )
    if a["shape"] == "circle":
        return _circle_polygon_overlap(
            a["center"], a["dimensions"][0] / 2, _rectangle(b["center"], *b["dimensions"])
        )
    if b["shape"] == "circle":
        return _column_shapes_overlap(b, a)
    return _convex_overlap(
        _rectangle(a["center"], *a["dimensions"]), _rectangle(b["center"], *b["dimensions"])
    )


def _convex_overlap(a, b):
    """Separating-axis narrow phase; touching boundaries do not overlap."""
    for polygon in (a, b):
        for i, p in enumerate(polygon):
            q = polygon[(i + 1) % len(polygon)]
            nx, ny = -(q[1] - p[1]), q[0] - p[0]
            length = math.hypot(nx, ny)
            nx, ny = nx / length, ny / length
            ap = [v[0] * nx + v[1] * ny for v in a]
            bp = [v[0] * nx + v[1] * ny for v in b]
            if min(max(ap), max(bp)) <= max(min(ap), min(bp)) + _EPS:
                return False
    return True


def _gate_g15_clashes(payload, plan_type, angle_unit):
    if plan_type != "architectural_floor_plan":
        return _na("R08-G15-spatial_clashes", "spatial_clashes")
    reasons, refs = [], []
    walls = {w["wall_id"]: w for w in payload.get("walls", [])}
    columns = payload.get("columns", [])
    for opening in payload.get("openings", []):
        host = walls.get(opening["host_wall_id"])
        if host is None:
            continue  # G4 already blocks unresolved hosting.
        if not columns:
            continue
        oid = opening["opening_id"]
        if host["baseline"] != "center":
            reasons.append(f"opening_clash_frame_unresolved:{oid}")
            continue
        start, end = host["start"], host["end"]
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        distance = opening["offset_along_wall"] + opening["width"] / 2
        center = (start[0] + distance * math.cos(angle), start[1] + distance * math.sin(angle))
        band = _rectangle(center, opening["width"], host["thickness"], angle)
        for column in columns:
            cid = column["column_id"]
            bounds = _column_bbox(column)
            if bounds is None:
                continue  # G10 blocks unresolvable geometry.
            broad = evaluate_architecture_clashes(
                columns=[{"id": cid, "bounds": bounds}],
                openings=[{"id": oid, "bounds": _polygon_bounds(band)}],
            )
            if broad["result"] == "pass":
                continue
            if column["shape"] == "circle":
                c, radius = column["center"], column["dimensions"][0] / 2
                overlap = _circle_polygon_overlap(c, radius, band)
            else:
                overlap = _convex_overlap(band, _rectangle(column["center"], *column["dimensions"]))
            if overlap:
                reasons.append(f"column_opening_clash:{cid}:{oid}")
                refs.extend((cid, oid))
    fixtures = []
    for fixture in payload.get("fixtures", []):
        dims = fixture.get("dimensions")
        if dims is None:
            continue  # G12 blocks missing envelopes.
        angle = fixture.get("rotation", 0.0)
        if angle_unit == "deg":
            angle = math.radians(angle)
        fixtures.append((fixture["fixture_id"], _rectangle(fixture["position"], *dims, angle)))
    for i, (aid, a) in enumerate(fixtures):
        for bid, b in fixtures[i + 1 :]:
            if _convex_overlap(a, b):
                reasons.append(f"fixture_overlap:{aid}:{bid}")
                refs.extend((aid, bid))
    return _finding(
        "R08-G15-spatial_clashes",
        "spatial_clashes",
        "BLOCKER",
        "fail" if reasons else "pass",
        reasons,
        list(dict.fromkeys(refs)),
    )


_LAYER_KINDS = (
    ("axes", "axis_id"),
    ("walls", "wall_id"),
    ("columns", "column_id"),
    ("openings", "opening_id"),
    ("spaces", "space_id"),
    ("fixtures", "fixture_id"),
    ("dimensions", "dimension_id"),
)


def _gate_g13_layers(
    payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]
) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G13-layer_discipline", "layer_discipline")
    if not req.get("require_layers", False):
        return _finding(
            "R08-G13-layer_discipline",
            "layer_discipline",
            "OBSERVATION",
            "pass",
            ["layer_discipline_not_required"],
        )
    reasons: list[str] = []
    refs: list[str] = []
    kind_layers: dict[str, set[str]] = {}
    for key, id_key in _LAYER_KINDS:
        for item in payload.get(key, []) or []:
            if not isinstance(item, Mapping):
                continue
            fid = item.get(id_key, "?")
            refs.append(fid)
            layer = item.get("layer")
            if not isinstance(layer, str) or not layer:
                reasons.append(f"missing_layer:{fid}")
            else:
                kind_layers.setdefault(key, set()).add(layer)
    for kind in sorted(kind_layers):
        if len(kind_layers[kind]) > 1:
            reasons.append(f"split_layer:{kind}:{sorted(kind_layers[kind])}")
    seen: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.append(r)
    return _finding(
        "R08-G13-layer_discipline",
        "layer_discipline",
        "MAJOR",
        "fail" if seen else "pass",
        seen,
        refs,
    )


_SOURCE_FAMILIES = {
    "axes": ("axes", "axis_id", None),
    "walls": ("walls", "wall_id", None),
    "bearing_walls": ("walls", "wall_id", ("wall_type", "bearing")),
    "partition_walls": ("walls", "wall_id", ("wall_type", "partition")),
    "columns": ("columns", "column_id", None),
    "doors": ("openings", "opening_id", ("opening_type", "door")),
    "windows": ("openings", "opening_id", ("opening_type", "window")),
    "spaces": ("spaces", "space_id", None),
    "fixtures": ("fixtures", "fixture_id", None),
    "dimensions": ("dimensions", "dimension_id", None),
}


def _gate_g14_source_inventory(spec: Mapping[str, Any], req: Mapping[str, Any]) -> dict[str, Any]:
    """Check planned coverage against independently frozen source requirements.

    The completeness adapter below checks PlanSpec presence only. It is NOT
    native implementation/verification evidence and never releases an artifact.
    """
    if spec.get("plan_type") != "architectural_floor_plan":
        return _na("R08-G14-source_completeness", "source_completeness")
    payload = spec.get("payload", {})
    reasons: list[str] = []
    if not payload.get("walls") or not payload.get("spaces"):
        reasons.append("floor_plan_requires_walls_and_spaces")
    inventory = spec.get("source_inventory")
    if inventory is None:
        reasons.append("source_inventory_missing")
        return _finding(
            "R08-G14-source_completeness",
            "source_completeness",
            "BLOCKER",
            "fail" if reasons else "pass",
            reasons,
        )

    if inventory["source_type"] == "image" and inventory["review_passes"] != [
        "context",
        "detail",
        "confirmation",
    ]:
        reasons.append("image_review_passes_incomplete_or_unordered")
    items = inventory["items"]
    if not items:
        reasons.append("source_inventory_empty")
    family_ids = {
        family: {
            v[id_key]
            for v in payload.get(key, [])
            if selector is None or v.get(selector[0]) == selector[1]
        }
        for family, (key, id_key, selector) in _SOURCE_FAMILIES.items()
    }
    payload_ids = [v[id_key] for key, id_key in _LAYER_KINDS for v in payload.get(key, [])]
    if len(payload_ids) != len(set(payload_ids)):
        reasons.append("duplicate_plan_feature_id")
    represented = set()
    seen = set()
    coverage = []
    accounted_refs = {family: set() for family in _SOURCE_FAMILIES}
    refs = []
    for item in items:
        iid = item["item_id"]
        if iid in seen:
            reasons.append(f"duplicate_source_item_id:{iid}")
            continue
        seen.add(iid)
        family = item["semantic_family"]
        represented.add(family)
        expected = item["feature_refs"]
        refs.extend(expected)
        known_evidence = item["evidence_state"] not in _LOW_PROVENANCE
        evidence = item.get("source_evidence", [])
        if not evidence:
            reasons.append(f"source_item_evidence_missing:{iid}")
        if not known_evidence:
            reasons.append(f"source_item_unresolved:{iid}")
        if family not in family_ids:
            reasons.append(f"source_family_unsupported:{family}")
        available = family_ids.get(family, set())
        if not item["required"]:
            if not item.get("exclusion_reason") or not item.get("reviewed_by"):
                reasons.append(f"source_exclusion_unreviewed:{iid}")
            if expected or available:
                reasons.append(f"source_exclusion_contradicts_plan:{iid}")
            continue
        if family in accounted_refs:
            accounted_refs[family].update(expected)
        if not expected:
            reasons.append(f"source_required_refs_missing:{iid}")
        for fid in expected:
            if fid not in available:
                reasons.append(f"source_feature_missing_or_wrong_family:{iid}:{fid}")
        coverage.append(
            {
                "item_id": iid,
                "required": True,
                "implementation_state": "implemented"
                if expected and set(expected) <= available
                else "missing",
                "verification_state": "verified" if evidence and known_evidence else "unverified",
            }
        )
    for family in sorted(set(_SOURCE_FAMILIES) - represented):
        reasons.append(f"source_family_unaccounted:{family}")
    for family in sorted(family_ids):
        for fid in sorted(family_ids[family] - accounted_refs[family]):
            reasons.append(f"plan_feature_not_in_source_inventory:{family}:{fid}")
    if not coverage:
        reasons.append("source_inventory_no_required_items")
    reasons.extend(assess_inventory(coverage)["reason_codes"])
    return _finding(
        "R08-G14-source_completeness",
        "source_completeness",
        "BLOCKER",
        "fail" if reasons else "pass",
        reasons,
        refs,
    )


def _inside_or_boundary(pt: Sequence[float], polygon: Sequence[Sequence[float]]) -> bool:
    return _point_in_polygon(pt, polygon) or any(
        _point_on_segment(pt, a, polygon[(i + 1) % len(polygon)], _EPS)
        for i, a in enumerate(polygon)
    )


def _footprint_contained(
    footprint: Sequence[Sequence[float]], polygon: Sequence[Sequence[float]]
) -> bool:
    """Check edge intervals as well as vertices; concave notches cannot be bridged."""
    if not all(_inside_or_boundary(pt, polygon) for pt in footprint):
        return False
    for i, a in enumerate(footprint):
        b = footprint[(i + 1) % len(footprint)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        span2 = dx * dx + dy * dy
        if span2 <= _EPS * _EPS:
            return False
        cuts = {0.0, 1.0}
        for j, c in enumerate(polygon):
            d = polygon[(j + 1) % len(polygon)]
            ex, ey = d[0] - c[0], d[1] - c[1]
            denominator = dx * ey - dy * ex
            if abs(denominator) > _EPS:
                t = ((c[0] - a[0]) * ey - (c[1] - a[1]) * ex) / denominator
                u = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / denominator
                if -_EPS <= t <= 1 + _EPS and -_EPS <= u <= 1 + _EPS:
                    cuts.add(max(0.0, min(1.0, t)))
            else:
                for pt in (c, d):
                    if _point_on_segment(pt, a, b, _EPS):
                        cuts.add(
                            max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / span2))
                        )
        ordered = sorted(cuts)
        for left, right in zip(ordered, ordered[1:], strict=False):
            t = (left + right) / 2
            if not _inside_or_boundary((a[0] + t * dx, a[1] + t * dy), polygon):
                return False
    return True


@dataclass(frozen=True)
class PlanReviewResult:
    approved: bool
    verdict: str  # "APPROVED_FOR_EXECUTION" | "REJECTED"
    findings: list[Any] = field(default_factory=list)
    blocked_gates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "verdict": self.verdict,
            "findings": [dict(f) for f in self.findings],
            "blocked_gates": list(self.blocked_gates),
        }


def review_plan_spec(
    spec: Mapping[str, Any], requirements: Mapping[str, Any] | None = None
) -> PlanReviewResult:
    """Run deterministic pre-CAD professional review gates over a PlanSpec IR mapping."""
    if not isinstance(spec, Mapping):
        raise ValueError("spec must be a mapping")
    req = _normalize_requirements(requirements)
    findings: list[dict[str, Any]] = []

    g0 = _gate_g0_planspec_valid(spec)
    findings.append(g0)
    if g0["result"] != "pass":
        return PlanReviewResult(
            approved=False, verdict="REJECTED", findings=findings, blocked_gates=["planspec_valid"]
        )

    plan_type = spec.get("plan_type")
    payload = spec.get("payload", {})
    findings.append(_gate_g1_axes(payload, plan_type))
    findings.append(_gate_g2_dimensions(payload, plan_type, req))
    findings.append(_gate_g3_topology(payload, plan_type, req))
    findings.append(_gate_g4_openings(payload, plan_type, req))
    findings.append(_gate_g5_wall_joins(payload, plan_type, req))
    findings.append(_gate_g6_clearance(payload, plan_type, req))
    findings.append(_gate_g7_provenance(spec, req))
    findings.append(_gate_g8_profile(payload, plan_type, req))
    findings.append(_gate_g9_cross_section(payload, plan_type, req))
    findings.append(_gate_g10_columns(payload, plan_type, req))
    findings.append(_gate_g11_opening_clearances(payload, plan_type, req))
    findings.append(_gate_g12_fixture_containment(payload, plan_type, req, spec["units"]["angle"]))
    findings.append(_gate_g13_layers(payload, plan_type, req))
    findings.append(_gate_g14_source_inventory(spec, req))
    findings.append(_gate_g15_clashes(payload, plan_type, spec["units"]["angle"]))

    blocked: list[str] = []
    for f in findings:
        if f["severity"] in ("BLOCKER", "MAJOR") and f["result"] in ("fail", "unknown"):
            blocked.append(f["gate"])
    approved = not blocked
    return PlanReviewResult(
        approved=approved,
        verdict="APPROVED_FOR_EXECUTION" if approved else "REJECTED",
        findings=findings,
        blocked_gates=blocked,
    )
