#!/usr/bin/env python3
"""Export real geometry-planner recipes as ENG-R03 end-to-end fixtures.

Wing: code | Topic: planner-fixtures | Updated: 2026-09-17

Each fixture is produced by the actual
:mod:`domains.building_architecture.geometry_planner` (never hand-written
coordinates) and pairs the recipe with its ``create_mesh`` payload plus the
analytically expected oracle values. The CDT-SketchUp acceptance consumes
``create_mesh`` and returns ``get_entity_state`` read-backs that
:mod:`domains.building_architecture.plan_oracle` verifies.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from domains.building_architecture.geometry_planner import (
    plan_loft_mesh,
    plan_profile_sweep,
    sample_circular_arc,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "domains" / "building-architecture" / "e2e-fixtures"


def _polygon_area(outline) -> float:
    total = 0.0
    count = len(outline)
    for index in range(count):
        x0, y0 = outline[index]
        x1, y1 = outline[(index + 1) % count]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def _path_length(path) -> float:
    return sum(
        math.dist(path[index], path[index + 1]) for index in range(len(path) - 1)
    )


def _frustum_volume(area_a: float, area_b: float, height: float) -> float:
    return height / 3.0 * (area_a + area_b + math.sqrt(area_a * area_b))


def _fixture(case_id: str, planner: str, inputs: dict, recipe: dict,
             expected_volume: float | None,
             volume_tolerance: float = 1e-6,
             volume_tolerance_reason: str = "") -> dict:
    expected: dict = {
        "planner_unit": "mm",
        "expected_volume": expected_volume,
        "volume_tolerance": volume_tolerance,
        "bounds": recipe["bounds"],
        "vertex_count": recipe["vertex_count"],
        "face_count": recipe["face_count"],
    }
    if volume_tolerance_reason:
        expected["volume_tolerance_reason"] = volume_tolerance_reason
    return {
        "case_id": case_id,
        "planner": planner,
        "planner_inputs": inputs,
        "recipe": recipe,
        "create_mesh": {
            "name": case_id,
            "points": recipe["points"],
            "faces": recipe["faces"],
            "unit": "mm",
            "expect": {
                "active_entity_delta": 1,
                "type": "Group",
                "vertex_count": recipe["vertex_count"],
                "face_count": recipe["face_count"],
            },
        },
        "expected": expected,
    }


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = []

    rect = [[0, 0], [10, 0], [10, 20], [0, 20]]
    straight = [[0, 0], [100, 0]]
    recipe = plan_profile_sweep(
        profile=rect, path=straight,
        max_path_deviation=0.0, observed_path_deviation=0.0,
    )
    fixtures.append(_fixture(
        "straight-rect-sweep", "plan_profile_sweep",
        {"profile": rect, "path": straight},
        recipe, _polygon_area(rect) * _path_length(straight),
    ))

    lower = [[-10, -10, 0], [10, -10, 0], [10, 10, 0], [-10, 10, 0]]
    upper = [[-5, -5, 100], [5, -5, 100], [5, 5, 100], [-5, 5, 100]]
    recipe = plan_loft_mesh([lower, upper])
    fixtures.append(_fixture(
        "tapered-quad-loft", "plan_loft_mesh",
        {"sections": [lower, upper]},
        recipe, _frustum_volume(400.0, 100.0, 100.0),
    ))

    concave = [[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3]]
    short_path = [[0, 0], [10, 0]]
    recipe = plan_profile_sweep(
        profile=concave, path=short_path,
        max_path_deviation=0.0, observed_path_deviation=0.0,
    )
    fixtures.append(_fixture(
        "concave-c-sweep", "plan_profile_sweep",
        {"profile": concave, "path": short_path},
        recipe, _polygon_area(concave) * _path_length(short_path),
        # Measured native volume precision on re-entrant cap tessellation
        # (SketchUp 2024 24.0.594): rel dev 7.9e-05 vs convex cases ~1e-07.
        # 2e-04 stays far below engineering significance; case-specific.
        volume_tolerance=2e-4,
        volume_tolerance_reason=(
            "measured native volume deviation 7.9e-05 on concave caps, "
            "SketchUp 2024 24.0.594, 2026-09-17 live run"
        ),
    ))

    tall_rect = [[0, 0], [20, 0], [20, 40], [0, 40]]
    arc = sample_circular_arc(
        center=[0, 0], radius=500.0,
        start_angle_deg=0.0, end_angle_deg=90.0, max_chord_error=0.5,
    )
    recipe = plan_profile_sweep(
        profile=tall_rect, path=arc["points"],
        max_path_deviation=0.5,
        observed_path_deviation=arc["max_chord_error_bound"],
    )
    fixtures.append(_fixture(
        "curved-rect-sweep", "plan_profile_sweep",
        {"profile": tall_rect,
         "arc": {"center": [0, 0], "radius": 500.0,
                 "start_angle_deg": 0.0, "end_angle_deg": 90.0,
                 "max_chord_error": 0.5}},
        # Curved-sweep volume is tessellation-dependent: no exact analytic
        # expectation, so the oracle must report unknown (fail-closed).
        recipe, None,
    ))

    halves = [10.0, 8.0, 6.0, 4.0]
    heights = [0.0, 30.0, 60.0, 100.0]
    sections = [
        [[-h, -h, z], [h, -h, z], [h, h, z], [-h, h, z]]
        for h, z in zip(halves, heights)
    ]
    recipe = plan_loft_mesh(sections)
    areas = [(2.0 * h) ** 2 for h in halves]
    volume = sum(
        _frustum_volume(areas[i], areas[i + 1], heights[i + 1] - heights[i])
        for i in range(3)
    )
    fixtures.append(_fixture(
        "four-section-loft", "plan_loft_mesh",
        {"sections": sections}, recipe, volume,
    ))

    for fixture in fixtures:
        path = FIXTURE_DIR / f"{fixture['case_id']}.json"
        path.write_text(json.dumps(fixture, indent=2), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} "
              f"verts={fixture['recipe']['vertex_count']} "
              f"faces={fixture['recipe']['face_count']} "
              f"volume={fixture['expected']['expected_volume']}")


if __name__ == "__main__":
    main()
