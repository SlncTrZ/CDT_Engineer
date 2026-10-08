"""E3 common invariants: observation truth and dependency-impact invalidation.
Wing: code | Topic: e3-common-invariants | Updated: 2026-09-19
"""
from __future__ import annotations

import unittest

from execution.impact_graph import assess_evidence_freshness, compute_impact
from execution.observation import assess_observation


class ImpactGraphTests(unittest.TestCase):
    def nodes(self):
        return [
            {"node_id": "source", "revision": "S2", "depends_on": []},
            {"node_id": "model", "revision": "M3", "depends_on": ["source"]},
            {"node_id": "drawing", "revision": "D4", "depends_on": ["model"]},
            {"node_id": "handoff", "revision": "H4", "depends_on": ["drawing"]},
            {"node_id": "independent", "revision": "I1", "depends_on": []},
        ]

    def test_change_propagates_transitively_without_invalidating_independent_branch(self):
        result = compute_impact(self.nodes(), ["source"])
        self.assertEqual(
            result["impacted_ids"],
            ["source", "model", "drawing", "handoff"],
        )
        self.assertEqual(result["unaffected_ids"], ["independent"])

    def test_evidence_binds_subject_and_transitive_dependency_revisions(self):
        evidence = [
            {
                "evidence_id": "ev-drawing",
                "subject_id": "drawing",
                "bound_revisions": {"source": "S2", "model": "M3", "drawing": "D4"},
            },
            {
                "evidence_id": "ev-independent",
                "subject_id": "independent",
                "bound_revisions": {"independent": "I1"},
            },
        ]
        result = assess_evidence_freshness(self.nodes(), evidence)
        self.assertEqual(result["stale_evidence_ids"], [])
        self.assertEqual(result["current_evidence_ids"], ["ev-drawing", "ev-independent"])

    def test_old_source_revision_stales_dependent_evidence_only(self):
        evidence = [
            {
                "evidence_id": "ev-drawing",
                "subject_id": "drawing",
                "bound_revisions": {"source": "S1", "model": "M3", "drawing": "D4"},
            },
            {
                "evidence_id": "ev-independent",
                "subject_id": "independent",
                "bound_revisions": {"independent": "I1"},
            },
        ]
        result = assess_evidence_freshness(self.nodes(), evidence)
        self.assertEqual(result["stale_evidence_ids"], ["ev-drawing"])
        self.assertEqual(result["current_evidence_ids"], ["ev-independent"])
        self.assertIn("revision_mismatch:source", result["reason_codes"]["ev-drawing"])

    def test_missing_transitive_binding_is_stale(self):
        evidence = [{
            "evidence_id": "ev-handoff",
            "subject_id": "handoff",
            "bound_revisions": {"drawing": "D4", "handoff": "H4"},
        }]
        result = assess_evidence_freshness(self.nodes(), evidence)
        self.assertEqual(result["stale_evidence_ids"], ["ev-handoff"])
        self.assertIn("binding_missing:source", result["reason_codes"]["ev-handoff"])
        self.assertIn("binding_missing:model", result["reason_codes"]["ev-handoff"])

    def test_cycle_and_dangling_dependency_fail_closed(self):
        with self.assertRaises(ValueError):
            compute_impact([
                {"node_id": "a", "revision": "1", "depends_on": ["b"]},
                {"node_id": "b", "revision": "1", "depends_on": ["a"]},
            ], ["a"])
        with self.assertRaises(ValueError):
            compute_impact([
                {"node_id": "a", "revision": "1", "depends_on": ["missing"]},
            ], ["a"])


class ObservationContractTests(unittest.TestCase):
    def observation(self, **changes):
        value = {
            "observation_id": "obs-1",
            "observer_id": "checker-path-1",
            "method": "native_object_query",
            "semantic_id": "wall-1",
            "native_id": "pid:wall-1",
            "observed_revision": "D4",
            "status": "observed",
            "state": {"wall-1": {"length": 5000.0, "layer": "A-WALL"}},
            "precision": 0.001,
            "confidence": 1.0,
        }
        value.update(changes)
        return value

    def test_independent_observation_passes_only_exact_identity_revision_and_state(self):
        result = assess_observation(
            self.observation(),
            expected_semantic_id="wall-1",
            expected_native_id="pid:wall-1",
            expected_revision="D4",
            expected_state={"wall-1": {"length": 5000.0, "layer": "A-WALL"}},
        )
        self.assertEqual(result["result"], "pass")

    def test_count_mimic_or_identity_substitution_blocks(self):
        mimic = self.observation(
            state={"impostor": {"length": 5000.0, "layer": "A-WALL"}},
        )
        result = assess_observation(
            mimic,
            expected_semantic_id="wall-1",
            expected_native_id="pid:wall-1",
            expected_revision="D4",
            expected_state={"wall-1": {"length": 5000.0, "layer": "A-WALL"}},
        )
        self.assertEqual(result["result"], "blocked")
        self.assertIn("state_fingerprint_mismatch", result["reason_codes"])

        substituted = assess_observation(
            self.observation(semantic_id="wall-2"),
            expected_semantic_id="wall-1",
            expected_native_id="pid:wall-1",
            expected_revision="D4",
        )
        self.assertEqual(substituted["result"], "blocked")
        self.assertIn("semantic_identity_mismatch", substituted["reason_codes"])

    def test_stale_revision_blocks_and_unavailable_is_unknown(self):
        stale = assess_observation(
            self.observation(observed_revision="D3"),
            expected_semantic_id="wall-1",
            expected_revision="D4",
        )
        self.assertEqual(stale["result"], "blocked")
        self.assertIn("observation_revision_stale", stale["reason_codes"])

        unavailable = assess_observation(
            self.observation(status="unavailable", state=None),
            expected_semantic_id="wall-1",
            expected_revision="D4",
        )
        self.assertEqual(unavailable["result"], "unknown")
        self.assertIn("observation_unavailable", unavailable["reason_codes"])

    def test_explicit_absence_requires_absence_expectation(self):
        absent = self.observation(status="absent", state={})
        blocked = assess_observation(
            absent,
            expected_semantic_id="wall-1",
            expected_revision="D4",
        )
        self.assertEqual(blocked["result"], "blocked")
        self.assertIn("unexpected_absence", blocked["reason_codes"])

        passed = assess_observation(
            absent,
            expected_semantic_id="wall-1",
            expected_revision="D4",
            expect_absent=True,
        )
        self.assertEqual(passed["result"], "pass")


if __name__ == "__main__":
    unittest.main()
