"""Pre-CAD professional review gates for PlanSpec IR (ENG-R08).
Wing: code | Topic: plan-review-gates | Updated: 2026-09-18 00:10
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

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


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric")
    return float(value)


def _normalize_requirements(requirements: Mapping[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = dict(_DEFAULT_REQUIREMENTS)
    if requirements is None:
        return merged
    if not isinstance(requirements, Mapping):
        raise ValueError("requirements must be a mapping")
    for key, value in requirements.items():
        merged[key] = value
    release = merged.get("release_target")
    if release not in _RELEASE_TARGETS:
        raise ValueError(f"invalid release_target: {release}")
    for key in ("dimension_tolerance", "endpoint_snap_tolerance", "grade_tolerance_percent",
                "min_door_width", "min_space_area", "min_clear_dimension",
                "max_grade_percent", "min_vertical_curve_radius", "max_cross_slope_percent"):
        if key in merged and merged[key] is not None:
            _finite(merged[key], f"requirements.{key}")
    return merged


def _finding(finding_id: str, gate: str, severity: str, result: str,
             reason_codes: Sequence[str], feature_refs: Sequence[str] = ()) -> dict[str, Any]:
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
    return _finding(finding_id, gate, "OBSERVATION", "not_applicable", ["gate_not_applicable_for_plan_type"])


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


def _segments_intersect(a: Sequence[float], b: Sequence[float],
                        c: Sequence[float], d: Sequence[float]) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if ((o1 > _EPS and o2 < -_EPS) or (o1 < -_EPS and o2 > _EPS)) and \
       ((o3 > _EPS and o4 < -_EPS) or (o3 < -_EPS and o4 > _EPS)):
        return True
    return any((
        abs(o1) <= _EPS and _on_segment(a, b, c),
        abs(o2) <= _EPS and _on_segment(a, b, d),
        abs(o3) <= _EPS and _on_segment(c, d, a),
        abs(o4) <= _EPS and _on_segment(c, d, b),
    ))


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
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))) / 2.0


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
    return _finding("R08-G0-planspec_valid", "planspec_valid", "BLOCKER", "fail",
                    [f"planspec_invalid:{e}" for e in result.errors[:8]])


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
    return _finding("R08-G1-axes_datum", "axes_datum", "MAJOR",
                    "fail" if reasons else "pass", reasons, refs)


def _gate_g2_dimensions(payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]) -> dict[str, Any]:
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
    return _finding("R08-G2-dimensional_consistency", "dimensional_consistency", "MAJOR",
                    "fail" if reasons else "pass", reasons, refs)


def _gate_g3_topology(payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]) -> dict[str, Any]:
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
        if area <= _EPS:
            reasons.append(f"degenerate_space_zero_area:{sid}")
        elif min_area is not None and area + _EPS < float(min_area):
            reasons.append(f"space_below_minimum_area:{sid}")
    return _finding("R08-G3-room_topology", "room_topology", "BLOCKER",
                    "fail" if reasons else "pass", reasons, refs)


def _gate_g4_openings(payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]) -> dict[str, Any]:
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
        if wall_h is not None and op.get("sill_height", 0.0) + width * 0 + op.get("height", 0.0) > wall_h + 1e-4:
            reasons.append(f"opening_head_exceeds_wall:{oid}")
        if op.get("opening_type") == "door" and min_door is not None and width + _EPS < float(min_door):
            reasons.append(f"door_below_minimum_width:{oid}")
    return _finding("R08-G4-opening_placement", "opening_placement", "BLOCKER",
                    "fail" if reasons else "pass", reasons, refs)


def _point_on_segment(pt: Sequence[float], a: Sequence[float], b: Sequence[float], tol: float) -> bool:
    cross = abs(_orientation(a, b, pt))
    seg_len = math.hypot(b[0] - a[0], b[1] - a[1])
    if seg_len <= _EPS:
        return False
    if cross / seg_len > tol:
        return False
    dot = (pt[0] - a[0]) * (b[0] - a[0]) + (pt[1] - a[1]) * (b[1] - a[1])
    return -tol <= dot <= seg_len * seg_len + tol


def _gate_g5_wall_joins(payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]) -> dict[str, Any]:
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
                if _point_on_segment(pt, list(other.get("start", [])), list(other.get("end", [])), snap):
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
    return _finding("R08-G5-wall_joins", "wall_joins", "MAJOR",
                    "fail" if seen else "pass", seen, refs)


def _gate_g6_clearance(payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]) -> dict[str, Any]:
    if plan_type != "architectural_floor_plan":
        return _na("R08-G6-circulation_clearance", "circulation_clearance")
    min_clear = req.get("min_clear_dimension")
    if min_clear is None:
        return _finding("R08-G6-circulation_clearance", "circulation_clearance",
                        "OBSERVATION", "pass", ["clearance_requirement_not_declared"])
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
    return _finding("R08-G6-circulation_clearance", "circulation_clearance", "MAJOR",
                    "fail" if reasons else "pass", reasons, refs)


def _gate_g7_provenance(spec: Mapping[str, Any], req: Mapping[str, Any]) -> dict[str, Any]:
    ledger = spec.get("provenance_ledger", {})
    release = req.get("release_target")
    weak = sorted(fid for fid, info in ledger.items()
                  if isinstance(info, Mapping) and info.get("status") in _LOW_PROVENANCE)
    if not weak:
        return _finding("R08-G7-provenance_quality", "provenance_quality",
                        "BLOCKER", "pass", [])
    if release == "design_review":
        return _finding("R08-G7-provenance_quality", "provenance_quality", "BLOCKER", "fail",
                        [f"low_provenance_blocks_release:{fid}" for fid in weak], weak)
    return _finding("R08-G7-provenance_quality", "provenance_quality", "OBSERVATION", "pass",
                    [f"low_provenance_noted:{fid}" for fid in weak], weak)


def _gate_g8_profile(payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]) -> dict[str, Any]:
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
                reasons.append(f"grade_declaration_mismatch:segment_{idx}({declared}%vs{computed:.3f}%)")
        if max_grade is not None and abs(computed) > float(max_grade) + 1e-9:
            reasons.append(f"grade_exceeds_maximum:segment_{idx}({computed:.3f}%)")
    for idx, pvi in enumerate(grade_line):
        radius = pvi.get("curve_radius")
        if radius is not None and min_radius is not None and float(radius) + _EPS < float(min_radius):
            reasons.append(f"vertical_curve_below_minimum_radius:pvi_{idx}")
    return _finding("R08-G8-profile_grade", "profile_grade", "MAJOR",
                    "fail" if reasons else "pass", reasons,
                    [f"pvi_{i}" for i in range(len(grade_line))])


def _gate_g9_cross_section(payload: Mapping[str, Any], plan_type: str, req: Mapping[str, Any]) -> dict[str, Any]:
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
        if slope is not None and max_slope is not None and abs(float(slope)) > float(max_slope) + 1e-9:
            reasons.append(f"cross_slope_exceeds_maximum:{key}({slope}%)")
    for side_key in ("left", "right"):
        side = (payload.get("side_slopes") or {}).get(side_key)
        if isinstance(side, Mapping) and side.get("is_cut") is True and not side.get("ditch"):
            minor.append(f"missing_ditch_in_cut:{side_key}")
    finding = _finding("R08-G9-cross_section", "cross_section", "MAJOR",
                       "fail" if reasons else "pass", reasons,
                       [ly.get("layer_id", f"layer_{i}") for i, ly in enumerate(layers)])
    if minor and not reasons:
        return _finding("R08-G9-cross_section", "cross_section", "MINOR", "pass", minor, finding["feature_refs"])
    finding["reason_codes"] = reasons + [f"minor:{m}" for m in minor]
    if reasons:
        return finding
    if minor:
        return _finding("R08-G9-cross_section", "cross_section", "MINOR", "pass", minor, finding["feature_refs"])
    return finding


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


def review_plan_spec(spec: Mapping[str, Any], requirements: Mapping[str, Any] | None = None) -> PlanReviewResult:
    """Run deterministic pre-CAD professional review gates over a PlanSpec IR mapping."""
    if not isinstance(spec, Mapping):
        raise ValueError("spec must be a mapping")
    req = _normalize_requirements(requirements)
    findings: list[dict[str, Any]] = []

    g0 = _gate_g0_planspec_valid(spec)
    findings.append(g0)
    if g0["result"] != "pass":
        return PlanReviewResult(approved=False, verdict="REJECTED",
                                findings=findings, blocked_gates=["planspec_valid"])

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
