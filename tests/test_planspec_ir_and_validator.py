"""Tests for PlanSpec IR and Deterministic Validator (ENG-R07).
Wing: code | Topic: plan-spec-ir | Updated: 2026-09-17 22:50
"""
from __future__ import annotations

import unittest
from execution.planspec import validate_plan_spec


class TestPlanSpecIRAndValidator(unittest.TestCase):
    def test_valid_architectural_floor_plan(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "arch_fp_001",
            "domain_id": "building-architecture",
            "plan_type": "architectural_floor_plan",
            "units": {"length": "mm", "angle": "deg"},
            "coordinate_system": {
                "datum": "project_local_origin",
                "origin": [0.0, 0.0],
                "azimuth": 0.0,
                "scale": {"horizontal": 1.0, "vertical": 1.0},
            },
            "provenance_ledger": {
                "axis_A": {"status": "specified", "source_id": "dwg_ref_01", "assumption_id": None, "confidence": 1.0},
                "wall_w1": {"status": "approved_assumption", "source_id": None, "assumption_id": "asm_wall_thick_220", "confidence": 0.9},
                "door_d1": {"status": "specified", "source_id": "spec_sheet_01", "assumption_id": None, "confidence": 1.0},
                "space_living": {"status": "derived", "source_id": None, "assumption_id": None, "confidence": 0.95},
                "col_c1": {"status": "observed", "source_id": "img_ref_01", "assumption_id": None, "confidence": 0.8},
                "dim_01": {"status": "derived", "source_id": None, "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [
                {
                    "id": "asm_wall_thick_220",
                    "statement": "Exterior wall assumed 220mm brick masonry",
                    "status": "approved_assumption",
                    "evidence": ["local_standard_tcvn"],
                }
            ],
            "chunk_dependencies": [
                {"chunk_id": "chk_shell", "semantic_type": "wall_shell", "depends_on": []},
                {"chunk_id": "chk_openings", "semantic_type": "openings", "depends_on": ["chk_shell"]},
            ],
            "payload": {
                "axes": [
                    {"axis_id": "axis_A", "label": "A", "start": [0.0, 0.0], "end": [15000.0, 0.0]}
                ],
                "walls": [
                    {
                        "wall_id": "wall_w1",
                        "wall_type": "exterior",
                        "thickness": 220.0,
                        "start": [0.0, 0.0],
                        "end": [5000.0, 0.0],
                        "baseline": "center",
                        "height": 3300.0,
                    }
                ],
                "columns": [
                    {
                        "column_id": "col_c1",
                        "shape": "rect",
                        "dimensions": [220.0, 220.0],
                        "center": [0.0, 0.0],
                    }
                ],
                "openings": [
                    {
                        "opening_id": "door_d1",
                        "host_wall_id": "wall_w1",
                        "opening_type": "door",
                        "offset_along_wall": 1000.0,
                        "width": 900.0,
                        "height": 2200.0,
                        "sill_height": 0.0,
                        "head_height": 2200.0,
                    }
                ],
                "spaces": [
                    {
                        "space_id": "space_living",
                        "name": "Living Room",
                        "boundary_polygon": [[0.0, 0.0], [5000.0, 0.0], [5000.0, 4000.0], [0.0, 4000.0]],
                        "net_area": 20.0,
                    }
                ],
                "dimensions": [
                    {
                        "dimension_id": "dim_01",
                        "dimension_type": "linear",
                        "measured_value": 5000.0,
                        "witness_points": [[0.0, 0.0], [5000.0, 0.0]],
                        "feature_refs": ["wall_w1"],
                    }
                ],
            },
        }

        res = validate_plan_spec(spec)
        self.assertTrue(res.valid, f"Validation failed with: {res.errors}")
        self.assertEqual(res.verdict, "APPROVED_FOR_EXECUTION")
        self.assertEqual(res.feature_count, 6)
        self.assertEqual(res.provenance_summary["approved_assumption"], 1)
        self.assertEqual(res.provenance_summary["specified"], 2)

    def test_banned_cad_primitives_rejected(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "bad_cad_spec",
            "domain_id": "building-architecture",
            "plan_type": "architectural_floor_plan",
            "units": {"length": "mm", "angle": "deg"},
            "coordinate_system": {
                "datum": "local",
                "origin": [0.0, 0.0],
                "scale": {"horizontal": 1.0},
            },
            "provenance_ledger": {},
            "assumptions": [],
            "payload": {
                "raw_drawing": {
                    "LINE": [[0, 0], [100, 100]],
                }
            },
        }
        res = validate_plan_spec(spec)
        self.assertFalse(res.valid)
        self.assertEqual(res.verdict, "REJECTED")
        self.assertTrue(any("cad_primitive_forbidden_key:LINE" in err for err in res.errors))

    def test_opening_exceeding_wall_length_rejected(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "bad_opening_len",
            "domain_id": "building-architecture",
            "plan_type": "architectural_floor_plan",
            "units": {"length": "mm", "angle": "deg"},
            "coordinate_system": {
                "datum": "local",
                "origin": [0.0, 0.0],
                "scale": {"horizontal": 1.0},
            },
            "provenance_ledger": {
                "w1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
                "d1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [],
            "payload": {
                "walls": [
                    {"wall_id": "w1", "wall_type": "interior", "thickness": 110.0, "start": [0, 0], "end": [2000, 0], "baseline": "center"}
                ],
                "openings": [
                    {
                        "opening_id": "d1",
                        "host_wall_id": "w1",
                        "opening_type": "door",
                        "offset_along_wall": 1500.0,
                        "width": 900.0,  # 1500 + 900 = 2400 > 2000
                        "height": 2200.0,
                        "sill_height": 0.0,
                        "head_height": 2200.0,
                    }
                ],
            },
        }
        res = validate_plan_spec(spec)
        self.assertFalse(res.valid)
        self.assertTrue(any("opening_exceeds_host_wall_length:d1" in err for err in res.errors))

    def test_opening_exceeding_wall_height_rejected(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "bad_opening_height",
            "domain_id": "building-architecture",
            "plan_type": "architectural_floor_plan",
            "units": {"length": "mm", "angle": "deg"},
            "coordinate_system": {
                "datum": "local",
                "origin": [0.0, 0.0],
                "scale": {"horizontal": 1.0},
            },
            "provenance_ledger": {
                "w1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
                "win1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [],
            "payload": {
                "walls": [
                    {"wall_id": "w1", "wall_type": "exterior", "thickness": 220.0, "start": [0, 0], "end": [4000, 0], "baseline": "center", "height": 3000.0}
                ],
                "openings": [
                    {
                        "opening_id": "win1",
                        "host_wall_id": "w1",
                        "opening_type": "window",
                        "offset_along_wall": 1000.0,
                        "width": 1200.0,
                        "height": 2200.0,
                        "sill_height": 900.0,  # sill 900 + height 2200 = 3100 > wall height 3000
                        "head_height": 3100.0,
                    }
                ],
            },
        }
        res = validate_plan_spec(spec)
        self.assertFalse(res.valid)
        self.assertTrue(any("opening_head_exceeds_wall_height:win1" in err for err in res.errors))

    def test_missing_provenance_entry_rejected(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "missing_prov",
            "domain_id": "building-architecture",
            "plan_type": "architectural_floor_plan",
            "units": {"length": "mm", "angle": "deg"},
            "coordinate_system": {
                "datum": "local",
                "origin": [0.0, 0.0],
                "scale": {"horizontal": 1.0},
            },
            "provenance_ledger": {
                # w1 registered, but space_1 is not
                "w1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [],
            "payload": {
                "walls": [
                    {"wall_id": "w1", "wall_type": "interior", "thickness": 110.0, "start": [0, 0], "end": [2000, 0], "baseline": "center"}
                ],
                "spaces": [
                    {"space_id": "space_1", "name": "Room", "boundary_polygon": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]}
                ]
            },
        }
        res = validate_plan_spec(spec)
        self.assertFalse(res.valid)
        self.assertTrue(any("missing_provenance_entry_for_feature:space_1" in err for err in res.errors))

    def test_unlinked_approved_assumption_rejected(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "unlinked_asm",
            "domain_id": "building-architecture",
            "plan_type": "architectural_floor_plan",
            "units": {"length": "mm", "angle": "deg"},
            "coordinate_system": {
                "datum": "local",
                "origin": [0.0, 0.0],
                "scale": {"horizontal": 1.0},
            },
            "provenance_ledger": {
                "w1": {"status": "approved_assumption", "source_id": None, "assumption_id": "non_existent_asm", "confidence": 0.8},
            },
            "assumptions": [
                {"id": "real_asm", "statement": "Statement", "status": "approved_assumption"}
            ],
            "payload": {
                "walls": [
                    {"wall_id": "w1", "wall_type": "interior", "thickness": 110.0, "start": [0, 0], "end": [2000, 0], "baseline": "center"}
                ]
            },
        }
        res = validate_plan_spec(spec)
        self.assertFalse(res.valid)
        self.assertTrue(any("unlinked_approved_assumption:w1->non_existent_asm" in err for err in res.errors))

    def test_chunk_dependency_cycle_rejected(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "cyclic_chunks",
            "domain_id": "building-architecture",
            "plan_type": "architectural_floor_plan",
            "units": {"length": "mm", "angle": "deg"},
            "coordinate_system": {
                "datum": "local",
                "origin": [0.0, 0.0],
                "scale": {"horizontal": 1.0},
            },
            "provenance_ledger": {},
            "assumptions": [],
            "chunk_dependencies": [
                {"chunk_id": "chunk_A", "semantic_type": "type_A", "depends_on": ["chunk_B"]},
                {"chunk_id": "chunk_B", "semantic_type": "type_B", "depends_on": ["chunk_A"]},
            ],
            "payload": {},
        }
        res = validate_plan_spec(spec)
        self.assertFalse(res.valid)
        self.assertTrue(any("cyclic_chunk_dependency_detected" in err for err in res.errors))

    def test_valid_civil_road_longitudinal_profile(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "road_profile_01",
            "domain_id": "civil-road-infrastructure",
            "plan_type": "civil_road_profile",
            "units": {"length": "m", "angle": "deg", "station": "m"},
            "coordinate_system": {
                "datum": "VN2000_Zone3_Central105_00",
                "origin": [500000.0, 2300000.0, 0.0],
                "scale": {"horizontal": 1000.0, "vertical": 100.0},  # 1/1000 H, 1/100 V (standard 10x vertical distortion)
            },
            "provenance_ledger": {
                "ground_pt_0": {"status": "observed", "source_id": "topo_survey_2026", "assumption_id": None, "confidence": 1.0},
                "ground_pt_1": {"status": "observed", "source_id": "topo_survey_2026", "assumption_id": None, "confidence": 1.0},
                "ground_pt_2": {"status": "observed", "source_id": "topo_survey_2026", "assumption_id": None, "confidence": 1.0},
                "pvi_0": {"status": "specified", "source_id": "prelim_design", "assumption_id": None, "confidence": 1.0},
                "pvi_1": {"status": "specified", "source_id": "prelim_design", "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [],
            "payload": {
                "alignment_ref": "tuyen_chinh_km0_km1",
                "ground_line": [
                    {"station": 0.0, "elevation": 12.50, "label": "Km0+000"},
                    {"station": 50.0, "elevation": 12.85, "label": "Cọc 1"},
                    {"station": 100.0, "elevation": 13.20, "label": "Km0+100"},
                ],
                "grade_line": [
                    {"station": 0.0, "elevation": 13.00, "grade_in_percent": 1.0, "grade_out_percent": 1.0},
                    {"station": 100.0, "elevation": 14.00, "grade_in_percent": 1.0, "curve_radius": 2000.0, "curve_length": 40.0},
                ],
            },
        }
        res = validate_plan_spec(spec)
        self.assertTrue(res.valid, f"Validation failed with: {res.errors}")
        self.assertEqual(res.verdict, "APPROVED_FOR_EXECUTION")
        self.assertEqual(res.feature_count, 5)

    def test_civil_road_profile_non_monotonic_station_rejected(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "road_profile_bad_station",
            "domain_id": "civil-road-infrastructure",
            "plan_type": "civil_road_profile",
            "units": {"length": "m", "angle": "deg", "station": "m"},
            "coordinate_system": {
                "datum": "VN2000",
                "origin": [0.0, 0.0],
                "scale": {"horizontal": 1000.0, "vertical": 100.0},
            },
            "provenance_ledger": {
                "ground_pt_0": {"status": "observed", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
                "ground_pt_1": {"status": "observed", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
                "pvi_0": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
                "pvi_1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [],
            "payload": {
                "alignment_ref": "tuyen_1",
                "ground_line": [
                    {"station": 50.0, "elevation": 12.0},
                    {"station": 30.0, "elevation": 12.5},  # 30.0 <= 50.0 non-monotonic!
                ],
                "grade_line": [
                    {"station": 0.0, "elevation": 13.0},
                    {"station": 100.0, "elevation": 14.0},
                ],
            },
        }
        res = validate_plan_spec(spec)
        self.assertFalse(res.valid)
        self.assertTrue(any("ground_line_non_monotonic_station:1" in err for err in res.errors))

    def test_valid_civil_road_cross_section(self):
        spec = {
            "schema_version": "0.1.0",
            "plan_id": "road_cs_km0_050",
            "domain_id": "civil-road-infrastructure",
            "plan_type": "civil_road_cross_section",
            "units": {"length": "m", "angle": "deg", "station": "m"},
            "coordinate_system": {
                "datum": "cross_section_datum_c1",
                "origin": [0.0, 10.0],
                "scale": {"horizontal": 100.0, "vertical": 100.0},
            },
            "provenance_ledger": {
                "carriageway": {"status": "specified", "source_id": "tcvn_4054_2005", "assumption_id": None, "confidence": 1.0},
                "layer_btnc": {"status": "specified", "source_id": "standard_spec", "assumption_id": None, "confidence": 1.0},
                "layer_btnr": {"status": "specified", "source_id": "standard_spec", "assumption_id": None, "confidence": 1.0},
                "layer_cpdd1": {"status": "specified", "source_id": "standard_spec", "assumption_id": None, "confidence": 1.0},
                "layer_cpdd2": {"status": "specified", "source_id": "standard_spec", "assumption_id": None, "confidence": 1.0},
                "layer_k98": {"status": "specified", "source_id": "standard_spec", "assumption_id": None, "confidence": 1.0},
            },
            "assumptions": [],
            "payload": {
                "alignment_ref": "tuyen_chinh_km0_km1",
                "station": 50.0,
                "elevation_datum": 10.0,
                "carriageway": {
                    "width_left": 3.5,
                    "width_right": 3.5,
                    "cross_slope_left_percent": -2.0,
                    "cross_slope_right_percent": -2.0,
                },
                "shoulders": {
                    "paved_left": {"width": 1.5, "cross_slope_percent": -2.0},
                    "paved_right": {"width": 1.5, "cross_slope_percent": -2.0},
                    "unpaved_left": {"width": 0.5, "cross_slope_percent": -4.0},
                    "unpaved_right": {"width": 0.5, "cross_slope_percent": -4.0},
                },
                "pavement_structure": [
                    {"layer_id": "layer_btnc", "name": "Bê tông nhựa chặt C12.5", "material": "asphalt_concrete_c12_5", "thickness": 0.05, "order": 1},
                    {"layer_id": "layer_btnr", "name": "Bê tông nhựa rỗng C19", "material": "asphalt_concrete_c19", "thickness": 0.07, "order": 2},
                    {"layer_id": "layer_cpdd1", "name": "Cấp phối đá dăm Loại 1", "material": "crushed_stone_class_1", "thickness": 0.15, "order": 3},
                    {"layer_id": "layer_cpdd2", "name": "Cấp phối đá dăm Loại 2", "material": "crushed_stone_class_2", "thickness": 0.25, "order": 4},
                    {"layer_id": "layer_k98", "name": "Đáy áo đường K98", "material": "compacted_subgrade_k98", "thickness": 0.30, "order": 5},
                ],
                "side_slopes": {
                    "left": {
                        "slope_ratio": 1.0,  # 1:1 cut or fill
                        "is_cut": True,
                        "ditch": {"ditch_type": "trapezoidal_masonry", "depth": 0.4, "bottom_width": 0.4},
                    },
                    "right": {
                        "slope_ratio": 1.0,
                        "is_cut": True,
                        "ditch": {"ditch_type": "trapezoidal_masonry", "depth": 0.4, "bottom_width": 0.4},
                    },
                },
            },
        }
        res = validate_plan_spec(spec)
        self.assertTrue(res.valid, f"Validation failed with: {res.errors}")
        self.assertEqual(res.verdict, "APPROVED_FOR_EXECUTION")
        self.assertEqual(res.feature_count, 6)


if __name__ == "__main__":
    unittest.main()
