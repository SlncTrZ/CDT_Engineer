"""Tests for forced-uncertainty chunk recovery (ENG-R05).
Wing: code | Topic: chunk-recovery | Updated: 2026-09-18 02:00
"""
from __future__ import annotations

import unittest
from execution.chunk_recovery import (
    execute_chunk_with_recovery,
    fingerprint_state,
    reconcile,
)


class _TransportUncertain(Exception):
    """Simulated lost receipt: mutation may or may not have committed."""


class _ScriptedExecutor:
    """Fault-injection double with a persistent state store and idempotency keys.

    Behaviors per call: success | timeout_after_commit | partial | fail | count_mimic.
    The observer reads the state store independently of (possibly lost) receipts.
    """

    def __init__(self, behaviors):
        self._behaviors = dict(behaviors)
        self._calls: dict[str, int] = {}
        self.state_store: dict[str, dict] = {}
        self.seen_keys: list[str] = []

    @property
    def calls(self):
        return dict(self._calls)

    def _next(self, chunk_id):
        n = self._calls.get(chunk_id, 0)
        self._calls[chunk_id] = n + 1
        script = self._behaviors.get(chunk_id, ["success"])
        return script[min(n, len(script) - 1)]

    def execute(self, chunk, idempotency_key):
        self.seen_keys.append(idempotency_key)
        chunk_id = chunk["chunk_id"]
        behavior = self._next(chunk_id)
        full = {fid: params for fid, params in chunk["semantic_params"].items()}
        if behavior == "success":
            self.state_store[chunk_id] = dict(full)
            return {"outcome": "committed", "state": dict(full)}
        if behavior == "timeout_after_commit":
            self.state_store[chunk_id] = dict(full)
            raise _TransportUncertain(f"receipt lost for {chunk_id}")
        if behavior == "partial":
            part = dict(list(full.items())[:1])
            self.state_store[chunk_id] = part
            raise _TransportUncertain(f"interrupted {chunk_id}")
        if behavior == "fail":
            # Explicit failure receipt: no state mutated, safe to retry.
            return {"outcome": "failed", "error": f"explicit failure {chunk_id}"}
        if behavior == "count_mimic":
            # Same COUNT, wrong identity: count-only checks would pass.
            mimic = {f"impostor_{i}": {"params": "wrong"} for i in range(len(full))}
            self.state_store[chunk_id] = mimic
            return {"outcome": "committed", "state": dict(mimic)}
        raise AssertionError(f"unknown behavior {behavior}")

    def compensate(self, chunk_id):
        self.state_store.pop(chunk_id, None)
        return {"compensated": chunk_id}

    def observe(self, chunk_id):
        state = self.state_store.get(chunk_id)
        return None if state is None else dict(state)


def _chunk(chunk_id="plan:wall_shell:01"):
    params = {"wall_w1": {"length": 5000.0}, "wall_w2": {"length": 4000.0}}
    return {"chunk_id": chunk_id, "semantic_type": "wall_shell",
            "feature_ids": ["wall_w1", "wall_w2"], "semantic_params": params}


class TestChunkRecovery(unittest.TestCase):
    def test_clean_success_commits_first_attempt(self):
        ex = _ScriptedExecutor({})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "committed")
        self.assertEqual(record.attempts, 1)
        self.assertEqual(ex.calls, {"plan:wall_shell:01": 1})

    def test_timeout_after_commit_adopts_without_replay(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["timeout_after_commit"]})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "committed")
        self.assertIn("adopted_without_replay", record.decisions)
        # The one uncertain call is the only mutation: no blind replay.
        self.assertEqual(ex.calls, {"plan:wall_shell:01": 1})

    def test_partial_commit_compensates_before_retry(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["partial", "success"]})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "committed")
        self.assertIn("compensated_partial_state", record.decisions)
        self.assertNotIn("blind_replay", record.decisions)
        # After compensation + retry, the store holds exactly the full set.
        self.assertEqual(set(ex.observe("plan:wall_shell:01").keys()), {"wall_w1", "wall_w2"})

    def test_explicit_fail_retries_then_commits(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["fail", "success"]})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "committed")
        self.assertEqual(record.attempts, 2)

    def test_uncertain_without_observation_verifies_first(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["timeout_after_commit"]})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, lambda _cid: None, ex.compensate)
        # Observer blind: must verify before deciding; state exists but
        # unverifiable -> blocked, never replayed blindly.
        self.assertEqual(record.final, "blocked")
        self.assertIn("verify_first_no_observation", record.decisions)
        self.assertEqual(ex.calls, {"plan:wall_shell:01": 1})

    def test_attempts_exhausted_blocks(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["fail", "fail", "fail", "fail"]})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate,
                                             max_attempts=3)
        self.assertEqual(record.final, "blocked")
        self.assertEqual(record.attempts, 3)
        self.assertIn("attempt_budget_exhausted", record.decisions)

    def test_count_match_with_wrong_identity_blocks(self):
        # count_mimic stores 2 ids like expected, but impostor identity.
        # A count-only check would PASS; fingerprint comparison must BLOCK.
        expected_fp = fingerprint_state(dict(_chunk()["semantic_params"]))
        observed = {"impostor_0": {"params": "wrong"}, "impostor_1": {"params": "wrong"}}
        decision = reconcile(expected_fp, ["wall_w1", "wall_w2"], observed,
                             last_outcome="committed", attempts_used=1, max_attempts=3)
        self.assertEqual(decision["decision"], "blocked")
        self.assertTrue(any("fingerprint_mismatch" in r for r in decision["reasons"]))
        self.assertEqual(len(observed), 2)  # counts match: proof count-only is insufficient

    def test_committed_receipt_with_mismatched_state_blocks(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["count_mimic"]})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "blocked")
        self.assertTrue(any("fingerprint_mismatch" in d for d in record.decisions))

    def test_retry_reuses_idempotency_key(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["fail", "success"]})
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "committed")
        self.assertEqual(len(ex.seen_keys), 2)
        self.assertEqual(ex.seen_keys[0], ex.seen_keys[1])
        self.assertTrue(ex.seen_keys[0].startswith("plan:wall_shell:01:"))

    def test_ia01_committed_receipt_with_empty_observation_blocks(self):
        # Producer claims committed + expected state, but independent
        # observation shows empty: the receipt must not become a commit.
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["success"]})
        calls = []
        inner = ex.observe
        ex.observe = lambda cid: calls.append(cid) or {}
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "blocked")
        self.assertEqual(len(calls), 1)
        self.assertTrue(any("fingerprint_mismatch" in d for d in record.decisions))

    def test_ia01_committed_receipt_with_blind_observer_blocks(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["success"]})
        def _blind(_cid):
            raise RuntimeError("observer down")
        record = execute_chunk_with_recovery(_chunk(), ex.execute, _blind, ex.compensate)
        self.assertEqual(record.final, "blocked")
        self.assertTrue(any("committed_receipt_without_observable_state" in d
                            for d in record.decisions))

    def test_ia02_compensation_noop_blocks_without_second_execute(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["partial", "success"]})
        ex.compensate = lambda _cid: False  # no-op: store keeps partial state
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "blocked")
        self.assertIn("compensation_unverified_state_remains", record.decisions)
        self.assertEqual(ex.calls, {"plan:wall_shell:01": 1})

    def test_ia02_compensation_exception_blocks(self):
        ex = _ScriptedExecutor({"plan:wall_shell:01": ["partial", "success"]})
        def _boom(_cid):
            raise RuntimeError("compensator down")
        ex.compensate = _boom
        record = execute_chunk_with_recovery(_chunk(), ex.execute, ex.observe, ex.compensate)
        self.assertEqual(record.final, "blocked")
        self.assertTrue(any(d.startswith("compensation_failed") for d in record.decisions))
        self.assertEqual(ex.calls, {"plan:wall_shell:01": 1})

    def test_reconcile_pure_function_matrix(self):
        fp = fingerprint_state({"a": {"x": 1}})
        # Uncertain + full match -> adopt, no replay.
        d = reconcile(fp, ["a"], {"a": {"x": 1}}, last_outcome="uncertain",
                      attempts_used=1, max_attempts=3)
        self.assertEqual(d["decision"], "adopted")
        # Uncertain + partial -> compensate, never blind replay.
        d = reconcile(fp, ["a", "b"], {"a": {"x": 1}}, last_outcome="uncertain",
                      attempts_used=1, max_attempts=3)
        self.assertEqual(d["decision"], "compensate")
        # Uncertain + no observation -> verify first.
        d = reconcile(fp, ["a"], None, last_outcome="uncertain",
                      attempts_used=1, max_attempts=3)
        self.assertEqual(d["decision"], "verify_first")
        # Failed pre-mutation with budget -> retry.
        d = reconcile(fp, ["a"], None, last_outcome="failed", attempts_used=1, max_attempts=3)
        self.assertEqual(d["decision"], "retry")


if __name__ == "__main__":
    unittest.main()
