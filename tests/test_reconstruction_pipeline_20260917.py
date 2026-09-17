"""End-to-end reconstruction pipeline benchmark (ENG-R10 / Benchmark M).
Wing: code | Topic: reconstruction-pipeline | Updated: 2026-09-18 01:40
"""
from __future__ import annotations

import hashlib
import json
import unittest
from execution.plan_compiler import compile_plan_spec
from execution.provenance_release import assess_provenance_release, build_chunk_receipt
from execution.source_calibration import calibrate_plan_source

IMAGE = "_test_workspace/references/Test6_House_3_Floors_Layout.jpg"
ANCHOR_MM = 15000.0


def _image_size():
    from PIL import Image
    with Image.open(IMAGE) as im:
        return im.size


class _SimulatedAutocadLaneExecutor:
    """Explicit test-double for the AutoCAD 2D drafting lane. SIMULATED.

    Never native proof: it records chunk execution order, derives observed
    state deterministically from chunk semantic features, and lets the
    pipeline verify postconditions read-back style. Production runs must
    replace this double with the real CDT-AutoCAD executor evidence.
    """

    SIMULATED = True

    def __init__(self):
        self.executed: list[str] = []
        self.committed: set[str] = set()
        self.observed: dict[str, dict] = {}

    def execute(self, chunk):
        for dep in chunk["depends_on"]:
            if dep not in self.committed:
                raise AssertionError(f"dependent chunk released early: {chunk['chunk_id']} before {dep}")
        canonical = json.dumps(chunk["features"], sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.executed.append(chunk["chunk_id"])
        self.committed.add(chunk["chunk_id"])
        state = {"feature_ids": list(chunk["feature_ids"]),
                 "feature_count": len(chunk["feature_ids"]),
                 "fingerprint": fingerprint}
        self.observed[chunk["chunk_id"]] = state
        return state

    def read_back(self, chunk):
        return dict(self.observed[chunk["chunk_id"]])


def _run_calibration():
    width, height = _image_size()
    return calibrate_plan_source(
        source={"source_id": "test6_house_3_floors", "kind": "reference_image",
                "pixel_width": width, "pixel_height": height},
        pixel_features=[
            {"feature_id": "wall_w1", "kind": "polyline", "pixels": [[320.0, 200.0], [720.0, 200.0]]},
            {"feature_id": "wall_w2", "kind": "polyline", "pixels": [[720.0, 200.0], [720.0, 520.0]]},
        ],
        anchors=[{"anchor_id": "anchor_total_width",
                  "statement": "Toan bo chieu ngang mat bang = 15 000 mm (owner assumption)",
                  "pixel_from": [0.0, 0.0], "pixel_to": [float(width), 0.0],
                  "real_length": ANCHOR_MM, "unit": "mm", "confidence": 0.9}],
    )


def _planspec_from_calibration(cal):
    by_id = {f["feature_id"]: f for f in cal.features}
    w1 = by_id["wall_w1"]["coords_mm"]
    w2 = by_id["wall_w2"]["coords_mm"]
    return {
        "schema_version": "0.1.0",
        "plan_id": "benchmark_m_house",
        "domain_id": "building-architecture",
        "plan_type": "architectural_floor_plan",
        "units": {"length": "mm", "angle": "deg"},
        "coordinate_system": {
            "datum": "test6_calibrated_frame", "origin": [0.0, 0.0],
            "azimuth": 0.0, "scale": {"horizontal": 1.0, "vertical": 1.0},
        },
        "provenance_ledger": {
            "axis_A": {"status": "specified", "source_id": "benchmark_m", "assumption_id": None, "confidence": 1.0},
            "axis_1": {"status": "specified", "source_id": "benchmark_m", "assumption_id": None, "confidence": 1.0},
            "wall_w1": {"status": "derived", "source_id": "test6_house_3_floors", "assumption_id": None,
                        "confidence": cal.confidence},
            "wall_w2": {"status": "derived", "source_id": "test6_house_3_floors", "assumption_id": None,
                        "confidence": cal.confidence},
            "door_d1": {"status": "specified", "source_id": "benchmark_m", "assumption_id": None, "confidence": 1.0},
            "space_living": {"status": "derived", "source_id": None, "assumption_id": None, "confidence": 0.9},
            "dim_01": {"status": "derived", "source_id": None, "assumption_id": None, "confidence": 1.0},
        },
        "assumptions": [
            {"id": "anchor_total_width",
             "statement": "Toan bo chieu ngang mat bang = 15 000 mm (owner assumption)",
             "status": "approved_assumption"},
            {"id": "asm_wall_thick_220", "statement": "Exterior wall thickness assumed 220 mm",
             "status": "approved_assumption"},
        ],
        "payload": {
            "axes": [
                {"axis_id": "axis_A", "label": "A", "start": [w1[0][0], w1[0][1]], "end": [w1[1][0], w1[1][1]]},
                {"axis_id": "axis_1", "label": "1", "start": [w2[0][0], w2[0][1]], "end": [w2[1][0], w2[1][1]]},
            ],
            "walls": [
                {"wall_id": "wall_w1", "wall_type": "exterior", "thickness": 220.0,
                 "start": w1[0], "end": w1[1], "baseline": "center", "height": 3300.0},
                {"wall_id": "wall_w2", "wall_type": "exterior", "thickness": 220.0,
                 "start": w2[0], "end": w2[1], "baseline": "center", "height": 3300.0},
            ],
            "openings": [
                {"opening_id": "door_d1", "host_wall_id": "wall_w1", "opening_type": "door",
                 "offset_along_wall": 1000.0, "width": 900.0, "height": 2200.0,
                 "sill_height": 0.0, "head_height": 2200.0},
            ],
            "spaces": [
                {"space_id": "space_living", "name": "Living Room",
                 "boundary_polygon": [w1[0], w1[1], w2[1], [w1[0][0], w2[1][1]]],
                 "net_area": 20.0},
            ],
            "dimensions": [
                {"dimension_id": "dim_01", "dimension_type": "linear", "measured_value": 5000.0,
                 "witness_points": [w1[0], w1[1]], "feature_refs": ["wall_w1"]},
            ],
        },
    }


class TestReconstructionPipelineBenchmarkM(unittest.TestCase):
    def test_full_pipeline_passes_design_review(self):
        cal = _run_calibration()
        self.assertEqual(cal.verdict, "CALIBRATED")
        spec = _planspec_from_calibration(cal)
        compiled = compile_plan_spec(spec)  # validate + review gates inside
        self.assertTrue(compiled.ok, f"errors: {compiled.errors}")

        executor = _SimulatedAutocadLaneExecutor()
        self.assertTrue(executor.SIMULATED)
        for chunk in compiled.chunks:
            observed = executor.execute(chunk)
            read_back = executor.read_back(chunk)
            self.assertEqual(read_back["feature_ids"], chunk["feature_ids"])
            self.assertEqual(read_back["feature_count"], len(chunk["feature_ids"]))
            post = chunk["expected_outputs"]
            count_keys = [k for k in post if k.endswith("_count")]
            self.assertTrue(count_keys)
            # Primary count (max over breakdown keys) must match read-back.
            self.assertEqual(max(post[k] for k in count_keys),
                             read_back["feature_count"])

        receipts = [build_chunk_receipt(c, engine_receipt_id=f"sim-{i}",
                                        created_or_modified_ids=list(c["feature_ids"]),
                                        transaction_mode="checkpointed_atomic")
                    for i, c in enumerate(compiled.chunks)]
        release = assess_provenance_release(receipts, "design_review")
        self.assertEqual(release["result"], "pass", f"reason_codes: {release['reason_codes']}")

    def test_calibrated_dimension_fidelity(self):
        cal = _run_calibration()
        self.assertAlmostEqual(cal.frame["scale_unit_per_pixel"], 12.5, places=9)
        by_id = {f["feature_id"]: f for f in cal.features}
        # 400 px span at 12.5 mm/px -> 5000 mm wall in PlanSpec.
        w1 = by_id["wall_w1"]["coords_mm"]
        length = abs(w1[1][0] - w1[0][0])
        self.assertAlmostEqual(length, 5000.0, places=6)

    def test_openings_execute_after_wall_shell(self):
        compiled = compile_plan_spec(_planspec_from_calibration(_run_calibration()))
        self.assertTrue(compiled.ok)
        executor = _SimulatedAutocadLaneExecutor()
        for chunk in compiled.chunks:
            executor.execute(chunk)
        order = executor.executed
        wall_idx = next(i for i, cid in enumerate(order) if ":wall_shell:" in cid)
        opening_idx = next(i for i, cid in enumerate(order) if ":openings:" in cid)
        self.assertLess(wall_idx, opening_idx)

    def test_unapproved_plan_never_reaches_executor(self):
        spec = _planspec_from_calibration(_run_calibration())
        spec["payload"]["spaces"][0]["boundary_polygon"] = [
            [0.0, 0.0], [5000.0, 3000.0], [4000.0, 0.0], [1000.0, 4000.0],
        ]
        compiled = compile_plan_spec(spec)
        self.assertFalse(compiled.ok)
        executor = _SimulatedAutocadLaneExecutor()
        for chunk in compiled.chunks:
            executor.execute(chunk)
        self.assertEqual(executor.executed, [])

    def test_contradictory_calibration_blocks_pipeline_at_stage_one(self):
        width, height = _image_size()
        cal = calibrate_plan_source(
            source={"source_id": "test6_house_3_floors", "kind": "reference_image",
                    "pixel_width": width, "pixel_height": height},
            pixel_features=[],
            anchors=[
                {"anchor_id": "a1", "statement": "width 15m",
                 "pixel_from": [0.0, 0.0], "pixel_to": [float(width), 0.0],
                 "real_length": 15000.0, "unit": "mm", "confidence": 0.9},
                {"anchor_id": "a2", "statement": "conflicting width",
                 "pixel_from": [0.0, 0.0], "pixel_to": [float(width), 0.0],
                 "real_length": 16000.0, "unit": "mm", "confidence": 0.9},
            ],
        )
        self.assertEqual(cal.verdict, "CONTRADICTORY")
        # No frame -> no PlanSpec -> pipeline stops before CAD. Nothing to compile.
        self.assertEqual(cal.features, [])


if __name__ == "__main__":
    unittest.main()
