"""Tests for the deterministic PlanSpec revise loop (gates -> fix -> re-validate).
Wing: code | Topic: plan-revise-loop | Updated: 2026-09-18 04:00
"""
from __future__ import annotations

import unittest
from execution.plan_revise import revise_plan_spec


def _arch_spec(plan_id="revise_case"):
    return {
        "schema_version": "0.1.0",
        "plan_id": plan_id,
        "domain_id": "building-architecture",
        "plan_type": "architectural_floor_plan",
        "units": {"length": "mm", "angle": "deg"},
        "coordinate_system": {
            "datum": "project_local_origin", "origin": [0.0, 0.0],
            "azimuth": 0.0, "scale": {"horizontal": 1.0, "vertical": 1.0},
        },
        "provenance_ledger": {
            "axis_A": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            "axis_1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            "wall_w1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            "wall_w2": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            "door_d1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
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
    }


def _xs_spec(plan_id="revise_xs"):
    return {
        "schema_version": "0.1.0",
        "plan_id": plan_id,
        "domain_id": "civil-road-infrastructure",
        "plan_type": "civil_road_cross_section",
        "units": {"length": "m", "angle": "deg", "station": "m"},
        "coordinate_system": {
            "datum": "xs_datum", "origin": [0.0, 10.0],
            "scale": {"horizontal": 100.0, "vertical": 100.0},
        },
        "provenance_ledger": {
            "carriageway": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            "layer_a": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            "layer_b": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
        },
        "assumptions": [],
        "payload": {
            "alignment_ref": "tuyen_chinh",
            "station": 50.0,
            "elevation_datum": 10.0,
            "carriageway": {"width_left": 3.5, "width_right": 3.5,
                            "cross_slope_left_percent": -2.0, "cross_slope_right_percent": -2.0},
            "pavement_structure": [
                {"layer_id": "layer_a", "name": "BTN", "material": "asphalt", "thickness": 0.05, "order": 1},
                {"layer_id": "layer_b", "name": "CPDD", "material": "stone", "thickness": 0.15, "order": 3},
            ],
        },
    }


_DIM_AUTH = {"dim_01": {"action": "recompute_dimension_from_witness", "evidence_ref": "review-1"}}
_PAVEMENT_AUTH = {"pavement_structure": {"action": "renumber_pavement_order", "evidence_ref": "review-2"}}


class TestPlanReviseLoop(unittest.TestCase):
    def test_dimension_mismatch_auto_fixed_and_approved(self):
        spec = _arch_spec("revise_dim")
        spec["payload"]["dimensions"][0]["measured_value"] = 4800.0
        res = revise_plan_spec(spec, repair_authorizations=_DIM_AUTH)
        self.assertTrue(res.approved)
        self.assertEqual(res.verdict, "REVISED_APPROVED")
        self.assertEqual(res.rounds, 1)
        self.assertEqual(len(res.applied_repairs), 1)
        repair = res.applied_repairs[0]
        self.assertEqual(repair["feature_id"], "dim_01")
        self.assertEqual(repair["old_value"], 4800.0)
        self.assertEqual(repair["new_value"], 5000.0)
        self.assertEqual(repair["authorization_evidence_ref"], "review-1")
        self.assertEqual(res.proposals, [])
        # Input mapping untouched; fix lives in the returned spec.
        self.assertEqual(spec["payload"]["dimensions"][0]["measured_value"], 4800.0)
        self.assertEqual(res.spec["payload"]["dimensions"][0]["measured_value"], 5000.0)

    def test_orphan_wall_needs_manual_with_proposal(self):
        spec = _arch_spec("revise_orphan")
        spec["payload"]["walls"].append(
            {"wall_id": "wall_orphan", "wall_type": "partition", "thickness": 110.0,
             "start": [20000.0, 20000.0], "end": [22000.0, 20000.0],
             "baseline": "center", "height": 2700.0},
        )
        spec["provenance_ledger"]["wall_orphan"] = {
            "status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0,
        }
        res = revise_plan_spec(spec, repair_authorizations=_DIM_AUTH)
        self.assertFalse(res.approved)
        self.assertEqual(res.verdict, "NEEDS_MANUAL_DECISION")
        self.assertEqual(res.applied_repairs, [])
        reasons = [p["reason"] for p in res.proposals]
        self.assertIn("orphan_wall:wall_orphan", reasons)
        proposal = next(p for p in res.proposals if p["reason"] == "orphan_wall:wall_orphan")
        self.assertFalse(proposal["auto_fixable"])
        self.assertTrue(proposal["suggestion"])

    def test_pavement_order_renumbered_and_approved(self):
        res = revise_plan_spec(_xs_spec(), repair_authorizations=_PAVEMENT_AUTH)
        self.assertTrue(res.approved, f"proposals: {res.proposals}")
        self.assertEqual(res.rounds, 1)
        orders = [ly["order"] for ly in res.spec["payload"]["pavement_structure"]]
        self.assertEqual(sorted(orders), [1, 2])

    def test_mixed_fixable_and_manual_applies_fix_then_asks(self):
        spec = _arch_spec("revise_mixed")
        spec["payload"]["dimensions"][0]["measured_value"] = 4800.0
        spec["payload"]["walls"].append(
            {"wall_id": "wall_orphan", "wall_type": "partition", "thickness": 110.0,
             "start": [20000.0, 20000.0], "end": [22000.0, 20000.0],
             "baseline": "center", "height": 2700.0},
        )
        spec["provenance_ledger"]["wall_orphan"] = {
            "status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0,
        }
        res = revise_plan_spec(spec, repair_authorizations=_DIM_AUTH)
        self.assertFalse(res.approved)
        self.assertEqual(res.rounds, 1)
        self.assertEqual([r["feature_id"] for r in res.applied_repairs], ["dim_01"])
        self.assertTrue(any(p["reason"] == "orphan_wall:wall_orphan" for p in res.proposals))
        self.assertFalse(any("dimension_witness_mismatch" in p["reason"] for p in res.proposals))

    def test_already_valid_spec_approved_without_rounds(self):
        res = revise_plan_spec(_arch_spec("revise_clean"))
        self.assertTrue(res.approved)
        self.assertEqual(res.rounds, 0)
        self.assertEqual(res.applied_repairs, [])
        self.assertEqual(res.proposals, [])

    def test_rounds_bounded(self):
        spec = _arch_spec("revise_bounded")
        spec["payload"]["dimensions"][0]["measured_value"] = 4800.0
        spec["payload"]["walls"].append(
            {"wall_id": "wall_orphan", "wall_type": "partition", "thickness": 110.0,
             "start": [20000.0, 20000.0], "end": [22000.0, 20000.0],
             "baseline": "center", "height": 2700.0},
        )
        spec["provenance_ledger"]["wall_orphan"] = {
            "status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0,
        }
        res = revise_plan_spec(spec, max_rounds=1, repair_authorizations=_DIM_AUTH)
        self.assertFalse(res.approved)
        self.assertLessEqual(res.rounds, 1)

    def test_dimension_without_authority_is_not_rewritten(self):
        spec = _arch_spec()
        spec["payload"]["dimensions"][0]["measured_value"] = 4800.0
        result = revise_plan_spec(spec)
        self.assertFalse(result.approved)
        self.assertEqual(result.applied_repairs, [])
        self.assertEqual(result.spec["payload"]["dimensions"][0]["measured_value"], 4800.0)
        self.assertFalse(result.proposals[0]["auto_fixable"])

    def test_specified_dimension_is_not_replaced_by_geometry(self):
        spec = _arch_spec()
        spec["payload"]["dimensions"][0]["measured_value"] = 4800.0
        spec["provenance_ledger"]["dim_01"]["status"] = "specified"
        result = revise_plan_spec(spec, repair_authorizations={
            "dim_01": {"action": "recompute_dimension_from_witness", "evidence_ref": "review-1"},
        })
        self.assertFalse(result.approved)
        self.assertEqual(result.applied_repairs, [])
        self.assertEqual(result.spec["payload"]["dimensions"][0]["measured_value"], 4800.0)

    def test_pavement_without_authority_is_not_renumbered(self):
        result = revise_plan_spec(_xs_spec())
        self.assertFalse(result.approved)
        self.assertEqual(result.applied_repairs, [])
        self.assertEqual([x["order"] for x in result.spec["payload"]["pavement_structure"]], [1, 3])

    def test_malformed_authority_never_changes_dimension(self):
        for authorization in (None, {}, False,
                              {"action": "other", "evidence_ref": "review-1"},
                              {"action": "recompute_dimension_from_witness", "evidence_ref": " "}):
            with self.subTest(authorization=authorization):
                spec = _arch_spec()
                spec["payload"]["dimensions"][0]["measured_value"] = 4800.0
                result = revise_plan_spec(spec, repair_authorizations={"dim_01": authorization})
                self.assertFalse(result.approved)
                self.assertEqual(result.spec, spec)
                self.assertEqual(result.applied_repairs, [])

    def test_invalid_max_rounds_rejected(self):
        with self.assertRaises(ValueError):
            revise_plan_spec(_arch_spec(), max_rounds=0)


if __name__ == "__main__":
    unittest.main()
