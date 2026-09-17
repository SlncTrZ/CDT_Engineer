"""Integration: compile -> recovery -> receipt -> release with fault injection (IA-04).
Wing: code | Topic: pipeline-recovery-integration | Updated: 2026-09-18 02:40
"""
from __future__ import annotations

import unittest
from execution.chunk_recovery import (
    chunk_to_recovery_params,
    execute_chunk_with_recovery,
)
from execution.plan_compiler import compile_plan_spec
from execution.provenance_release import assess_provenance_release, build_chunk_receipt


def _arch_spec(plan_id="ia04_integration"):
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
            "window_w1": {"status": "specified", "source_id": "s1", "assumption_id": None, "confidence": 1.0},
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
                {"opening_id": "window_w1", "host_wall_id": "wall_w2", "opening_type": "window",
                 "offset_along_wall": 1000.0, "width": 1200.0, "height": 1500.0,
                 "sill_height": 900.0, "head_height": 2400.0},
            ],
        },
    }


class _FaultyLane:
    """Lane double with scripted faults, state store, independent observer."""

    def __init__(self, script):
        self._script = dict(script)
        self.calls: dict[str, int] = {}
        self.store: dict[str, dict] = {}

    def _behavior(self, chunk_id):
        n = self.calls.get(chunk_id, 0)
        self.calls[chunk_id] = n + 1
        seq = self._script.get(chunk_id, ["success"])
        return seq[min(n, len(seq) - 1)]

    def execute(self, chunk, key):  # noqa: ARG002 - key recorded by caller contract
        params = dict(chunk["semantic_params"])
        behavior = self._behavior(chunk["chunk_id"])
        if behavior == "success":
            self.store[chunk["chunk_id"]] = dict(params)
            return {"outcome": "committed", "state": dict(params)}
        if behavior == "timeout_after_commit":
            self.store[chunk["chunk_id"]] = dict(params)
            raise TimeoutError(f"receipt lost {chunk['chunk_id']}")
        if behavior == "partial":
            part = dict(list(params.items())[:1])
            self.store[chunk["chunk_id"]] = part
            raise TimeoutError(f"interrupted {chunk['chunk_id']}")
        raise AssertionError(f"unknown behavior {behavior}")

    def observe(self, chunk_id):
        state = self.store.get(chunk_id)
        return None if state is None else dict(state)

    def compensate(self, chunk_id):
        self.store.pop(chunk_id, None)
        return {"compensated": chunk_id}


class TestCompileRecoveryIntegration(unittest.TestCase):
    def test_adapter_rejects_malformed_chunks(self):
        with self.assertRaises(ValueError):
            chunk_to_recovery_params({"chunk_id": "c1"})
        with self.assertRaises(ValueError):
            chunk_to_recovery_params({"chunk_id": "c1", "feature_ids": ["a"],
                                      "features": [{"x": 1}, {"y": 2}]})
        with self.assertRaises(ValueError):
            chunk_to_recovery_params({"chunk_id": "c1", "feature_ids": ["a"],
                                      "features": ["not-a-mapping"]})

    def test_compile_recovery_receipt_release_with_faults(self):
        compiled = compile_plan_spec(_arch_spec())
        self.assertTrue(compiled.ok, f"errors: {compiled.errors}")
        by_type = {c["semantic_type"]: c for c in compiled.chunks}
        lane = _FaultyLane({
            by_type["wall_shell"]["chunk_id"]: ["timeout_after_commit"],
            by_type["openings"]["chunk_id"]: ["partial", "success"],
        })
        receipts = []
        for chunk in compiled.chunks:
            recovery_chunk = {"chunk_id": chunk["chunk_id"],
                              "semantic_params": chunk_to_recovery_params(chunk)}
            record = execute_chunk_with_recovery(recovery_chunk, lane.execute,
                                                 lane.observe, lane.compensate)
            self.assertEqual(record.final, "committed", f"{chunk['chunk_id']}: {record.decisions}")
            receipts.append(build_chunk_receipt(chunk, engine_receipt_id=f"sim-{chunk['chunk_id']}",
                                                created_or_modified_ids=list(chunk["feature_ids"]),
                                                transaction_mode="checkpointed_atomic"))
        # Uncertain wall_shell adopted with exactly one mutation call.
        wall_id = by_type["wall_shell"]["chunk_id"]
        self.assertEqual(lane.calls[wall_id], 1)
        # Partial openings compensated then retried exactly once more.
        openings_id = by_type["openings"]["chunk_id"]
        self.assertEqual(lane.calls[openings_id], 2)
        release = assess_provenance_release(receipts, "design_review")
        self.assertEqual(release["result"], "pass", f"reason_codes: {release['reason_codes']}")


if __name__ == "__main__":
    unittest.main()
