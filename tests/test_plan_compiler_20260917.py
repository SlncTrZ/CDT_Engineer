"""Tests for deterministic PlanSpec -> semantic chunks compiler (ENG-R09).
Wing: code | Topic: plan-compiler | Updated: 2026-09-18 00:25
"""
from __future__ import annotations

import unittest
from execution.plan_compiler import compile_plan_spec


def _base_envelope(plan_id="compile_case_01", plan_type="architectural_floor_plan"):
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


def _valid_arch_spec(plan_id="arch_compile_ok"):
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


def _chunk_by_type(result, semantic_type):
    return [c for c in result.chunks if c["semantic_type"] == semantic_type]


def _assert_dag_valid(testcase, result):
    ids = {c["chunk_id"] for c in result.chunks}
    seen_order = []
    for chunk in result.chunks:
        for dep in chunk["depends_on"]:
            testcase.assertIn(dep, ids, f"dangling dependency {dep}")
            testcase.assertIn(dep, seen_order, f"dependency {dep} not committed before {chunk['chunk_id']}")
        seen_order.append(chunk["chunk_id"])
    testcase.assertEqual(len(ids), len(result.chunks), "duplicate chunk_id")


class TestPlanCompiler(unittest.TestCase):
    def test_valid_arch_compiles_to_bounded_chunks(self):
        res = compile_plan_spec(_valid_arch_spec())
        self.assertTrue(res.ok, f"errors: {res.errors}")
        self.assertEqual(res.verdict, "COMPILED_READY_FOR_EXECUTION")
        # 5 semantic groups, not dozens of primitive round-trips.
        self.assertLessEqual(len(res.chunks), 5)
        self.assertGreaterEqual(len(res.chunks), 4)
        _assert_dag_valid(self, res)
        types = [c["semantic_type"] for c in res.chunks]
        self.assertIn("grid_axes", types)
        self.assertIn("wall_shell", types)
        self.assertIn("openings", types)

    def test_openings_depend_on_wall_shell(self):
        res = compile_plan_spec(_valid_arch_spec())
        walls = _chunk_by_type(res, "wall_shell")
        openings = _chunk_by_type(res, "openings")
        self.assertEqual(len(walls), 1)
        self.assertEqual(len(openings), 1)
        self.assertIn(walls[0]["chunk_id"], openings[0]["depends_on"])

    def test_review_rejected_spec_refused(self):
        spec = _valid_arch_spec("arch_bad_space")
        spec["payload"]["spaces"][0]["boundary_polygon"] = [
            [0.0, 0.0], [5000.0, 3000.0], [4000.0, 0.0], [1000.0, 4000.0],
        ]
        res = compile_plan_spec(spec)
        self.assertFalse(res.ok)
        self.assertEqual(res.verdict, "REFUSED")
        self.assertEqual(res.chunks, [])
        self.assertTrue(any("review_not_approved" in e for e in res.errors))

    def test_invalid_planspec_refused(self):
        spec = _valid_arch_spec("arch_invalid")
        spec["payload"]["openings"][0]["offset_along_wall"] = 4500.0
        spec["payload"]["openings"][0]["width"] = 900.0  # 5400 > 5000 wall
        res = compile_plan_spec(spec)
        self.assertFalse(res.ok)
        self.assertEqual(res.verdict, "REFUSED")
        self.assertTrue(any("planspec_invalid" in e for e in res.errors))

    def test_wall_group_splits_over_budget(self):
        spec = _valid_arch_spec("arch_many_walls")
        for i in range(3, 8):
            wid = f"wall_w{i}"
            spec["payload"]["walls"].append(
                {"wall_id": wid, "wall_type": "partition", "thickness": 110.0,
                 "start": [float(i * 10000), 0.0], "end": [float(i * 10000 + 3000), 0.0],
                 "baseline": "center", "height": 2700.0},
            )
            spec["provenance_ledger"][wid] = {
                "status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0,
            }
        # Connect the new walls into one chain so G5 wall_joins passes.
        for i in range(3, 7):
            spec["payload"]["walls"][i - 1]["end"] = [float((i + 1) * 10000), 0.0]
            spec["payload"]["walls"][i]["start"] = [float((i + 1) * 10000), 0.0]
        res = compile_plan_spec(spec, requirements={"max_features_per_chunk": 2})
        self.assertTrue(res.ok, f"errors: {res.errors}")
        shells = _chunk_by_type(res, "wall_shell")
        # 7 walls over budget 2 -> 4 sub-chunks, chained.
        self.assertEqual(len(shells), 4)
        for shell in shells:
            self.assertLessEqual(len(shell["feature_ids"]), 2)
        _assert_dag_valid(self, res)

    def test_civil_profile_compiles_with_grade_dependency(self):
        spec = _base_envelope("profile_compile_ok", "civil_road_profile")
        spec["domain_id"] = "civil-road-infrastructure"
        spec["units"] = {"length": "m", "angle": "deg", "station": "m"}
        spec["coordinate_system"] = {
            "datum": "VN2000_Zone3", "origin": [500000.0, 2300000.0, 0.0],
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
        res = compile_plan_spec(spec)
        self.assertTrue(res.ok, f"errors: {res.errors}")
        types = [c["semantic_type"] for c in res.chunks]
        self.assertIn("profile_ground", types)
        self.assertIn("profile_grade", types)
        ground = _chunk_by_type(res, "profile_ground")[0]
        grade = _chunk_by_type(res, "profile_grade")[0]
        self.assertIn(ground["chunk_id"], grade["depends_on"])
        _assert_dag_valid(self, res)

    def test_civil_cross_section_pavement_postcondition(self):
        spec = _base_envelope("xs_compile_ok", "civil_road_cross_section")
        spec["domain_id"] = "civil-road-infrastructure"
        spec["units"] = {"length": "m", "angle": "deg", "station": "m"}
        spec["coordinate_system"] = {
            "datum": "xs_datum", "origin": [0.0, 10.0],
            "scale": {"horizontal": 100.0, "vertical": 100.0},
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
                    {"layer_id": "layer_b", "name": "CPDD 1", "material": "crushed_stone_1", "thickness": 0.15, "order": 2},
                ],
            },
        })
        res = compile_plan_spec(spec)
        self.assertTrue(res.ok, f"errors: {res.errors}")
        pavement = _chunk_by_type(res, "xs_pavement")
        self.assertEqual(len(pavement), 1)
        post = pavement[0]["expected_outputs"]
        self.assertEqual(post["layer_count"], 2)
        self.assertAlmostEqual(post["total_thickness"], 0.20, places=9)

    def test_compile_is_deterministic(self):
        first = compile_plan_spec(_valid_arch_spec("arch_determinism"))
        second = compile_plan_spec(_valid_arch_spec("arch_determinism"))
        self.assertEqual([c["chunk_id"] for c in first.chunks],
                         [c["chunk_id"] for c in second.chunks])
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_provenance_carried_into_chunks(self):
        res = compile_plan_spec(_valid_arch_spec())
        self.assertTrue(res.ok)
        for chunk in res.chunks:
            for fid in chunk["feature_ids"]:
                self.assertIn(fid, chunk["provenance"])

    def test_no_cad_primitives_in_chunks(self):
        banned = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "HATCH",
                  "TEXT", "MTEXT", "INSERT", "BLOCK", "3DFACE", "SOLID", "SPLINE", "ELLIPSE"}

        def _scan(data):
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(k, str) and k.upper() in banned:
                        return k
                    hit = _scan(v)
                    if hit:
                        return hit
            elif isinstance(data, list):
                for item in data:
                    hit = _scan(item)
                    if hit:
                        return hit
            elif isinstance(data, str):
                if data.strip().upper() in banned:
                    return data
            return None

        res = compile_plan_spec(_valid_arch_spec())
        self.assertTrue(res.ok)
        for chunk in res.chunks:
            self.assertIsNone(_scan(chunk), f"CAD primitive leaked in {chunk['chunk_id']}")

    def test_empty_groups_skipped(self):
        spec = _valid_arch_spec("arch_minimal")
        spec["payload"]["spaces"] = []
        spec["payload"]["dimensions"] = []
        for fid in ("space_living", "dim_01"):
            del spec["provenance_ledger"][fid]
        res = compile_plan_spec(spec)
        self.assertTrue(res.ok, f"errors: {res.errors}")
        types = [c["semantic_type"] for c in res.chunks]
        self.assertNotIn("spaces_fixtures", types)
        self.assertNotIn("annotation_dimensions", types)
        _assert_dag_valid(self, res)


if __name__ == "__main__":
    unittest.main()
