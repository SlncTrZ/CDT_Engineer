"""Acceptance: omissions must fail before CAD; footprints and units must be truthful."""
from __future__ import annotations

import copy
import unittest

from execution.plan_compiler import compile_plan_spec
from execution.plan_review import review_plan_spec
from execution.source_calibration import calibrate_plan_source
from source_inventory_fixture import freeze_test_source
from test_plan_review_gates_20260917 import _valid_arch_spec


class DrawingCompletenessAcceptance(unittest.TestCase):
    def spec(self):
        return freeze_test_source(_valid_arch_spec())

    def test_empty_plan_never_compiles_even_for_concept(self):
        spec = self.spec()
        spec["payload"] = {}
        spec["provenance_ledger"] = {}
        for release in ("concept", "technical_draft", "design_review"):
            result = compile_plan_spec(spec, {"release_target": release})
            self.assertFalse(result.ok)
            self.assertEqual(result.chunks, [])

    def test_missing_inventory_blocks_every_release(self):
        spec = self.spec()
        del spec["source_inventory"]
        for release in ("concept", "technical_draft", "design_review"):
            self.assertFalse(review_plan_spec(spec, {"release_target": release}).approved)

    def test_frozen_door_and_dimension_cannot_be_deleted(self):
        for key, fid in (("openings", "door_d1"), ("dimensions", "dim_01")):
            spec = self.spec()
            spec["payload"][key] = []
            spec["provenance_ledger"].pop(fid)
            result = compile_plan_spec(spec, {"release_target": "design_review"})
            self.assertFalse(result.ok)
            self.assertEqual(result.chunks, [])

    def test_family_accounting_cannot_be_dropped(self):
        spec = self.spec()
        spec["source_inventory"]["items"] = [
            i for i in spec["source_inventory"]["items"] if i["semantic_family"] != "columns"]
        self.assertFalse(review_plan_spec(spec).approved)

    def test_required_unknown_column_is_not_invented(self):
        spec = self.spec()
        item = next(i for i in spec["source_inventory"]["items"] if i["semantic_family"] == "columns")
        item.update(required=True, feature_refs=["unknown-column"], evidence_state="unknown")
        result = compile_plan_spec(spec)
        self.assertFalse(result.ok)
        self.assertNotIn("columns", spec["payload"])

    def test_na_requires_review_and_evidence(self):
        for field in ("reviewed_by", "exclusion_reason", "source_evidence"):
            spec = self.spec()
            item = next(i for i in spec["source_inventory"]["items"] if not i["required"])
            item.pop(field)
            self.assertFalse(review_plan_spec(spec).approved)

    def test_image_requires_all_three_ordered_reads(self):
        for passes in ([], ["context"], ["context", "detail"], ["detail", "context", "confirmation"]):
            spec = self.spec()
            spec["source_inventory"].update(source_type="image", review_passes=passes)
            self.assertFalse(review_plan_spec(spec).approved)
        spec["source_inventory"].update(review_passes=["context", "detail", "confirmation"])
        self.assertTrue(review_plan_spec(spec).approved)

    def test_duplicate_inventory_ids_rejected(self):
        spec = self.spec()
        spec["source_inventory"]["items"].append(copy.deepcopy(spec["source_inventory"]["items"][0]))
        self.assertFalse(review_plan_spec(spec).approved)

    def test_ref_cannot_match_wrong_semantic_family(self):
        spec = self.spec()
        item = next(i for i in spec["source_inventory"]["items"] if i["semantic_family"] == "doors")
        item["feature_refs"] = ["wall_w1"]
        self.assertFalse(review_plan_spec(spec).approved)

    def fixture_spec(self, position=(2500, 2000), dimensions=(1000, 600), rotation=0):
        spec = self.spec()
        spec["payload"]["fixtures"] = [{
            "fixture_id": "sofa", "fixture_type": "sofa", "host_space_id": "space_living",
            "position": list(position), "dimensions": list(dimensions), "rotation": rotation}]
        spec["provenance_ledger"]["sofa"] = {"status": "specified", "source_id": "test-source"}
        return freeze_test_source(spec)

    def test_center_inside_envelope_outside_blocks(self):
        self.assertFalse(review_plan_spec(self.fixture_spec((4900, 3900), (3000, 2000))).approved)

    def test_rotated_fitting_footprint_passes(self):
        self.assertTrue(review_plan_spec(self.fixture_spec(rotation=45)).approved)

    def test_radian_rotation_has_same_containment(self):
        import math
        spec = self.fixture_spec((4500, 2000), (1600, 400), rotation=math.pi / 2)
        spec["units"]["angle"] = "rad"
        self.assertTrue(review_plan_spec(spec).approved)

    def test_missing_envelope_is_unknown_not_point_pass(self):
        spec = self.fixture_spec()
        del spec["payload"]["fixtures"][0]["dimensions"]
        self.assertFalse(review_plan_spec(spec).approved)

    def test_missing_host_cannot_skip_containment(self):
        spec = self.fixture_spec()
        del spec["payload"]["fixtures"][0]["host_space_id"]
        self.assertFalse(review_plan_spec(spec).approved)

    def test_concave_room_edge_excursion_blocks(self):
        spec = self.fixture_spec((2500, 2000), (4000, 2000))
        spec["payload"]["spaces"][0]["boundary_polygon"] = [
            [0, 0], [5000, 0], [5000, 4000], [3000, 4000],
            [3000, 2500], [2000, 2500], [2000, 4000], [0, 4000]]
        self.assertFalse(review_plan_spec(spec).approved)

    def test_small_boundary_touch_allowed(self):
        self.assertTrue(review_plan_spec(self.fixture_spec((500, 300))).approved)

    def test_payload_schema_actually_validates_nested_features(self):
        spec = self.spec()
        spec["payload"]["walls"][0]["thickness"] = -1
        self.assertFalse(review_plan_spec(spec).approved)

    def test_every_supported_anchor_unit_outputs_real_mm(self):
        for unit, factor in {"mm": 1, "cm": 10, "m": 1000, "in": 25.4, "ft": 304.8}.items():
            result = calibrate_plan_source(
                source={"source_id": "image", "pixel_width": 100, "pixel_height": 100},
                anchors=[{"anchor_id": "anchor", "pixel_from": [0, 0], "pixel_to": [100, 0],
                          "real_length": 10, "unit": unit}],
                pixel_features=[{"feature_id": "p", "kind": "point", "pixels": [50, 50]}])
            self.assertEqual(result.verdict, "CALIBRATED")
            self.assertEqual(result.frame["unit"], "mm")
            self.assertAlmostEqual(result.features[0]["coords_mm"][0], 5 * factor)
            self.assertEqual(result.anchors[0]["unit"], unit)

    def test_unsupported_unit_refused_before_calibration(self):
        result = calibrate_plan_source(
            source={"source_id": "image", "pixel_width": 100, "pixel_height": 100},
            anchors=[{"anchor_id": "anchor", "pixel_from": [0, 0], "pixel_to": [100, 0],
                      "real_length": 10, "unit": "yards"}])
        self.assertEqual(result.verdict, "INVALID_SOURCE")

    def complete_spec(self):
        spec = self.fixture_spec()
        spec["payload"]["columns"] = [
            {"column_id": "column_c1", "shape": "rect", "dimensions": [220, 220], "center": [0, 0]}]
        spec["payload"]["walls"].extend([
            {"wall_id": "wall_partition", "wall_type": "partition", "thickness": 110,
             "start": [5000, 4000], "end": [0, 4000], "baseline": "center"},
            {"wall_id": "wall_bearing", "wall_type": "bearing", "thickness": 220,
             "start": [0, 4000], "end": [0, 0], "baseline": "center"}])
        spec["payload"]["openings"].append({
            "opening_id": "window_w1", "host_wall_id": "wall_w2", "opening_type": "window",
            "offset_along_wall": 1000, "width": 1200, "height": 1500,
            "sill_height": 900, "head_height": 2400})
        for fid in ("column_c1", "wall_partition", "wall_bearing", "window_w1"):
            spec["provenance_ledger"][fid] = {"status": "specified", "source_id": "test-source"}
        return freeze_test_source(spec)

    def test_complete_floor_plan_passes_and_every_family_is_required(self):
        spec = self.complete_spec()
        self.assertTrue(all(item["required"] for item in spec["source_inventory"]["items"]))
        self.assertTrue(compile_plan_spec(spec, {"release_target": "design_review"}).ok)

    def test_each_small_or_large_required_feature_omission_blocks(self):
        for family, key, id_key, fid in (
                ("columns", "columns", "column_id", "column_c1"),
                ("bearing_walls", "walls", "wall_id", "wall_bearing"),
                ("partition_walls", "walls", "wall_id", "wall_partition"),
                ("doors", "openings", "opening_id", "door_d1"),
                ("windows", "openings", "opening_id", "window_w1"),
                ("fixtures", "fixtures", "fixture_id", "sofa"),
                ("dimensions", "dimensions", "dimension_id", "dim_01")):
            with self.subTest(family=family):
                spec = self.complete_spec()
                spec["payload"][key] = [v for v in spec["payload"][key] if v[id_key] != fid]
                spec["provenance_ledger"].pop(fid)
                result = compile_plan_spec(spec, {"release_target": "design_review"})
                self.assertFalse(result.ok)
                self.assertEqual(result.chunks, [])

    def test_explicit_na_cannot_hide_existing_geometry(self):
        spec = self.complete_spec()
        item = next(i for i in spec["source_inventory"]["items"] if i["semantic_family"] == "windows")
        item.update(required=False, feature_refs=[], exclusion_reason="Not applicable", reviewed_by="reviewer")
        self.assertFalse(review_plan_spec(spec).approved)

    def test_duplicate_native_feature_identity_blocks(self):
        spec = self.spec()
        spec["payload"]["axes"][1]["axis_id"] = "axis_A"
        self.assertFalse(review_plan_spec(spec).approved)

    def test_zero_required_source_items_block(self):
        spec = self.spec()
        spec["source_inventory"]["items"] = []
        self.assertFalse(review_plan_spec(spec).approved)

    def test_negative_or_malformed_envelope_blocks(self):
        for dims in ([-1, 2], [0, 2], [2], [2, 3, 4], ["2", 3]):
            spec = self.fixture_spec()
            spec["payload"]["fixtures"][0]["dimensions"] = dims
            self.assertFalse(review_plan_spec(spec).approved)

    def test_compiler_binds_source_inventory_to_every_chunk(self):
        import hashlib
        import json
        spec = self.complete_spec()
        result = compile_plan_spec(spec)
        binding = hashlib.sha256(json.dumps(
            spec["source_inventory"], sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False).encode("utf-8")).hexdigest()
        self.assertTrue(result.ok)
        for chunk in result.chunks:
            self.assertEqual(chunk["source_inventory_sha256"], binding)
            self.assertEqual(chunk["source_sha256"], spec["source_inventory"]["source_sha256"])

    def test_unplanned_extra_feature_cannot_be_invented(self):
        spec = self.complete_spec()
        extra = copy.deepcopy(spec["payload"]["openings"][-1])
        extra.update(opening_id="invented-window", offset_along_wall=2500, width=800)
        spec["payload"]["openings"].append(extra)
        spec["provenance_ledger"]["invented-window"] = {"status": "specified", "source_id": "test-source"}
        self.assertFalse(review_plan_spec(spec).approved)

    def test_source_bindings_survive_execution_receipt(self):
        from execution.provenance_release import build_chunk_receipt
        chunk = compile_plan_spec(self.complete_spec()).chunks[0]
        receipt = build_chunk_receipt(chunk, engine_receipt_id="independent-readback",
                                      created_or_modified_ids=["native-id"],
                                      transaction_mode="compensating")
        for key in ("source_sha256", "source_inventory_sha256"):
            self.assertEqual(receipt[key], chunk[key])
        del chunk["source_inventory_sha256"]
        with self.assertRaises(ValueError):
            build_chunk_receipt(chunk, engine_receipt_id="readback",
                                created_or_modified_ids=[], transaction_mode="compensating")

    def test_unit_conversion_overflow_is_invalid_source(self):
        result = calibrate_plan_source(
            source={"source_id": "image", "pixel_width": 100, "pixel_height": 100},
            anchors=[{"anchor_id": "anchor", "pixel_from": [0, 0], "pixel_to": [100, 0],
                      "real_length": 1e308, "unit": "m"}])
        self.assertEqual(result.verdict, "INVALID_SOURCE")
