"""PlanSpec IR — typed intermediate representation and deterministic validator.
Wing: code | Topic: plan-spec-ir | Updated: 2026-09-17 22:45
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "docs" / "schemas" / "plan-spec.schema.json"

_BANNED_CAD_PRIMITIVES = {
    "LINE",
    "LWPOLYLINE",
    "POLYLINE",
    "ARC",
    "CIRCLE",
    "HATCH",
    "TEXT",
    "MTEXT",
    "INSERT",
    "BLOCK",
    "3DFACE",
    "SOLID",
    "SPLINE",
    "ELLIPSE",
}


@dataclass(frozen=True)
class PlanSpecValidationResult:
    valid: bool
    verdict: str  # "APPROVED_FOR_EXECUTION" | "REJECTED"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provenance_summary: dict[str, int] = field(default_factory=dict)
    feature_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "verdict": self.verdict,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "provenance_summary": dict(self.provenance_summary),
            "feature_count": self.feature_count,
        }


def _load_schema_text() -> str:
    # IA-05: installed wheels have no source-tree docs/; prefer packaged
    # resources (cdt_engineer/data/schemas via wheel force-include), fall back
    # to the source checkout path. Same convention as cdt_engineer.server.
    try:
        from importlib import resources
        packaged = resources.files("cdt_engineer").joinpath("data").joinpath("schemas").joinpath(
            "plan-spec.schema.json")
        if packaged.is_file():
            return packaged.read_text(encoding="utf-8")
    except (ImportError, ModuleNotFoundError, FileNotFoundError):
        pass
    return _SCHEMA_PATH.read_text(encoding="utf-8")


def _load_validator() -> Draft202012Validator:
    schema = json.loads(_load_schema_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


_VALIDATOR = _load_validator()


def _scan_for_cad_primitives(data: Any, path: str = "") -> list[str]:
    violations: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else k
            if isinstance(k, str) and k.upper() in _BANNED_CAD_PRIMITIVES:
                violations.append(f"cad_primitive_forbidden_key:{k} at {current_path}")
            violations.extend(_scan_for_cad_primitives(v, current_path))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            violations.extend(_scan_for_cad_primitives(item, f"{path}[{idx}]"))
    elif isinstance(data, str):
        val_upper = data.strip().upper()
        if val_upper in _BANNED_CAD_PRIMITIVES:
            violations.append(f"cad_primitive_forbidden_value:{data} at {path}")
    return violations


def _check_chunk_dag(chunk_deps: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    chunk_ids = {c.get("chunk_id") for c in chunk_deps if "chunk_id" in c}
    adj: dict[str, list[str]] = {}

    for c in chunk_deps:
        cid = c.get("chunk_id")
        if not cid:
            continue
        deps = c.get("depends_on", [])
        for d in deps:
            if d not in chunk_ids:
                errors.append(f"missing_chunk_dependency:{cid}->{d}")
        adj[cid] = list(deps)

    # Cycle detection via DFS
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

    def dfs(node: str) -> bool:
        visited[node] = 1
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                continue
            if visited[neighbor] == 1:
                return True
            if visited[neighbor] == 0 and dfs(neighbor):
                return True
        visited[node] = 2
        return False

    for cid in chunk_ids:
        visited[cid] = 0
    for cid in chunk_ids:
        if visited[cid] == 0:
            if dfs(cid):
                errors.append("cyclic_chunk_dependency_detected")
                break

    return errors


def _validate_architectural_payload(payload: Mapping[str, Any]) -> tuple[list[str], list[str], set[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    feature_ids: set[str] = set()

    walls_map: dict[str, dict[str, Any]] = {}
    # Local cache only: the validator must never mutate caller payloads
    # (a previous revision wrote wall["_length"] into the input mapping).
    wall_lengths: dict[str, float] = {}

    # 1. Axes
    for ax in payload.get("axes", []):
        aid = ax.get("axis_id")
        if aid:
            feature_ids.add(aid)

    # 2. Walls
    for wall in payload.get("walls", []):
        wid = wall.get("wall_id")
        if wid:
            feature_ids.add(wid)
            walls_map[wid] = wall
            start = wall.get("start", [])
            end = wall.get("end", [])
            if len(start) == 2 and len(end) == 2:
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = math.hypot(dx, dy)
                if length < 1e-4:
                    errors.append(f"degenerate_wall_zero_length:{wid}")
                wall_lengths[wid] = length

    # 3. Columns
    for col in payload.get("columns", []):
        cid = col.get("column_id")
        if cid:
            feature_ids.add(cid)

    # 4. Openings
    for op in payload.get("openings", []):
        oid = op.get("opening_id")
        if oid:
            feature_ids.add(oid)
            hwid = op.get("host_wall_id")
            if hwid not in walls_map:
                errors.append(f"unresolved_host_wall:{oid}->{hwid}")
            else:
                host_wall = walls_map[hwid]
                wall_len = wall_lengths.get(hwid, 0.0)
                offset = op.get("offset_along_wall", 0.0)
                width = op.get("width", 0.0)
                if offset + width > wall_len + 1e-4:
                    errors.append(f"opening_exceeds_host_wall_length:{oid}({offset+width}>{wall_len})")
                
                wall_height = host_wall.get("height")
                if wall_height is not None:
                    sill = op.get("sill_height", 0.0)
                    height = op.get("height", 0.0)
                    if sill + height > wall_height + 1e-4:
                        errors.append(f"opening_head_exceeds_wall_height:{oid}({sill+height}>{wall_height})")

    # 5. Spaces
    for sp in payload.get("spaces", []):
        sid = sp.get("space_id")
        if sid:
            feature_ids.add(sid)
            poly = sp.get("boundary_polygon", [])
            if len(poly) >= 3:
                # Shoelace formula to verify non-zero area
                area = 0.0
                n = len(poly)
                for i in range(n):
                    j = (i + 1) % n
                    area += poly[i][0] * poly[j][1]
                    area -= poly[j][0] * poly[i][1]
                area = abs(area) / 2.0
                if area < 1e-4:
                    errors.append(f"degenerate_space_zero_area:{sid}")

    # 6. Fixtures
    for fx in payload.get("fixtures", []):
        fid = fx.get("fixture_id")
        if fid:
            feature_ids.add(fid)

    # 7. Dimensions
    for dm in payload.get("dimensions", []):
        did = dm.get("dimension_id")
        if did:
            feature_ids.add(did)

    return errors, warnings, feature_ids


def _validate_civil_road_profile(payload: Mapping[str, Any]) -> tuple[list[str], list[str], set[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    feature_ids: set[str] = set()

    ground_line = payload.get("ground_line", [])
    grade_line = payload.get("grade_line", [])

    # Check ground line monotonicity
    prev_st = -float("inf")
    for idx, pt in enumerate(ground_line):
        st = pt.get("station", 0.0)
        feature_ids.add(f"ground_pt_{idx}")
        if st <= prev_st:
            errors.append(f"ground_line_non_monotonic_station:{idx}({st}<={prev_st})")
        prev_st = st

    # Check grade line monotonicity and slope reasonableness
    prev_st = -float("inf")
    for idx, pvi in enumerate(grade_line):
        st = pvi.get("station", 0.0)
        feature_ids.add(f"pvi_{idx}")
        if st <= prev_st:
            errors.append(f"grade_line_non_monotonic_station:{idx}({st}<={prev_st})")
        prev_st = st

        gin = pvi.get("grade_in_percent")
        if gin is not None and abs(gin) > 20.0:
            warnings.append(f"steep_grade_in_percent:{idx}({gin}%)")
        gout = pvi.get("grade_out_percent")
        if gout is not None and abs(gout) > 20.0:
            warnings.append(f"steep_grade_out_percent:{idx}({gout}%)")

    for idx, cr in enumerate(payload.get("crossings", [])):
        feature_ids.add(f"crossing_{idx}")

    return errors, warnings, feature_ids


def _validate_civil_road_cross_section(payload: Mapping[str, Any]) -> tuple[list[str], list[str], set[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    feature_ids: set[str] = set()

    cw = payload.get("carriageway", {})
    wl = cw.get("width_left", 0.0)
    wr = cw.get("width_right", 0.0)
    if wl + wr <= 1e-4:
        errors.append("carriageway_total_width_zero")
    feature_ids.add("carriageway")

    layers = payload.get("pavement_structure", [])
    seen_orders: set[int] = set()
    total_thickness = 0.0
    for ly in layers:
        lid = ly.get("layer_id")
        if lid:
            feature_ids.add(lid)
        order = ly.get("order")
        if order in seen_orders:
            errors.append(f"duplicate_pavement_layer_order:{order}")
        if order is not None:
            seen_orders.add(order)
        th = ly.get("thickness", 0.0)
        total_thickness += th

    if total_thickness <= 1e-4:
        errors.append("pavement_structure_total_thickness_zero")

    return errors, warnings, feature_ids


def validate_plan_spec(spec: Mapping[str, Any]) -> PlanSpecValidationResult:
    """Validate an engineering PlanSpec intermediate representation against schema and hard gates."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Schema gate
    schema_errors = list(_VALIDATOR.iter_errors(spec))
    if schema_errors:
        for err in schema_errors:
            path = ".".join(str(p) for p in err.path)
            errors.append(f"schema_violation:{path}:{err.message}")
        return PlanSpecValidationResult(
            valid=False,
            verdict="REJECTED",
            errors=errors,
            warnings=warnings,
            provenance_summary={},
            feature_count=0,
        )

    # 2. Gate CAD Primitive Ban
    cad_primitive_violations = _scan_for_cad_primitives(spec.get("payload", {}))
    if cad_primitive_violations:
        errors.extend(cad_primitive_violations)

    # 3. Gate Coordinate system & Dual scale
    coords = spec.get("coordinate_system", {})
    scale = coords.get("scale", {})
    h_scale = scale.get("horizontal", 0.0)
    v_scale = scale.get("vertical", h_scale)
    if h_scale <= 0.0 or (v_scale is not None and v_scale <= 0.0):
        errors.append("invalid_coordinate_scale_non_positive")

    # 4. Gate Chunk DAG
    chunk_deps = spec.get("chunk_dependencies", [])
    if chunk_deps:
        errors.extend(_check_chunk_dag(chunk_deps))

    # 5. Domain-specific payload validation
    plan_type = spec.get("plan_type")
    payload = spec.get("payload", {})
    feature_ids: set[str] = set()

    if plan_type == "architectural_floor_plan":
        sub_errs, sub_warns, f_ids = _validate_architectural_payload(payload)
        errors.extend(sub_errs)
        warnings.extend(sub_warns)
        feature_ids.update(f_ids)
    elif plan_type == "civil_road_profile":
        sub_errs, sub_warns, f_ids = _validate_civil_road_profile(payload)
        errors.extend(sub_errs)
        warnings.extend(sub_warns)
        feature_ids.update(f_ids)
    elif plan_type == "civil_road_cross_section":
        sub_errs, sub_warns, f_ids = _validate_civil_road_cross_section(payload)
        errors.extend(sub_errs)
        warnings.extend(sub_warns)
        feature_ids.update(f_ids)

    # 6. Gate Provenance Completeness
    ledger = spec.get("provenance_ledger", {})
    assumptions_map = {a.get("id"): a for a in spec.get("assumptions", []) if "id" in a}

    provenance_summary: dict[str, int] = {
        "observed": 0,
        "specified": 0,
        "derived": 0,
        "inferred": 0,
        "approved_assumption": 0,
        "unknown": 0,
    }

    # Verify every extracted feature ID is registered in the ledger
    for fid in feature_ids:
        if fid not in ledger:
            errors.append(f"missing_provenance_entry_for_feature:{fid}")

    # Validate ledger entries
    for entry_id, p_info in ledger.items():
        status = p_info.get("status")
        if status in provenance_summary:
            provenance_summary[status] += 1
        if status == "approved_assumption":
            as_id = p_info.get("assumption_id")
            if not as_id or as_id not in assumptions_map:
                errors.append(f"unlinked_approved_assumption:{entry_id}->{as_id}")

    valid = len(errors) == 0
    verdict = "APPROVED_FOR_EXECUTION" if valid else "REJECTED"

    return PlanSpecValidationResult(
        valid=valid,
        verdict=verdict,
        errors=errors,
        warnings=warnings,
        provenance_summary=provenance_summary,
        feature_count=len(feature_ids),
    )
