"""Comprehensive Injected Fault & Recovery Matrix (ENG-C09).
Wing: code | Topic: fault-recovery-matrix | Updated: 2026-10-03

Proves the four-quadrant failure & recovery lifecycle:
1. Early failure: malformed chunk rejected before mutation; no state change.
2. Middle failure: execution failure rolls back; prior committed chunk preserved.
3. Uncertain failure: transport timeout / dropped receipt reconciled from observation; no blind replay.
4. Late failure: post-execution seal/hash drift blocks final release_bundle_check.
5. Clean bundle verification: release_bundle_check PASS when all 4 recovery classes have evidence.
"""
from __future__ import annotations

import hashlib
import unittest
from typing import Any

from execution.chunk_recovery import (
    execute_chunk_with_recovery,
    fingerprint_state,
)
from execution.release_bundle import assess_release_bundle


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _MatrixExecutor:
    """Mock executor allowing dynamic fault injection per chunk_id."""

    def __init__(self, fault_schedule: dict[str, str] | None = None) -> None:
        self.fault_schedule = dict(fault_schedule or {})
        self.state: dict[str, dict[str, Any]] = {}
        self.call_count: dict[str, int] = {}
        self.compensated: list[str] = []

    def execute(self, chunk: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        cid = chunk["chunk_id"]
        self.call_count[cid] = self.call_count.get(cid, 0) + 1
        fault = self.fault_schedule.get(cid)

        if fault == "early_reject":
            return {"outcome": "failed", "error": f"preflight_rejected:{cid}"}

        if fault == "middle_crash":
            return {"outcome": "failed", "error": f"mutation_aborted:{cid}"}

        if fault == "uncertain_timeout":
            # Mutates successfully but raises transport exception
            self.state[cid] = dict(chunk.get("semantic_params", {}))
            raise TimeoutError(f"transport_timeout:{cid}")

        # Normal success
        self.state[cid] = dict(chunk.get("semantic_params", {}))
        return {
            "outcome": "committed",
            "chunk_id": cid,
            "state": dict(self.state[cid]),
        }

    def observe(self, chunk_id: str) -> dict[str, Any]:
        if chunk_id not in self.state:
            return {}
        return dict(self.state[chunk_id])

    def compensate(self, chunk_id: str) -> None:
        self.compensated.append(chunk_id)
        self.state.pop(chunk_id, None)


class FaultRecoveryMatrixTests(unittest.TestCase):
    def test_01_early_failure_fails_before_mutation(self) -> None:
        executor = _MatrixExecutor({"chunk_01": "early_reject"})
        chunk = {
            "chunk_id": "chunk_01",
            "semantic_type": "grid_axes",
            "semantic_params": {"axis_A": {"start": [0, 0], "end": [10, 0]}},
        }
        res = execute_chunk_with_recovery(
            chunk=chunk,
            execute=executor.execute,
            observe=executor.observe,
            compensate=executor.compensate,
            max_attempts=2,
        )
        self.assertEqual("blocked", res.final)
        # Engine state was never mutated
        self.assertEqual({}, executor.observe("chunk_01"))

    def test_02_middle_failure_preserves_predecessor_and_blocks_downstream(self) -> None:
        executor = _MatrixExecutor({"chunk_02": "middle_crash"})

        chunk_1 = {
            "chunk_id": "chunk_01",
            "semantic_type": "grid_axes",
            "semantic_params": {"axis_1": {"start": [0, 0], "end": [5000, 0]}},
        }
        res1 = execute_chunk_with_recovery(
            chunk=chunk_1,
            execute=executor.execute,
            observe=executor.observe,
            compensate=executor.compensate,
        )
        self.assertEqual("committed", res1.final)

        # Predecessor fingerprint
        c1_fp = fingerprint_state(executor.observe("chunk_01"))

        chunk_2 = {
            "chunk_id": "chunk_02",
            "semantic_type": "wall_shell",
            "semantic_params": {"wall_1": {"thickness": 220}},
        }
        res2 = execute_chunk_with_recovery(
            chunk=chunk_2,
            execute=executor.execute,
            observe=executor.observe,
            compensate=executor.compensate,
        )
        self.assertEqual("blocked", res2.final)

        # Predecessor chunk 1 state is intact and unchanged
        self.assertEqual(c1_fp, fingerprint_state(executor.observe("chunk_01")))
        self.assertEqual({}, executor.observe("chunk_02"))

    def test_03_uncertain_timeout_reconciles_and_prevents_duplicate_replay(self) -> None:
        executor = _MatrixExecutor({"chunk_01": "uncertain_timeout"})
        chunk = {
            "chunk_id": "chunk_01",
            "semantic_type": "wall_shell",
            "semantic_params": {"wall_A": {"length": 6000}},
        }
        res = execute_chunk_with_recovery(
            chunk=chunk,
            execute=executor.execute,
            observe=executor.observe,
            compensate=executor.compensate,
            max_attempts=3,
        )
        self.assertEqual("committed", res.final)
        # Exactly 1 call executed; no duplicate replay
        self.assertEqual(1, executor.call_count["chunk_01"])

    def test_04_late_failure_blocks_release_bundle_when_artifact_stale(self) -> None:
        valid_src = _sha("src_model_1")
        valid_art = _sha("dwg_out_1")
        tampered_art = _sha("dwg_tampered")

        bundle = {
            "run_id": "run-001",
            "design_basis_revision": "db-r1",
            "source_hashes": [
                {"source_id": "src-1", "sha256": valid_src, "verification_state": "verified"}
            ],
            "version_bindings": {
                "domain": "building-architecture@0.2.2",
                "workflow": "reconstruction@0.2.0",
                "engineer_source_revision": "0970711",
                "engineer_provider_version": "0.1.0a4",
                "engineer_contract_version": "cdt-engineer-v1-alpha4",
                "engineer_wheel_sha256": _sha("wheel_bytes"),
            },
            "runtime_identity": {
                "provider": "autocad",
                "provider_version": "0.4.0rc3",
                "contract_version": "autocad-generic-v1-rc3",
                "application_version": "AutoCAD 2027",
            },
            "artifacts": [
                {
                    "artifact_id": "drawing",
                    "sha256": valid_art,
                    "reopened": True,
                    "sealed": True,
                }
            ],
            "checker_evidence": {
                "verdict": "PASS_FOR_DECLARED_SCOPE",
                "reviewer_role": "Checker / QA Engineer",
                "independent": True,
                "evidence_sha256": _sha("checker_evidence"),
                "artifact_bindings": {"drawing": valid_art},
            },
            "required_recovery_classes": ["early", "middle", "late", "uncertain"],
            "recovery_negative_evidence": [
                {"case_id": "c_early", "recovery_class": "early", "result": "pass", "evidence_sha256": _sha("ev_early")},
                {"case_id": "c_mid", "recovery_class": "middle", "result": "pass", "evidence_sha256": _sha("ev_middle")},
                {"case_id": "c_late", "recovery_class": "late", "result": "pass", "evidence_sha256": _sha("ev_late")},
                {"case_id": "c_unc", "recovery_class": "uncertain", "result": "pass", "evidence_sha256": _sha("ev_unc")},
            ],
        }

        # Stale artifact on disk
        res = assess_release_bundle(
            bundle,
            current_source_hashes={"src-1": valid_src},
            current_artifact_hashes={"drawing": tampered_art},
            current_runtime_identity={
                "provider": "autocad",
                "provider_version": "0.4.0rc3",
                "contract_version": "autocad-generic-v1-rc3",
                "application_version": "AutoCAD 2027",
            },
        )
        self.assertEqual("blocked", res["result"])
        self.assertIn("artifact_hash_mismatch:drawing", res["reason_codes"])

    def test_05_clean_release_bundle_passes_when_all_recovery_classes_verified(self) -> None:
        src_h = _sha("src_v2")
        art_h = _sha("dwg_v2")
        bundle = {
            "run_id": "run-002",
            "design_basis_revision": "db-r2",
            "source_hashes": [
                {"source_id": "src-1", "sha256": src_h, "verification_state": "verified"}
            ],
            "version_bindings": {
                "domain": "building-architecture@0.2.2",
                "workflow": "reconstruction@0.2.0",
                "engineer_source_revision": "0970711",
                "engineer_provider_version": "0.1.0a4",
                "engineer_contract_version": "cdt-engineer-v1-alpha4",
                "engineer_wheel_sha256": _sha("wheel_bytes_v2"),
            },
            "runtime_identity": {
                "provider": "autocad",
                "provider_version": "0.4.0rc3",
                "contract_version": "autocad-generic-v1-rc3",
                "application_version": "AutoCAD 2027",
            },
            "artifacts": [
                {
                    "artifact_id": "drawing",
                    "sha256": art_h,
                    "reopened": True,
                    "sealed": True,
                }
            ],
            "checker_evidence": {
                "verdict": "PASS_FOR_DECLARED_SCOPE",
                "reviewer_role": "Checker / QA Engineer",
                "independent": True,
                "evidence_sha256": _sha("checker_evidence_v2"),
                "artifact_bindings": {"drawing": art_h},
            },
            "required_recovery_classes": ["early", "middle", "late", "uncertain"],
            "recovery_negative_evidence": [
                {"case_id": "c1", "recovery_class": "early", "result": "pass", "evidence_sha256": _sha("rec1")},
                {"case_id": "c2", "recovery_class": "middle", "result": "pass", "evidence_sha256": _sha("rec2")},
                {"case_id": "c3", "recovery_class": "uncertain", "result": "pass", "evidence_sha256": _sha("rec3")},
                {"case_id": "c4", "recovery_class": "late", "result": "pass", "evidence_sha256": _sha("rec4")},
            ],
        }

        res = assess_release_bundle(
            bundle,
            current_source_hashes={"src-1": src_h},
            current_artifact_hashes={"drawing": art_h},
            current_runtime_identity={
                "provider": "autocad",
                "provider_version": "0.4.0rc3",
                "contract_version": "autocad-generic-v1-rc3",
                "application_version": "AutoCAD 2027",
            },
        )
        self.assertEqual("pass", res["result"])
        self.assertEqual([], res["reason_codes"])


if __name__ == "__main__":
    unittest.main()
