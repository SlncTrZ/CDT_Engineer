"""Tests for reference-source interpretation and calibration (ENG-R06).
Wing: code | Topic: source-calibration | Updated: 2026-09-18 00:50
"""
from __future__ import annotations

import unittest
from execution.source_calibration import calibrate_plan_source


def _image_frame():
    from PIL import Image
    with Image.open("_test_workspace/references/Test6_House_3_Floors_Layout.jpg") as im:
        width, height = im.size
    return {
        "source_id": "test6_house_3_floors",
        "kind": "reference_image",
        "pixel_width": width,
        "pixel_height": height,
    }


def _width_anchor(pixel_width, real_length=15000.0, confidence=0.9):
    return {
        "anchor_id": "anchor_total_width",
        "statement": "Toan bo chieu ngang mat bang = 15 000 mm (owner assumption)",
        "pixel_from": [0.0, 0.0],
        "pixel_to": [float(pixel_width), 0.0],
        "real_length": real_length,
        "unit": "mm",
        "confidence": confidence,
    }


class TestSourceCalibration(unittest.TestCase):
    def test_single_anchor_scale_from_real_reference(self):
        source = _image_frame()
        self.assertEqual((source["pixel_width"], source["pixel_height"]), (1200, 1600))
        res = calibrate_plan_source(
            source=source, pixel_features=[], anchors=[_width_anchor(1200)],
        )
        self.assertEqual(res.verdict, "CALIBRATED")
        # 15 000 mm over 1200 px -> 12.5 mm/px. Anchor is assumption, not truth.
        self.assertAlmostEqual(res.frame["scale_unit_per_pixel"], 12.5, places=9)
        self.assertEqual(res.frame["unit"], "mm")
        anchor_entry = res.provenance_ledger["anchor_total_width"]
        self.assertEqual(anchor_entry["status"], "approved_assumption")

    def test_pixel_to_mm_transform_with_y_flip(self):
        source = _image_frame()
        res = calibrate_plan_source(
            source=source,
            pixel_features=[
                {"feature_id": "wall_probe_a", "kind": "point", "pixels": [0.0, 0.0]},
                {"feature_id": "wall_probe_b", "kind": "point", "pixels": [1200.0, 1600.0]},
            ],
            anchors=[_width_anchor(1200)],
        )
        self.assertEqual(res.verdict, "CALIBRATED")
        by_id = {f["feature_id"]: f for f in res.features}
        # Origin pixel maps to (0, H*s); opposite corner to (W*s, 0): y-up frame.
        self.assertEqual(by_id["wall_probe_a"]["coords_mm"], [0.0, 1600.0 * 12.5])
        self.assertEqual(by_id["wall_probe_b"]["coords_mm"], [1200.0 * 12.5, 0.0])
        self.assertEqual(by_id["wall_probe_a"]["provenance"], "derived")

    def test_two_consistent_anchors_agree(self):
        source = _image_frame()
        anchors = [
            _width_anchor(1200, real_length=15000.0),
            {"anchor_id": "anchor_half_width", "statement": "Half width check",
             "pixel_from": [0.0, 0.0], "pixel_to": [600.0, 0.0],
             "real_length": 7500.0, "unit": "mm", "confidence": 0.9},
        ]
        res = calibrate_plan_source(source=source, pixel_features=[], anchors=anchors)
        self.assertEqual(res.verdict, "CALIBRATED")
        self.assertAlmostEqual(res.frame["scale_unit_per_pixel"], 12.5, places=9)
        self.assertAlmostEqual(res.scale_disagreement_rel, 0.0, places=9)

    def test_contradictory_anchors_rejected(self):
        source = _image_frame()
        anchors = [
            _width_anchor(1200, real_length=15000.0),
            {"anchor_id": "anchor_conflict", "statement": "Conflicting width claim",
             "pixel_from": [0.0, 0.0], "pixel_to": [1200.0, 0.0],
             "real_length": 16000.0, "unit": "mm", "confidence": 0.9},
        ]
        res = calibrate_plan_source(source=source, pixel_features=[], anchors=anchors)
        self.assertEqual(res.verdict, "CONTRADICTORY")
        self.assertTrue(any("anchor_scale_contradiction" in e for e in res.errors))
        self.assertEqual(res.features, [])

    def test_missing_anchor_needs_anchor(self):
        res = calibrate_plan_source(
            source=_image_frame(),
            pixel_features=[{"feature_id": "p1", "kind": "point", "pixels": [10.0, 10.0]}],
            anchors=[],
        )
        self.assertEqual(res.verdict, "NEEDS_ANCHOR")
        self.assertTrue(any("no_dimensional_anchor" in e for e in res.errors))

    def test_zero_length_anchor_invalid(self):
        source = _image_frame()
        anchors = [{"anchor_id": "anchor_degenerate", "statement": "Zero span",
                    "pixel_from": [100.0, 100.0], "pixel_to": [100.0, 100.0],
                    "real_length": 15000.0, "unit": "mm", "confidence": 0.9}]
        res = calibrate_plan_source(source=source, pixel_features=[], anchors=anchors)
        self.assertEqual(res.verdict, "INVALID_SOURCE")
        self.assertTrue(any("anchor_zero_pixel_span" in e for e in res.errors))

    def test_anchor_out_of_bounds_invalid(self):
        source = _image_frame()
        anchors = [{"anchor_id": "anchor_oob", "statement": "Outside image",
                    "pixel_from": [0.0, 0.0], "pixel_to": [5000.0, 0.0],
                    "real_length": 15000.0, "unit": "mm", "confidence": 0.9}]
        res = calibrate_plan_source(source=source, pixel_features=[], anchors=anchors)
        self.assertEqual(res.verdict, "INVALID_SOURCE")
        self.assertTrue(any("anchor_out_of_bounds" in e for e in res.errors))

    def test_provenance_ledger_statuses(self):
        source = _image_frame()
        res = calibrate_plan_source(
            source=source,
            pixel_features=[{"feature_id": "wall_probe", "kind": "point", "pixels": [600.0, 800.0]}],
            anchors=[_width_anchor(1200)],
        )
        self.assertEqual(res.verdict, "CALIBRATED")
        ledger = res.provenance_ledger
        self.assertEqual(ledger["test6_house_3_floors"]["status"], "observed")
        self.assertEqual(ledger["wall_probe.pixels"]["status"], "observed")
        self.assertEqual(ledger["anchor_total_width"]["status"], "approved_assumption")
        self.assertEqual(ledger["wall_probe"]["status"], "derived")
        self.assertEqual(ledger["frame.scale"]["status"], "derived")

    def test_out_of_bounds_feature_excluded_with_warning(self):
        source = _image_frame()
        res = calibrate_plan_source(
            source=source,
            pixel_features=[
                {"feature_id": "good_probe", "kind": "point", "pixels": [600.0, 800.0]},
                {"feature_id": "bad_probe", "kind": "point", "pixels": [5000.0, 10.0]},
            ],
            anchors=[_width_anchor(1200)],
        )
        self.assertEqual(res.verdict, "CALIBRATED")
        by_id = {f["feature_id"]: f for f in res.features}
        self.assertIn("good_probe", by_id)
        self.assertNotIn("bad_probe", by_id)
        self.assertTrue(any("pixel_out_of_bounds:bad_probe" in w for w in res.warnings))
        self.assertEqual(res.provenance_ledger["bad_probe"]["status"], "unknown")

    def test_confidence_is_minimum_of_anchors(self):
        source = _image_frame()
        anchors = [
            _width_anchor(1200, real_length=15000.0, confidence=0.9),
            {"anchor_id": "anchor_half_width", "statement": "Half width check",
             "pixel_from": [0.0, 0.0], "pixel_to": [600.0, 0.0],
             "real_length": 7500.0, "unit": "mm", "confidence": 0.6},
        ]
        res = calibrate_plan_source(source=source, pixel_features=[], anchors=anchors)
        self.assertEqual(res.verdict, "CALIBRATED")
        self.assertAlmostEqual(res.confidence, 0.6, places=9)


if __name__ == "__main__":
    unittest.main()
