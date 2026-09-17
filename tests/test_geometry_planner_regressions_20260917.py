"""Regression tests for ENG-R01, ENG-R02 and ENG-R04."""
from __future__ import annotations

import math

import pytest

from domains.building_architecture.geometry_planner import (
    GeometryPlanError,
    plan_loft_mesh,
    plan_profile_sweep,
    sample_circular_arc,
)


def _triangle_area_yz(points, face):
    # Sweep caps lie in a path-station plane (x == const); the cap polygon
    # lives in (normal_offset, z_offset) == (y, z), not XY.
    a, b, c = (points[index] for index in face)
    return abs(
        (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])
    ) / 2.0


def _cap_faces(plan, *, x):
    points = plan["points"]
    return [face for face in plan["faces"] if len(face) == 3 and all(math.isclose(points[i][0], x) for i in face)]


@pytest.mark.parametrize(
    "profile",
    [
        [[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3]],
        [[0, 3], [1, 3], [1, 1], [2, 1], [2, 3], [3, 3], [3, 0], [0, 0]],
    ],
)
def test_concave_profile_caps_cover_polygon_without_fan_overlap(profile):
    plan = plan_profile_sweep(
        profile=profile,
        path=[[0, 0], [10, 0]],
        max_path_deviation=0,
        observed_path_deviation=0,
    )

    cap = _cap_faces(plan, x=0.0)
    assert len(cap) == len(profile) - 2
    assert math.isclose(sum(_triangle_area_yz(plan["points"], face) for face in cap), 7.0)
    assert plan["manifold_expected"] is True


def test_self_intersecting_loft_ring_is_rejected_before_manifold_claim():
    bow_tie = [[0, 0, 0], [2, 2, 0], [0, 2, 0], [2, 0, 0]]
    upper = [[x, y, 2] for x, y, _ in bow_tie]
    with pytest.raises(GeometryPlanError, match="self-intersecting"):
        plan_loft_mesh([bow_tie, upper])


def test_nonplanar_loft_ring_is_rejected():
    lower = [[0, 0, 0], [2, 0, 0], [2, 2, 0.5], [0, 2, 0]]
    upper = [[0, 0, 2], [2, 0, 2], [2, 2, 2], [0, 2, 2]]
    with pytest.raises(GeometryPlanError, match="planar"):
        plan_loft_mesh([lower, upper])


def test_arc_segment_budget_blocks_pathological_request_before_point_generation():
    with pytest.raises(GeometryPlanError, match="arc segment budget exceeded"):
        sample_circular_arc(
            center=[0, 0],
            radius=1_000_000_000.0,
            start_angle_deg=0,
            end_angle_deg=360,
            max_chord_error=1e-9,
            max_segments=1024,
        )
