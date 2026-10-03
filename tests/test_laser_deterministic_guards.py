"""Tests for Laser 2D-to-3D Assembly deterministic guards (LASER-01..06).
Wing: code | Topic: laser-guards-test | Updated: 2026-10-03
"""
from __future__ import annotations

import unittest

from domains.guard_primitives import GuardInputError
from domains.laser_2d3d_assembly.guards import (
    evaluate_cross_slot_dfm,
    evaluate_cut_contour,
    evaluate_material_intake,
    evaluate_nesting_layout,
    evaluate_slice_step,
)


class LaserDeterministicGuardsTests(unittest.TestCase):
    def test_material_intake_blocks_unknown_for_technical_draft(self) -> None:
        unknown_spec = {
            "material_id": "SUS304",
            "thickness_mm": None,
            "kerf_mm": None,
            "slot_clearance_mm": None,
            "status": "unknown",
        }
        res = evaluate_material_intake(unknown_spec, release_target="technical_draft")
        self.assertEqual("blocked", res["result"])
        self.assertIn("unknown_material_triple", res["reason_codes"])

        # Concept allows proxy
        concept_res = evaluate_material_intake(unknown_spec, release_target="concept")
        self.assertEqual("pass", concept_res["result"])
        self.assertEqual("concept_proxy", concept_res["mode"])

    def test_material_intake_passes_valid_specified_spec(self) -> None:
        valid_spec = {
            "material_id": "SUS304",
            "thickness_mm": 2.0,
            "kerf_mm": 0.15,
            "slot_clearance_mm": 0.1,
            "status": "specified",
        }
        res = evaluate_material_intake(valid_spec, release_target="technical_draft")
        self.assertEqual("pass", res["result"])
        self.assertEqual(2.0, res["thickness_mm"])

    def test_cross_slot_dfm_enforces_clearance_and_depth_limits(self) -> None:
        mat = {
            "material_id": "Plywood",
            "thickness_mm": 5.0,
            "kerf_mm": 0.2,
            "slot_clearance_mm": 0.2,
            "status": "specified",
        }
        # Good slot: width = 5.0 + 0.2 + 0.25 = 5.45, depth = 20mm on 50mm part
        good_slot = {
            "slot_width": 5.45,
            "slot_depth": 25.0,
            "local_part_width": 50.0,
            "mating_slot_id": "slot_b1",
        }
        self.assertEqual("pass", evaluate_cross_slot_dfm(good_slot, mat)["result"])

        # Insufficient clearance
        tight_slot = dict(good_slot, slot_width=5.1)
        res = evaluate_cross_slot_dfm(tight_slot, mat)
        self.assertEqual("fail", res["result"])
        self.assertIn("insufficient_slot_clearance", res["reason_codes"])

        # Blind slot overcut (severing the part)
        sever_slot = dict(good_slot, slot_depth=50.0)
        res = evaluate_cross_slot_dfm(sever_slot, mat)
        self.assertEqual("fail", res["result"])
        self.assertIn("blind_slot_overcut", res["reason_codes"])

    def test_cut_contour_validates_closed_loop_and_geometry(self) -> None:
        # Valid rectangle
        rect = [[0, 0], [100, 0], [100, 50], [0, 50]]
        res = evaluate_cut_contour(rect)
        self.assertEqual("pass", res["result"])
        self.assertEqual(5000.0, res["contour_area_mm2"])

        # Self-intersecting bowtie
        bowtie = [[0, 0], [100, 100], [0, 100], [100, 0]]
        res = evaluate_cut_contour(bowtie)
        self.assertEqual("fail", res["result"])
        self.assertIn("self_intersecting_contour", res["reason_codes"])

        # Zero length edge
        degenerate = [[0, 0], [0, 0], [100, 0], [0, 50]]
        res = evaluate_cut_contour(degenerate)
        self.assertEqual("fail", res["result"])
        self.assertIn("zero_length_edge", res["reason_codes"])

    def test_slice_step_validates_layer_thickness_and_alignment(self) -> None:
        mat = {
            "material_id": "MDF",
            "thickness_mm": 3.0,
            "kerf_mm": 0.15,
            "slot_clearance_mm": 0.1,
            "status": "specified",
        }
        slices = [
            {"slice_index": 0, "elevation_z": 0.0, "alignment_features": ["pin_1", "pin_2"]},
            {"slice_index": 1, "elevation_z": 3.0, "alignment_features": ["pin_1", "pin_2"]},
            {"slice_index": 2, "elevation_z": 6.0, "alignment_features": ["pin_1", "pin_2"]},
        ]
        self.assertEqual("pass", evaluate_slice_step(slices, mat)["result"])

        # Step mismatch
        bad_slices = [
            {"slice_index": 0, "elevation_z": 0.0, "alignment_features": ["pin_1"]},
            {"slice_index": 1, "elevation_z": 4.5, "alignment_features": ["pin_1"]},
        ]
        res = evaluate_slice_step(bad_slices, mat)
        self.assertEqual("fail", res["result"])
        self.assertIn("slice_step_mismatch:0", res["reason_codes"])

    def test_nesting_layout_detects_bed_overflow(self) -> None:
        bed = [600.0, 400.0]
        # Fits with margin 5mm
        fits = [580.0, 380.0]
        self.assertEqual("pass", evaluate_nesting_layout(fits, bed, margin_mm=5.0)["result"])

        # Fits rotated (380 x 580 on 600 x 400 bed)
        fits_rot = [380.0, 580.0]
        self.assertEqual("pass", evaluate_nesting_layout(fits_rot, bed, margin_mm=5.0)["result"])

        # Overflow
        too_big = [650.0, 400.0]
        res = evaluate_nesting_layout(too_big, bed, margin_mm=5.0)
        self.assertEqual("fail", res["result"])
        self.assertIn("over_bed_layout", res["reason_codes"])


if __name__ == "__main__":
    unittest.main()
