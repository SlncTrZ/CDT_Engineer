"""Tests for feature-level provenance receipts and release QA (ENG-R11).
Wing: code | Topic: provenance-release | Updated: 2026-09-18 01:15
"""
from __future__ import annotations

import unittest
from execution.plan_compiler import compile_plan_spec
from execution.provenance_release import assess_provenance_release, build_chunk_receipt


def _receipt(chunk_id="plan:wall_shell:01", provenance=None):
    return {
        "chunk_id": chunk_id,
        "batch_session_id": "plan",
        "semantic_type": "wall_shell",
        "feature_ids": list((provenance or {"wall_w1": "specified"}).keys()),
        "provenance": dict(provenance or {"wall_w1": "specified"}),
        "status": "committed",
        "transaction_mode": "checkpointed_atomic",
        "engine_receipt_id": "eng-001",
        "created_or_modified_ids": ["wall_w1"],
        "verification": {"status": "pass"},
        "artifact_revision": "rev-001",
    }


def _arch_spec(plan_id="arch_prov_e2e"):
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
    }


class TestProvenanceRelease(unittest.TestCase):
    def test_strong_provenance_passes_design_review(self):
        res = assess_provenance_release(
            [_receipt(provenance={"wall_w1": "specified", "door_d1": "derived"})],
            "design_review",
        )
        self.assertEqual(res["result"], "pass")
        self.assertEqual(res["effective_release_target"], "design_review")

    def test_inferred_blocks_design_review_but_passes_concept(self):
        receipts = [_receipt(provenance={"wall_w1": "inferred"})]
        blocked = assess_provenance_release(receipts, "design_review")
        self.assertEqual(blocked["result"], "blocked")
        self.assertTrue(any("provenance_blocks_release" in r and "wall_w1" in r
                            for r in blocked["reason_codes"]))
        self.assertEqual(blocked["recommended_release_target"], "concept")
        concept = assess_provenance_release(receipts, "concept")
        self.assertEqual(concept["result"], "pass")
        self.assertTrue(any("inferred" in lim for lim in concept["limitations"]))

    def test_unknown_provenance_blocks_everything(self):
        receipts = [_receipt(provenance={"wall_w1": "unknown"})]
        for target in ("concept", "technical_draft", "design_review"):
            res = assess_provenance_release(receipts, target)
            self.assertEqual(res["result"], "blocked", f"target={target}")
            self.assertTrue(any("unknown_provenance_blocks_release" in r for r in res["reason_codes"]))

    def test_receipt_builder_carries_provenance(self):
        chunk = {"chunk_id": "plan:wall_shell:01", "batch_session_id": "plan",
                 "semantic_type": "wall_shell", "feature_ids": ["wall_w1"],
                 "provenance": {"wall_w1": "approved_assumption"}}
        receipt = build_chunk_receipt(chunk, engine_receipt_id="eng-9",
                                      created_or_modified_ids=["wall_w1"],
                                      transaction_mode="compensating")
        self.assertEqual(receipt["chunk_id"], "plan:wall_shell:01")
        self.assertEqual(receipt["provenance"], {"wall_w1": "approved_assumption"})
        self.assertEqual(receipt["transaction_mode"], "compensating")
        self.assertEqual(receipt["verification"], {"status": "pass"})

    def test_receipt_builder_rejects_malformed_chunk(self):
        with self.assertRaises(ValueError):
            build_chunk_receipt({"semantic_type": "wall_shell"}, engine_receipt_id="e1",
                                created_or_modified_ids=["w1"], transaction_mode="compensating")
        with self.assertRaises(ValueError):
            build_chunk_receipt({"chunk_id": "c1", "feature_ids": ["w1"],
                                 "provenance": {"w1": "guessed"}},
                                engine_receipt_id="e1", created_or_modified_ids=["w1"],
                                transaction_mode="compensating")

    def test_approved_assumption_needs_ledger_linkage(self):
        receipts = [_receipt(provenance={"wall_w1": "approved_assumption"})]
        ledger = {"wall_w1": {"status": "approved_assumption", "source_id": None,
                              "assumption_id": "asm_wall_thick", "confidence": 0.9}}
        linked = assess_provenance_release(receipts, "design_review", plan_ledger=ledger)
        self.assertEqual(linked["result"], "pass")
        unlinked = assess_provenance_release(receipts, "design_review", plan_ledger={})
        self.assertEqual(unlinked["result"], "blocked")
        self.assertTrue(any(("assumption_link_missing" in r or "provenance_ledger_missing" in r)
                            and "wall_w1" in r for r in unlinked["reason_codes"]))

    def test_empty_receipts_blocked(self):
        res = assess_provenance_release([], "concept")
        self.assertEqual(res["result"], "blocked")
        self.assertIn("no_chunk_receipts", res["reason_codes"])

    def test_invalid_release_target_raises(self):
        with self.assertRaises(ValueError):
            assess_provenance_release([_receipt()], "issued_for_construction")

    def test_one_weak_feature_blocks_stronger_release(self):
        receipts = [
            _receipt("plan:wall_shell:01", {"wall_w1": "specified", "wall_w2": "specified"}),
            _receipt("plan:openings:01", {"door_d1": "inferred"}),
        ]
        res = assess_provenance_release(receipts, "technical_draft")
        self.assertEqual(res["result"], "blocked")
        self.assertTrue(any("door_d1" in r for r in res["reason_codes"]))
        self.assertEqual(res["feature_count"], 3)

    def test_ia03_empty_provenance_with_features_blocks(self):
        receipt = _receipt()
        receipt["feature_ids"] = ["missing"]
        receipt["provenance"] = {}
        for target in ("concept", "design_review", "ready_for_professional_review"):
            res = assess_provenance_release([receipt], target)
            self.assertEqual(res["result"], "blocked", f"target={target}")
            self.assertTrue(any("provenance_coverage_missing" in r and "missing" in r
                                for r in res["reason_codes"]))
        self.assertEqual(res["feature_count"], 0)

    def test_ia03_ledger_contradiction_blocks(self):
        receipts = [_receipt(provenance={"f": "specified"})]
        ledger = {"f": {"status": "unknown", "source_id": None,
                        "assumption_id": None, "confidence": None}}
        res = assess_provenance_release(receipts, "design_review", plan_ledger=ledger)
        self.assertEqual(res["result"], "blocked")
        self.assertTrue(any("provenance_ledger_contradiction" in r and ":f:" in r
                            for r in res["reason_codes"]))

    def test_ia03_failed_verification_receipt_never_committed(self):
        chunk = {"chunk_id": "c1", "batch_session_id": "plan", "semantic_type": "wall_shell",
                 "feature_ids": ["w1"], "provenance": {"w1": "specified"}}
        receipt = build_chunk_receipt(chunk, engine_receipt_id="e1",
                                      created_or_modified_ids=[],
                                      transaction_mode="nonrecoverable",
                                      verification_status="fail")
        self.assertEqual(receipt["status"], "verification_failed")
        res = assess_provenance_release([receipt], "concept")
        self.assertEqual(res["result"], "blocked")
        self.assertTrue(any("receipt_not_committed:c1" in r for r in res["reason_codes"]))

    def test_ia03_invalid_ledger_status_raises(self):
        receipts = [_receipt(provenance={"f": "specified"})]
        with self.assertRaises(ValueError):
            assess_provenance_release(receipts, "design_review",
                                      plan_ledger={"f": {"status": "guessed"}})

    def test_end_to_end_compile_receipts_release(self):
        compiled = compile_plan_spec(_arch_spec())
        self.assertTrue(compiled.ok, f"errors: {compiled.errors}")
        receipts = [build_chunk_receipt(c, engine_receipt_id=f"eng-{i}",
                                        created_or_modified_ids=list(c["feature_ids"]),
                                        transaction_mode="checkpointed_atomic")
                    for i, c in enumerate(compiled.chunks)]
        res = assess_provenance_release(receipts, "design_review")
        self.assertEqual(res["result"], "pass", f"reason_codes: {res['reason_codes']}")
        self.assertEqual(res["receipt_count"], len(compiled.chunks))
        self.assertEqual(res["feature_count"], compiled.feature_count)


if __name__ == "__main__":
    unittest.main()
