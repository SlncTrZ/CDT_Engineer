"""Tests for deterministic pre-CAD professional review gates (ENG-R08).
Wing: code | Topic: plan-review-gates | Updated: 2026-09-18 00:05
"""
from __future__ import annotations

import unittest
from execution.plan_review import review_plan_spec


def _base_envelope(plan_id="review_case_01", plan_type="architectural_floor_plan"):
    return {
        "schema_version": "0.1.0",
        "plan_id": plan_id,
        "domain_id": "building-architecture",
        "plan_type": plan_type,
        "units": {"length": "mm", "angle": "deg"},
        "coordinate_system": {
            "datum": "project_local_origin",
            "origin": [0.0, 0.0],
            "azimuth": 0.0,
            "scale": {"horizontal": 1.0, "vertical": 1.0},
        },
    }


def _valid_arch_spec(plan_id="arch_review_ok"):
    spec = _base_envelope(plan_id)
    spec.update({
        "provenance_ledger": {
            "axis_A": {"status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0},
            "axis_1": {"status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0},
            "wall_w1": {"status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0},
            "wall_w2": {"status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0},
            "door_d1": {"status": "specified", "source_id": "spec_sheet_01", "assumption_id": None, "confidence": 1.0},
            "space_living": {"status": "derived", "source_id": None, "assumption_id": None, "confidence": 0.95},
            "dim_01": {"status": "derived", "source_id": None, "assumption_id": None, "confidence": 1.0},
        },
        "assumptions": [],
        "payload": {
            "axes": [
                {"axis_id": "axis_A", "label": "A", "start": [0.0, 0.0], "end": [5000.0, 0.0]},
                {"axis_id": "axis_1", "label": "1", "start": [0.0, 0.0], "end": [0.0, 4000.0]},
            ],
            "walls": [
                {"wall_id": "wall_w1", "wall_type": "exterior", "thickness": 220.0,
                 "start": [0.0, 0.0], "end": [5000.0, 0.0], "baseline": "center", "height": 3300.0},
                {"wall_id": "wall_w2", "wall_type": "exterior", "thickness": 220.0,
                 "start": [5000.0, 0.0], "end": [5000.0, 4000.0], "baseline": "center", "height": 3300.0},
            ],
            "openings": [
                {"opening_id": "door_d1", "host_wall_id": "wall_w1", "opening_type": "door",
                 "offset_along_wall": 1000.0, "width": 900.0, "height": 2200.0,
                 "sill_height": 0.0, "head_height": 2200.0},
            ],
            "spaces": [
                {"space_id": "space_living", "name": "Living Room",
                 "boundary_polygon": [[0.0, 0.0], [5000.0, 0.0], [5000.0, 4000.0], [0.0, 4000.0]],
                 "net_area": 20.0},
            ],
            "dimensions": [
                {"dimension_id": "dim_01", "dimension_type": "linear", "measured_value": 5000.0,
                 "witness_points": [[0.0, 0.0], [5000.0, 0.0]], "feature_refs": ["wall_w1"]},
            ],
        },
    })
    return spec


def _valid_profile_spec(plan_id="profile_review_ok"):
    spec = _base_envelope(plan_id, "civil_road_profile")
    spec["domain_id"] = "civil-road-infrastructure"
    spec["units"] = {"length": "m", "angle": "deg", "station": "m"}
    spec["coordinate_system"] = {
        "datum": "VN2000_Zone3",
        "origin": [500000.0, 2300000.0, 0.0],
        "scale": {"horizontal": 1000.0, "vertical": 100.0},
    }
    spec.update({
        "provenance_ledger": {
            "ground_pt_0": {"status": "observed", "source_id": "topo_2026", "assumption_id": None, "confidence": 1.0},
            "ground_pt_1": {"status": "observed", "source_id": "topo_2026", "assumption_id": None, "confidence": 1.0},
            "pvi_0": {"status": "specified", "source_id": "prelim_design", "assumption_id": None, "confidence": 1.0},
            "pvi_1": {"status": "specified", "source_id": "prelim_design", "assumption_id": None, "confidence": 1.0},
        },
        "assumptions": [],
        "payload": {
            "alignment_ref": "tuyen_chinh",
            "ground_line": [
                {"station": 0.0, "elevation": 12.50},
                {"station": 100.0, "elevation": 13.20},
            ],
            "grade_line": [
                {"station": 0.0, "elevation": 13.00, "grade_in_percent": 1.0, "grade_out_percent": 1.0},
                {"station": 100.0, "elevation": 14.00, "grade_in_percent": 1.0,
                 "curve_radius": 2000.0, "curve_length": 40.0},
            ],
        },
    })
    return spec


def _finding(result, finding_id):
    for f in result.findings:
        if f["finding_id"] == finding_id:
            return f
    return None


class TestPlanReviewGates(unittest.TestCase):
    def test_valid_arch_plan_approved(self):
        res = review_plan_spec(_valid_arch_spec())
        self.assertEqual(res.verdict, "APPROVED_FOR_EXECUTION", f"findings: {[f for f in res.findings if f['result'] == 'fail']}")
        self.assertTrue(res.approved)

    def test_missing_axes_grid_rejected(self):
        spec = _valid_arch_spec("arch_no_axes")
        spec["payload"]["axes"] = []
        for aid in ("axis_A", "axis_1"):
            del spec["provenance_ledger"][aid]
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G1-axes_datum")
        self.assertIsNotNone(f)
        self.assertEqual(f["result"], "fail")
        self.assertIn("missing_axes_grid", f["reason_codes"])

    def test_dimension_witness_mismatch_rejected(self):
        spec = _valid_arch_spec("arch_bad_dim")
        spec["payload"]["dimensions"][0]["measured_value"] = 4800.0  # witnesses span 5000
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G2-dimensional_consistency")
        self.assertIsNotNone(f)
        self.assertIn("dimension_witness_mismatch:dim_01", f["reason_codes"])

    def test_self_intersecting_space_rejected(self):
        spec = _valid_arch_spec("arch_bowtie_space")
        # Crossed quad with unequal lobes: nonzero shoelace area (passes G0)
        # but self-intersecting edges (must fail G3, not G0).
        spec["payload"]["spaces"][0]["boundary_polygon"] = [
            [0.0, 0.0], [5000.0, 3000.0], [4000.0, 0.0], [1000.0, 4000.0],
        ]
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G3-room_topology")
        self.assertIsNotNone(f)
        self.assertIn("self_intersecting_boundary:space_living", f["reason_codes"])

    def test_orphan_wall_endpoint_rejected(self):
        spec = _valid_arch_spec("arch_orphan_wall")
        spec["payload"]["walls"].append(
            {"wall_id": "wall_orphan", "wall_type": "partition", "thickness": 110.0,
             "start": [20000.0, 20000.0], "end": [22000.0, 20000.0], "baseline": "center", "height": 2700.0},
        )
        spec["provenance_ledger"]["wall_orphan"] = {
            "status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0,
        }
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G5-wall_joins")
        self.assertIsNotNone(f)
        self.assertTrue(any(r.startswith("orphan_wall:wall_orphan") for r in f["reason_codes"]))

    def test_unjoined_tee_rejected(self):
        spec = _valid_arch_spec("arch_tee_wall")
        # Tee branch lands mid-span of wall_w1 (y=0), not at its endpoints.
        spec["payload"]["walls"].append(
            {"wall_id": "wall_tee", "wall_type": "partition", "thickness": 110.0,
             "start": [2500.0, 0.0], "end": [2500.0, 2000.0], "baseline": "center", "height": 2700.0},
        )
        spec["provenance_ledger"]["wall_tee"] = {
            "status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0,
        }
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G5-wall_joins")
        self.assertIsNotNone(f)
        self.assertTrue(any(r.startswith("unjoined_tee:wall_tee:start") for r in f["reason_codes"]))

    def test_narrow_door_below_egress_rejected(self):
        spec = _valid_arch_spec("arch_narrow_door")
        spec["payload"]["openings"][0]["width"] = 600.0
        res = review_plan_spec(spec, requirements={"min_door_width": 800.0})
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G4-opening_placement")
        self.assertIsNotNone(f)
        self.assertIn("door_below_minimum_width:door_d1", f["reason_codes"])

    def test_inferred_provenance_blocks_design_review_only(self):
        spec = _valid_arch_spec("arch_inferred_prov")
        spec["provenance_ledger"]["wall_w2"] = {
            "status": "inferred", "source_id": None, "assumption_id": None, "confidence": 0.4,
        }
        res_concept = review_plan_spec(spec, requirements={"release_target": "concept"})
        self.assertEqual(res_concept.verdict, "APPROVED_FOR_EXECUTION")
        res_design = review_plan_spec(spec, requirements={"release_target": "design_review"})
        self.assertEqual(res_design.verdict, "REJECTED")
        f = _finding(res_design, "R08-G7-provenance_quality")
        self.assertIsNotNone(f)
        self.assertIn("low_provenance_blocks_release:wall_w2", f["reason_codes"])

    def test_civil_grade_declaration_mismatch_rejected(self):
        spec = _valid_profile_spec("profile_bad_grade")
        # Declared 1% but geometry implies (14.00-13.00)/100 = 1%... break it:
        spec["payload"]["grade_line"][1]["elevation"] = 16.00  # implies 3%, declared 1%
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G8-profile_grade")
        self.assertIsNotNone(f)
        self.assertTrue(any(r.startswith("grade_declaration_mismatch") for r in f["reason_codes"]))

    def test_civil_cross_section_layer_order_gap_rejected(self):
        spec = _base_envelope("xs_bad_order", "civil_road_cross_section")
        spec["domain_id"] = "civil-road-infrastructure"
        spec["units"] = {"length": "m", "angle": "deg", "station": "m"}
        spec["coordinate_system"] = {
            "datum": "xs_datum", "origin": [0.0, 10.0], "scale": {"horizontal": 100.0, "vertical": 100.0},
        }
        spec.update({
            "provenance_ledger": {
                "carriageway": {"status": "specified", "source_id": "tcvn_4054", "assumption_id": None, "confidence": 1.0},
                "layer_a": {"status": "specified", "source_id": "spec", "assumption_id": None, "confidence": 1.0},
                "layer_b": {"status": "specified", "source_id": "spec", "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [],
            "payload": {
                "alignment_ref": "tuyen_chinh",
                "station": 50.0,
                "elevation_datum": 10.0,
                "carriageway": {"width_left": 3.5, "width_right": 3.5,
                                "cross_slope_left_percent": -2.0, "cross_slope_right_percent": -2.0},
                "pavement_structure": [
                    {"layer_id": "layer_a", "name": "BTN C12.5", "material": "asphalt_c12_5", "thickness": 0.05, "order": 1},
                    {"layer_id": "layer_b", "name": "CPDD 1", "material": "crushed_stone_1", "thickness": 0.15, "order": 3},
                ],
            },
        })
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G9-cross_section")
        self.assertIsNotNone(f)
        self.assertTrue(any(r.startswith("pavement_order_not_sequential") for r in f["reason_codes"]))

    def test_invalid_planspec_rejected_at_gate_zero(self):
        spec = _valid_arch_spec("arch_invalid_g0")
        # Break PlanSpec validity: opening longer than host wall
        spec["payload"]["openings"][0]["offset_along_wall"] = 4500.0
        spec["payload"]["openings"][0]["width"] = 900.0  # 5400 > 5000 wall
        res = review_plan_spec(spec)
        self.assertEqual(res.verdict, "REJECTED")
        f = _finding(res, "R08-G0-planspec_valid")
        self.assertIsNotNone(f)
        self.assertEqual(f["result"], "fail")


if __name__ == "__main__":
    unittest.main()
