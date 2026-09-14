"""Regression coverage for 2026-09-14 CDT_Engineer gap closure."""
from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from domains.building_architecture.guards import validate_casework_input_package
from domains.building_architecture.geometry_planner import (
    GeometryPlanError,
    MeshBudget,
    plan_loft_mesh,
    plan_profile_sweep,
    sample_circular_arc,
)

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "domains" / "building-architecture" / "skills" / "interior-casework-layout"


def ev(value, *, status="specified", source_ref="drawing-A3", approved_by=None):
    return {
        "status": status,
        "value": value,
        "source_ref": source_ref,
        "approved_by": approved_by,
    }


def valid_payload():
    return {
        "schema_version": "0.2.0",
        "system_id": "kitchen-01",
        "units": "mm",
        "release_target": "design_review",
        "source_refs": ["drawing-A3", "manufacturer-drawer"],
        "modules": [
            {
                "id": "base-01",
                "kind": "base_cabinet",
                "geometry": {
                    "type": "box",
                    "width": ev(900),
                    "height": ev(720),
                    "depth": ev(600),
                },
                "panels": {
                    "left": ev(18),
                    "right": ev(18),
                    "top": ev(18),
                    "bottom": ev(18),
                    "back": ev(9),
                },
                "component_resolution": "custom_allowed",
                "component_id": None,
            }
        ],
        "equipment": [
            {
                "id": "drawer-01",
                "kind": "drawer",
                "envelope": {
                    "width": ev(580, source_ref="manufacturer-drawer"),
                    "height": ev(680, source_ref="manufacturer-drawer"),
                    "depth": ev(560, source_ref="manufacturer-drawer"),
                },
                "clearances": {
                    "left": ev(5, source_ref="manufacturer-drawer"),
                    "right": ev(5, source_ref="manufacturer-drawer"),
                    "top": ev(5, source_ref="manufacturer-drawer"),
                    "bottom": ev(5, source_ref="manufacturer-drawer"),
                    "front": ev(0, source_ref="manufacturer-drawer"),
                    "back": ev(10, source_ref="manufacturer-drawer"),
                },
                "component_resolution": "custom_allowed",
                "component_id": None,
            }
        ],
    }


class InteriorInputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((SKILL / "inputs.schema.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)

    def assertValid(self, payload):
        self.assertEqual([], list(self.validator.iter_errors(payload)))

    def assertInvalid(self, payload):
        self.assertTrue(list(self.validator.iter_errors(payload)))

    def test_valid_package_uses_field_level_evidence(self):
        payload = valid_payload()
        self.assertValid(payload)
        result = validate_casework_input_package(payload)
        self.assertEqual("pass", result["result"])

    def test_resolved_component_requires_component_identity(self):
        payload = valid_payload()
        payload["modules"][0]["component_resolution"] = "resolved"
        payload["modules"][0]["component_id"] = None
        self.assertInvalid(payload)

    def test_duplicate_semantic_ids_fail_closed(self):
        payload = valid_payload()
        duplicate = copy.deepcopy(payload["modules"][0])
        duplicate["kind"] = "wall_cabinet"
        payload["modules"].append(duplicate)
        self.assertValid(payload)
        result = validate_casework_input_package(payload)
        self.assertEqual("blocked", result["result"])
        self.assertIn("duplicate_semantic_id:base-01", result["reason_codes"])

    def test_inferred_exact_dimension_cannot_support_design_review(self):
        payload = valid_payload()
        payload["modules"][0]["geometry"]["width"] = ev(900, status="inferred")
        self.assertValid(payload)
        result = validate_casework_input_package(payload)
        self.assertEqual("blocked", result["result"])
        self.assertIn("evidence_state_exceeds_release:base-01.geometry.width:inferred:concept", result["reason_codes"])

    def test_unknown_critical_dimension_cannot_carry_exact_value(self):
        payload = valid_payload()
        payload["modules"][0]["geometry"]["width"] = ev(900, status="unknown", source_ref=None)
        self.assertInvalid(payload)

    def test_field_source_ref_must_be_declared_in_package_sources(self):
        payload = valid_payload()
        payload["modules"][0]["geometry"]["width"] = ev(900, source_ref="undeclared-source")
        self.assertValid(payload)
        result = validate_casework_input_package(payload)
        self.assertEqual("blocked", result["result"])
        self.assertIn("evidence_source_not_declared:base-01.geometry.width:undeclared-source", result["reason_codes"])

    def test_proxy_metadata_is_required_and_ceiling_is_enforced(self):
        payload = valid_payload()
        module = payload["modules"][0]
        module["component_resolution"] = "proxy_allowed_for_scope"
        self.assertInvalid(payload)
        module["proxy"] = {
            "maximum_release": "concept",
            "reason": "native family unavailable",
            "unresolved_dependency": "catalog.casework-panel",
            "replacement_required_before": "technical_draft",
        }
        self.assertValid(payload)
        result = validate_casework_input_package(payload)
        self.assertEqual("blocked", result["result"])
        self.assertIn("proxy_not_valid_for_release:base-01:concept", result["reason_codes"])


class ComplexGeometryPlannerTests(unittest.TestCase):
    def test_tapered_loft_produces_bounded_indexed_mesh(self):
        sections = [
            [[-10, -10, 0], [10, -10, 0], [10, 10, 0], [-10, 10, 0]],
            [[-5, -5, 100], [5, -5, 100], [5, 5, 100], [-5, 5, 100]],
        ]
        plan = plan_loft_mesh(sections)
        self.assertEqual(8, plan["vertex_count"])
        self.assertEqual(8, plan["face_count"])
        self.assertEqual("indexed_mesh", plan["representation"])
        self.assertEqual(1, len(plan["chunks"]))

    def test_curved_profile_sweep_respects_declared_chord_error(self):
        path = sample_circular_arc(
            center=[0, 0],
            radius=500,
            start_angle_deg=0,
            end_angle_deg=90,
            max_chord_error=0.5,
        )
        plan = plan_profile_sweep(
            profile=[[0, 0], [20, 0], [20, 40], [0, 40]],
            path=path["points"],
            max_path_deviation=0.5,
            observed_path_deviation=path["max_chord_error_bound"],
        )
        self.assertLessEqual(plan["max_path_deviation_observed"], 0.5)
        self.assertTrue(plan["manifold_expected"])
        self.assertLessEqual(plan["vertex_count"], MeshBudget().max_vertices)
        self.assertLessEqual(plan["face_count"], MeshBudget().max_faces)

    def test_straight_profile_sweep_is_supported(self):
        plan = plan_profile_sweep(
            profile=[[0, 0], [10, 0], [10, 20], [0, 20]],
            path=[[0, 0], [100, 0]],
            max_path_deviation=0.0,
            observed_path_deviation=0.0,
        )
        self.assertEqual(8, plan["vertex_count"])
        self.assertEqual(8, plan["face_count"])

    def test_self_intersecting_profile_is_rejected(self):
        with self.assertRaisesRegex(GeometryPlanError, "self-intersecting"):
            plan_profile_sweep(
                profile=[[0, 0], [10, 10], [0, 10], [10, 0]],
                path=[[0, 0], [100, 0]],
                max_path_deviation=0.0,
                observed_path_deviation=0.0,
            )

    def test_budget_overflow_is_typed_blocker(self):
        path = [[float(i), 0.0] for i in range(600)]
        with self.assertRaisesRegex(GeometryPlanError, "mesh budget exceeded"):
            plan_profile_sweep(
                profile=[[0, 0], [1, 0], [1, 1], [0, 1]],
                path=path,
                max_path_deviation=0.0,
                observed_path_deviation=0.0,
            )

    def test_deviation_above_allowance_is_rejected(self):
        with self.assertRaisesRegex(GeometryPlanError, "path deviation exceeds allowance"):
            plan_profile_sweep(
                profile=[[0, 0], [10, 0], [10, 20], [0, 20]],
                path=[[0, 0], [100, 0]],
                max_path_deviation=0.25,
                observed_path_deviation=0.5,
            )


if __name__ == "__main__":
    unittest.main()
