"""Deterministic PlanSpec -> semantic feature chunks compiler (ENG-R09).
Wing: code | Topic: plan-compiler | Updated: 2026-10-06 16:14 (Asia/Ho_Chi_Minh)
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from execution.plan_review import review_plan_spec
from execution.plan_revise import plan_fingerprint
from execution.planspec import validate_plan_spec

_DEFAULT_MAX_FEATURES_PER_CHUNK = 256

# (semantic_type, payload_keys, id_key_or_None_for_synthetic, group_deps, capabilities)
_ARCH_GROUPS: tuple = (
    ("grid_axes", ("axes",), "axis_id", (), ("geometry.create", "geometry.measure")),
    (
        "wall_shell",
        ("walls", "columns"),
        None,
        ("grid_axes",),
        ("geometry.create", "geometry.measure"),
    ),
    (
        "openings",
        ("openings",),
        "opening_id",
        ("wall_shell",),
        ("geometry.create", "geometry.measure"),
    ),
    (
        "spaces_fixtures",
        ("spaces", "fixtures"),
        None,
        ("wall_shell",),
        ("geometry.create", "geometry.measure"),
    ),
    (
        "annotation_dimensions",
        ("dimensions",),
        "dimension_id",
        ("wall_shell",),
        ("annotation.create", "geometry.measure"),
    ),
)

_PROFILE_GROUPS: tuple = (
    ("profile_ground", ("ground_line",), None, (), ("geometry.create", "geometry.measure")),
    (
        "profile_grade",
        ("grade_line",),
        None,
        ("profile_ground",),
        ("geometry.create", "geometry.measure"),
    ),
    (
        "profile_crossings",
        ("crossings",),
        None,
        ("profile_grade",),
        ("geometry.create", "geometry.measure"),
    ),
)

_XS_GROUPS: tuple = (
    (
        "xs_carriageway",
        ("carriageway", "shoulders"),
        None,
        (),
        ("geometry.create", "geometry.measure"),
    ),
    (
        "xs_pavement",
        ("pavement_structure",),
        "layer_id",
        ("xs_carriageway",),
        ("geometry.create", "geometry.measure"),
    ),
    (
        "xs_slopes_drainage",
        ("side_slopes",),
        None,
        ("xs_carriageway",),
        ("geometry.create", "geometry.measure"),
    ),
)

_ID_KEYS = {
    "axes": "axis_id",
    "walls": "wall_id",
    "columns": "column_id",
    "openings": "opening_id",
    "spaces": "space_id",
    "fixtures": "fixture_id",
    "dimensions": "dimension_id",
    "pavement_structure": "layer_id",
}

_SYNTHETIC_PREFIX = {
    "ground_line": "ground_pt",
    "grade_line": "pvi",
    "crossings": "crossing",
}


def _normalize_requirements(requirements: Mapping[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "max_features_per_chunk": _DEFAULT_MAX_FEATURES_PER_CHUNK,
        "max_chunk_payload_bytes": 65536,
    }
    if requirements is None:
        return merged
    if not isinstance(requirements, Mapping):
        raise ValueError("requirements must be a mapping")
    merged.update(requirements)
    budget = merged["max_features_per_chunk"]
    if isinstance(budget, bool) or not isinstance(budget, int) or not 1 <= budget <= 4096:
        raise ValueError("requirements.max_features_per_chunk must be an integer in 1..4096")
    byte_budget = merged["max_chunk_payload_bytes"]
    if (
        isinstance(byte_budget, bool)
        or not isinstance(byte_budget, int)
        or not 1024 <= byte_budget <= 1048576
    ):
        raise ValueError("requirements.max_chunk_payload_bytes must be an integer in 1024..1048576")
    cell = merged.get("spatial_cell_size")
    if cell is not None:
        try:
            if isinstance(cell, bool) or not isinstance(cell, (int, float)):
                raise ValueError
            cell = float(cell)
        except (ValueError, OverflowError):
            raise ValueError("requirements.spatial_cell_size must be finite and positive") from None
        merged["spatial_cell_size"] = cell
    if cell is not None and (
        isinstance(cell, bool)
        or not isinstance(cell, (int, float))
        or not math.isfinite(cell)
        or cell <= 0
    ):
        raise ValueError("requirements.spatial_cell_size must be finite and positive")
    return merged


def _feature_bounds(item, payload):
    """Conservative local-plan bounds for scope/partition, not collision acceptance."""
    points = []
    pad = 0.0
    for key in ("start", "end", "center", "position"):
        if key in item:
            points.append(item[key])
    points.extend(item.get("boundary_polygon", []))
    points.extend(item.get("witness_points", []))
    if "host_wall_id" in item:
        host = next(
            (w for w in payload.get("walls", []) if w["wall_id"] == item["host_wall_id"]), None
        )
        if host:
            pad = host["thickness"] / 2
            a, b = host["start"], host["end"]
            length = _wall_length(host)
            dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
            points.extend(
                [
                    [a[0] + dx * t, a[1] + dy * t]
                    for t in (item["offset_along_wall"], item["offset_along_wall"] + item["width"])
                ]
            )
    if not points:
        return None
    if item.get("dimensions"):
        # Circumscribed radius includes rotated fixtures and circular columns.
        dims = item["dimensions"]
        pad = math.hypot(*dims) / 2 if len(dims) == 2 else dims[0] / 2
    elif "thickness" in item:
        pad = item["thickness"] / 2
    return [
        min(p[0] for p in points) - pad,
        min(p[1] for p in points) - pad,
        max(p[0] for p in points) + pad,
        max(p[1] for p in points) + pad,
    ]


def _spatial_parts(entries, payload, cell, budget):
    buckets = {}
    for entry in entries:
        bounds = _feature_bounds(entry[1], payload) if cell is not None else None
        key = (
            (
                math.floor((bounds[0] / 2 + bounds[2] / 2) / cell),
                math.floor((bounds[1] / 2 + bounds[3] / 2) / cell),
            )
            if bounds
            else (0, 0)
        )
        buckets.setdefault(key, []).append(entry)
    return [
        items[i : i + budget]
        for key, items in sorted(buckets.items())
        for i in range(0, len(items), budget)
    ]


def _seal_chunk(chunk):
    chunk["chunk_sha256"] = plan_fingerprint(chunk)
    # Include these metadata fields in the actual UTF-8 serialized byte bound.
    chunk["payload_bytes"] = 0
    for _ in range(4):
        size = len(
            json.dumps(
                chunk, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
            ).encode("utf-8")
        )
        if size == chunk["payload_bytes"]:
            break
        chunk["payload_bytes"] = size
    return chunk


def _feature_entries(payload_key: str, items: Any) -> list[tuple[str, Any]]:
    """Return (feature_id, semantic_feature) pairs preserving payload order."""
    if isinstance(items, Mapping):
        # Singleton groups: carriageway, shoulders, side_slopes.
        return [(payload_key, items)]
    entries: list[tuple[str, Any]] = []
    prefix = _SYNTHETIC_PREFIX.get(payload_key)
    for idx, item in enumerate(items or []):
        if not isinstance(item, Mapping):
            continue
        fid = item.get(_ID_KEYS.get(payload_key, "")) if _ID_KEYS.get(payload_key) else None
        if not fid and prefix:
            fid = f"{prefix}_{idx}"
        entries.append((fid or f"{payload_key}_{idx}", item))
    return entries


def _wall_length(wall: Mapping[str, Any]) -> float:
    start, end = wall.get("start", [0.0, 0.0]), wall.get("end", [0.0, 0.0])
    return math.hypot(end[0] - start[0], end[1] - start[1])


def _postconditions(semantic_type: str, features: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    items = [item for _, item in features]
    if semantic_type == "grid_axes":
        return {"axis_count": len(items)}
    if semantic_type == "wall_shell":
        walls = [i for i in items if isinstance(i, Mapping) and "wall_id" in i]
        cols = [i for i in items if isinstance(i, Mapping) and "column_id" in i]
        return {
            "wall_count": len(walls),
            "column_count": len(cols),
            "total_wall_length": sum(_wall_length(w) for w in walls),
        }
    if semantic_type == "openings":
        doors = sum(1 for i in items if isinstance(i, Mapping) and i.get("opening_type") == "door")
        return {
            "opening_count": len(items),
            "door_count": doors,
            "window_count": len(items) - doors,
        }
    if semantic_type == "spaces_fixtures":
        spaces = [i for i in items if isinstance(i, Mapping) and "space_id" in i]
        return {
            "space_count": len(spaces),
            "fixture_count": len(items) - len(spaces),
            "total_net_area": sum(
                float(i.get("net_area", 0.0))
                for i in spaces
                if isinstance(i.get("net_area"), (int, float))
            ),
        }
    if semantic_type == "annotation_dimensions":
        return {"dimension_count": len(items)}
    if semantic_type == "profile_ground":
        stations = [i.get("station", 0.0) for i in items if isinstance(i, Mapping)]
        return {
            "point_count": len(items),
            "station_span": (max(stations) - min(stations)) if stations else 0.0,
        }
    if semantic_type == "profile_grade":
        grades = [
            abs(float(i.get("grade_out_percent", i.get("grade_in_percent", 0.0))))
            for i in items
            if isinstance(i, Mapping)
        ]
        return {"pvi_count": len(items), "max_abs_grade_percent": max(grades) if grades else 0.0}
    if semantic_type == "profile_crossings":
        return {"crossing_count": len(items)}
    if semantic_type == "xs_carriageway":
        cw = next((i for _, i in features if isinstance(i, Mapping) and "width_left" in i), {})
        return {
            "total_carriageway_width": float(cw.get("width_left", 0.0))
            + float(cw.get("width_right", 0.0))
        }
    if semantic_type == "xs_pavement":
        return {
            "layer_count": len(items),
            "total_thickness": sum(
                float(i.get("thickness", 0.0)) for i in items if isinstance(i, Mapping)
            ),
        }
    if semantic_type == "xs_slopes_drainage":
        ditches = sum(
            1 for _, i in features if isinstance(i, Mapping) and isinstance(i.get("ditch"), Mapping)
        )
        return {"side_count": len(items), "ditch_count": ditches}
    return {"feature_count": len(items)}


def _scope_text(
    plan_id: str, semantic_type: str, features: Sequence[tuple[str, Any]], post: Mapping[str, Any]
) -> str:
    details = ", ".join(
        f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in post.items()
    )
    return f"{plan_id}:{semantic_type} [{len(features)} features] {details}"


@dataclass(frozen=True)
class PlanCompileResult:
    ok: bool
    verdict: str  # "COMPILED_READY_FOR_EXECUTION" | "REFUSED"
    chunks: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    chunk_count: int = 0
    feature_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verdict": self.verdict,
            "chunks": [dict(c) for c in self.chunks],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "chunk_count": self.chunk_count,
            "feature_count": self.feature_count,
        }


def _groups_for(plan_type: str) -> tuple | None:
    if plan_type == "architectural_floor_plan":
        return _ARCH_GROUPS
    if plan_type == "civil_road_profile":
        return _PROFILE_GROUPS
    if plan_type == "civil_road_cross_section":
        return _XS_GROUPS
    return None


def compile_plan_spec(
    spec: Mapping[str, Any], requirements: Mapping[str, Any] | None = None
) -> PlanCompileResult:
    """Compile an approved PlanSpec IR into bounded semantic feature chunks.

    Fail-closed pipeline: the spec must pass schema validation AND the
    pre-CAD professional review (APPROVED_FOR_EXECUTION) before any chunk
    is emitted. Chunks carry semantic features only — never CAD primitives.
    """
    if not isinstance(spec, Mapping):
        raise ValueError("spec must be a mapping")
    req = _normalize_requirements(requirements)

    validity = validate_plan_spec(spec)
    if not validity.valid:
        return PlanCompileResult(
            ok=False,
            verdict="REFUSED",
            errors=[f"planspec_invalid:{e}" for e in validity.errors[:8]],
        )
    review = review_plan_spec(spec, requirements)
    if not review.approved:
        return PlanCompileResult(
            ok=False,
            verdict="REFUSED",
            errors=[f"review_not_approved:{gate}" for gate in review.blocked_gates],
        )

    plan_type = spec.get("plan_type")
    groups = _groups_for(plan_type)
    if groups is None:
        return PlanCompileResult(
            ok=False, verdict="REFUSED", errors=[f"unsupported_plan_type_for_compiler:{plan_type}"]
        )

    plan_id = spec.get("plan_id", "plan")
    batch_session_id = req.get("batch_session_id", plan_id)
    budget = req["max_features_per_chunk"]
    ledger = spec.get("provenance_ledger", {})
    payload = spec.get("payload", {})
    source_inventory = spec.get("source_inventory")
    plan_sha256 = plan_fingerprint(spec)
    policy_sha256 = plan_fingerprint(req)
    cell = req.get("spatial_cell_size")
    if cell is None and plan_type == "architectural_floor_plan":
        cell = {"mm": 10000.0, "cm": 1000.0, "m": 10.0}.get(spec["units"]["length"])
    source_binding = {}
    if source_inventory is not None:
        source_binding = {
            "source_sha256": source_inventory["source_sha256"],
            "source_inventory_sha256": hashlib.sha256(
                json.dumps(
                    source_inventory,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest(),
        }

    chunks: list[dict[str, Any]] = []
    semantic_chunk_ids: dict[str, list[str]] = {}
    feature_total = 0

    def _resolve_deps(group_deps: Sequence[str], group_defs: Mapping[str, tuple]) -> list[str]:
        resolved: list[str] = []
        for dep in group_defs and group_deps or []:
            ids = semantic_chunk_ids.get(dep, [])
            if ids:
                # Each group is chained; the last receipt transitively seals
                # every earlier group chunk without an O(n) dependency payload.
                resolved.append(ids[-1])
            else:
                # Depended group emitted nothing (empty feature set): inherit
                # its own dependencies transitively so ordering stays valid.
                parent = group_defs.get(dep)
                if parent:
                    resolved.extend(_resolve_deps(parent[2], group_defs))
        seen: list[str] = []
        for chunk_id in resolved:
            if chunk_id not in seen:
                seen.append(chunk_id)
        return seen

    group_defs = {
        semantic: (keys, id_key, deps, caps) for semantic, keys, id_key, deps, caps in groups
    }
    for semantic, keys, _id_key, deps, caps in groups:
        entries: list[tuple[str, Any]] = []
        for key in keys:
            entries.extend(_feature_entries(key, payload.get(key)))
        if not entries:
            semantic_chunk_ids[semantic] = []
            continue
        base_deps = _resolve_deps(deps, group_defs)
        try:
            slices = _spatial_parts(entries, payload, cell, budget)
        except (OverflowError, ValueError):
            return PlanCompileResult(
                ok=False, verdict="REFUSED", errors=["spatial_partition_unrepresentable"]
            )
        group_ids: list[str] = []
        while slices:
            part = slices.pop(0)
            idx = len(group_ids) + 1
            chunk_id = f"{plan_id}:{semantic}:{idx:02d}"
            part_deps = list(base_deps) if idx == 1 else [f"{plan_id}:{semantic}:{idx - 1:02d}"]
            post = _postconditions(semantic, part)
            provenance = {fid: (ledger.get(fid, {}).get("status", "unknown")) for fid, _ in part}
            bounds = [_feature_bounds(item, payload) for _, item in part] if cell else []
            bounds = [b for b in bounds if b is not None]
            chunk = {
                "batch_session_id": batch_session_id,
                "chunk_id": chunk_id,
                "semantic_type": semantic,
                "scope": _scope_text(plan_id, semantic, part, post),
                "feature_ids": [fid for fid, _ in part],
                "features": [copy.deepcopy(item) for _, item in part],
                "depends_on": part_deps,
                "expected_outputs": dict(post),
                "required_capabilities": list(caps),
                # Requested isolation; the executor must confirm the actual
                # native mode at preflight (never inferred from call success).
                "transaction_policy": "checkpointed_atomic",
                "transaction_source": "compiler_requested_executor_must_confirm",
                "recovery_mode": "compensating",
                "verification_policy": "read_after_write",
                "ui_yield": True,
                "provenance": provenance,
                "plan_sha256": plan_sha256,
                "planning_policy_sha256": policy_sha256,
                "spatial_bounds": [
                    min(b[0] for b in bounds),
                    min(b[1] for b in bounds),
                    max(b[2] for b in bounds),
                    max(b[3] for b in bounds),
                ]
                if bounds
                else None,
                **source_binding,
                # Layer discipline (G13): lane layer names travel with the
                # chunk so the executor binds native layers deterministically.
                "layers": sorted(
                    {
                        item.get("layer")
                        for _, item in part
                        if isinstance(item, Mapping) and isinstance(item.get("layer"), str)
                    }
                ),
            }
            _seal_chunk(chunk)
            if chunk["payload_bytes"] > req["max_chunk_payload_bytes"]:
                if len(part) == 1:
                    return PlanCompileResult(
                        ok=False,
                        verdict="REFUSED",
                        errors=[f"feature_payload_exceeds_budget:{part[0][0]}"],
                    )
                middle = len(part) // 2
                slices[:0] = [part[:middle], part[middle:]]
                continue
            chunks.append(chunk)
            group_ids.append(chunk_id)
            feature_total += len(part)
        semantic_chunk_ids[semantic] = group_ids

    return PlanCompileResult(
        ok=True,
        verdict="COMPILED_READY_FOR_EXECUTION",
        chunks=chunks,
        chunk_count=len(chunks),
        feature_count=feature_total,
    )
