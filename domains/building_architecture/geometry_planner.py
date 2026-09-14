"""Bounded complex-geometry planning for Building Architecture.
Wing: code | Topic: building-complex-geometry | Updated: 2026-09-14 10:22

This module produces generic indexed-mesh recipes for an external CAD executor. It is
not a CAD kernel and does not call SketchUp/native APIs.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence

from domains.guard_primitives import finite_number

_EPS = 1e-9


class GeometryPlanError(ValueError):
    """Raised when a requested bounded geometry plan cannot be represented truthfully."""


@dataclass(frozen=True)
class MeshBudget:
    """Public executor limits mirrored by the Engineer planning boundary."""

    max_vertices: int = 2048
    max_faces: int = 4096
    max_face_vertices: int = 16
    max_index_references: int = 32768


def _point2(value, name: str) -> tuple[float, float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != 2:
        raise GeometryPlanError(f"{name} must contain two finite numbers")
    return finite_number(value[0], f"{name}[0]"), finite_number(value[1], f"{name}[1]")


def _point3(value, name: str) -> tuple[float, float, float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != 3:
        raise GeometryPlanError(f"{name} must contain three finite numbers")
    return (
        finite_number(value[0], f"{name}[0]"),
        finite_number(value[1], f"{name}[1]"),
        finite_number(value[2], f"{name}[2]"),
    )


def _orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, p) -> bool:
    return (
        min(a[0], b[0]) - _EPS <= p[0] <= max(a[0], b[0]) + _EPS
        and min(a[1], b[1]) - _EPS <= p[1] <= max(a[1], b[1]) + _EPS
        and abs(_orientation(a, b, p)) <= _EPS
    )


def _segments_intersect(a, b, c, d) -> bool:
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


def _validate_profile(profile: Sequence[Sequence[float]]) -> list[tuple[float, float]]:
    if isinstance(profile, (str, bytes)) or not isinstance(profile, Sequence):
        raise GeometryPlanError("profile must be a sequence")
    points = [_point2(point, f"profile[{index}]") for index, point in enumerate(profile)]
    if len(points) >= 2 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 3 or len(set(points)) < 3:
        raise GeometryPlanError("profile requires at least three unique points")
    for index in range(len(points)):
        a = points[index]
        b = points[(index + 1) % len(points)]
        if math.dist(a, b) <= _EPS:
            raise GeometryPlanError("profile contains a zero-length edge")
        for other in range(index + 1, len(points)):
            if other in {index, (index + 1) % len(points)} or index == (other + 1) % len(points):
                continue
            c = points[other]
            d = points[(other + 1) % len(points)]
            if _segments_intersect(a, b, c, d):
                raise GeometryPlanError("profile is self-intersecting")
    area2 = sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )
    if abs(area2) <= _EPS:
        raise GeometryPlanError("profile area is degenerate")
    return points


def _check_budget(points: Sequence, faces: Sequence[Sequence[int]], budget: MeshBudget) -> None:
    if len(points) > budget.max_vertices:
        raise GeometryPlanError(f"mesh budget exceeded: vertices {len(points)} > {budget.max_vertices}")
    if len(faces) > budget.max_faces:
        raise GeometryPlanError(f"mesh budget exceeded: faces {len(faces)} > {budget.max_faces}")
    if any(len(face) > budget.max_face_vertices for face in faces):
        raise GeometryPlanError(f"mesh budget exceeded: face vertex count > {budget.max_face_vertices}")
    refs = sum(len(face) for face in faces)
    if refs > budget.max_index_references:
        raise GeometryPlanError(
            f"mesh budget exceeded: index references {refs} > {budget.max_index_references}"
        )


def _bounds(points: Sequence[Sequence[float]]) -> dict:
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def plan_loft_mesh(
    sections: Sequence[Sequence[Sequence[float]]],
    *,
    budget: MeshBudget | None = None,
) -> dict:
    """Connect equal-cardinality 3D section rings into one capped indexed mesh."""
    budget = budget or MeshBudget()
    if isinstance(sections, (str, bytes)) or not isinstance(sections, Sequence) or len(sections) < 2:
        raise GeometryPlanError("loft requires at least two sections")
    normalized: list[list[tuple[float, float, float]]] = []
    width = None
    for section_index, raw in enumerate(sections):
        if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
            raise GeometryPlanError("each loft section must be a point sequence")
        ring = [_point3(point, f"sections[{section_index}][{point_index}]") for point_index, point in enumerate(raw)]
        if len(ring) < 3 or len(set(ring)) < 3:
            raise GeometryPlanError("each loft section requires at least three unique points")
        if width is None:
            width = len(ring)
        elif len(ring) != width:
            raise GeometryPlanError("all loft sections must have equal point count")
        normalized.append(ring)
    assert width is not None

    points = [list(point) for ring in normalized for point in ring]
    faces: list[list[int]] = []
    section_count = len(normalized)
    for section_index in range(section_count - 1):
        base_a = section_index * width
        base_b = (section_index + 1) * width
        for vertex_index in range(width):
            nxt = (vertex_index + 1) % width
            faces.append([base_a + vertex_index, base_a + nxt, base_b + nxt, base_b + vertex_index])

    for vertex_index in range(1, width - 1):
        faces.append([0, vertex_index + 1, vertex_index])
    last = (section_count - 1) * width
    for vertex_index in range(1, width - 1):
        faces.append([last, last + vertex_index, last + vertex_index + 1])

    _check_budget(points, faces, budget)
    chunk = {
        "chunk_id": "mesh-0001",
        "points": points,
        "faces": faces,
        "vertex_count": len(points),
        "face_count": len(faces),
    }
    return {
        "representation": "indexed_mesh",
        "points": points,
        "faces": faces,
        "vertex_count": len(points),
        "face_count": len(faces),
        "index_reference_count": sum(len(face) for face in faces),
        "bounds": _bounds(points),
        "manifold_expected": True,
        "budget": {
            "max_vertices": budget.max_vertices,
            "max_faces": budget.max_faces,
            "max_face_vertices": budget.max_face_vertices,
            "max_index_references": budget.max_index_references,
        },
        "chunks": [chunk],
        "chunking_disposition": "single_bounded_chunk",
    }


def sample_circular_arc(
    *,
    center: Sequence[float],
    radius,
    start_angle_deg,
    end_angle_deg,
    max_chord_error,
) -> dict:
    """Sample a planar circular arc with a mathematically bounded sagitta error."""
    cx, cy = _point2(center, "center")
    radius = finite_number(radius, "radius")
    start = math.radians(finite_number(start_angle_deg, "start_angle_deg"))
    end = math.radians(finite_number(end_angle_deg, "end_angle_deg"))
    tolerance = finite_number(max_chord_error, "max_chord_error")
    if radius <= 0 or tolerance <= 0:
        raise GeometryPlanError("radius and max_chord_error must be positive")
    sweep = end - start
    if abs(sweep) <= _EPS:
        raise GeometryPlanError("arc sweep must be nonzero")
    if tolerance >= radius:
        max_segment_angle = math.pi
    else:
        ratio = max(-1.0, min(1.0, 1.0 - tolerance / radius))
        max_segment_angle = 2.0 * math.acos(ratio)
    if max_segment_angle <= _EPS:
        raise GeometryPlanError("requested chord error is too small to sample safely")
    segments = max(1, math.ceil(abs(sweep) / max_segment_angle))
    step = sweep / segments
    points = [
        [cx + radius * math.cos(start + step * index), cy + radius * math.sin(start + step * index)]
        for index in range(segments + 1)
    ]
    actual_error = radius * (1.0 - math.cos(abs(step) / 2.0))
    return {
        "points": points,
        "segment_count": segments,
        "max_chord_error_requested": tolerance,
        "max_chord_error_bound": actual_error,
    }


def plan_profile_sweep(
    *,
    profile: Sequence[Sequence[float]],
    path: Sequence[Sequence[float]],
    max_path_deviation,
    observed_path_deviation,
    base_z=0.0,
    budget: MeshBudget | None = None,
) -> dict:
    """Sweep a 2D normal/Z profile along a planar polyline and return a bounded mesh recipe.

    Profile coordinates are ``[normal_offset, z_offset]``. At each path station the
    local planar normal is derived deterministically from neighboring stations.
    """
    profile_points = _validate_profile(profile)
    if isinstance(path, (str, bytes)) or not isinstance(path, Sequence) or len(path) < 2:
        raise GeometryPlanError("path requires at least two points")
    path_points = [_point2(point, f"path[{index}]") for index, point in enumerate(path)]
    for index in range(len(path_points) - 1):
        if math.dist(path_points[index], path_points[index + 1]) <= _EPS:
            raise GeometryPlanError("path contains consecutive duplicate points")

    allowed = finite_number(max_path_deviation, "max_path_deviation")
    observed = finite_number(observed_path_deviation, "observed_path_deviation")
    z0 = finite_number(base_z, "base_z")
    if allowed < 0 or observed < 0:
        raise GeometryPlanError("path deviations must be nonnegative")
    if observed > allowed + _EPS:
        raise GeometryPlanError("path deviation exceeds allowance")

    sections = []
    for index, point in enumerate(path_points):
        if index == 0:
            tx = path_points[1][0] - point[0]
            ty = path_points[1][1] - point[1]
        elif index == len(path_points) - 1:
            tx = point[0] - path_points[index - 1][0]
            ty = point[1] - path_points[index - 1][1]
        else:
            tx = path_points[index + 1][0] - path_points[index - 1][0]
            ty = path_points[index + 1][1] - path_points[index - 1][1]
        length = math.hypot(tx, ty)
        if length <= _EPS:
            raise GeometryPlanError("path tangent is degenerate")
        nx, ny = -ty / length, tx / length
        sections.append(
            [
                [point[0] + nx * normal_offset, point[1] + ny * normal_offset, z0 + z_offset]
                for normal_offset, z_offset in profile_points
            ]
        )

    plan = plan_loft_mesh(sections, budget=budget)
    plan.update(
        {
            "planner": "plan_profile_sweep",
            "profile_vertex_count": len(profile_points),
            "path_station_count": len(path_points),
            "max_path_deviation_allowed": allowed,
            "max_path_deviation_observed": observed,
            "approximation_state": "bounded" if observed > 0 else "exact_for_supplied_path",
        }
    )
    return plan
