"""Lane A native/runtime contract regression tests.
Wing: code | Topic: native-runtime-acceptance | Updated: 2026-09-12 22:45
"""
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class NativeRuntimeLaneContractTests(unittest.TestCase):
    def test_sketchup_map_tracks_native_accepted_contract_and_strong_identity(self):
        data = yaml.safe_load((ROOT / "software/sketchup/engine-map.yaml").read_text(encoding="utf-8"))
        snapshot = data["source_snapshot"]
        self.assertEqual("d9aecb07ecfae9e5ffb969f2314fafe2040c162b", snapshot["head"])
        self.assertEqual("0.28", snapshot["contract_version"])
        self.assertEqual(67, snapshot["public_tool_count"])

        by_semantic = {row["semantic"]: row for row in data["capability_mappings"]}
        registry = by_semantic["component.library_resolve"]
        self.assertEqual("expected", registry["support"])
        for tool in ["asset_list", "place_asset", "definition_info", "get_entity_state"]:
            self.assertIn(tool, registry["expected_public_tools"])

        blockers = {row["code"] for row in data["known_blockers"]}
        self.assertNotIn("native_component_registry_identity_metadata_missing", blockers)
        self.assertNotIn("artifact_seal_missing", blockers)
        self.assertEqual("expected", by_semantic["artifact.seal"]["support"])
        self.assertIn("artifact_seal", by_semantic["artifact.seal"]["expected_public_tools"])

    def test_sketchup_guide_records_native_identity_seal_and_mesh_acceptance(self):
        text = (ROOT / "software/sketchup/OPERATING_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("contract `0.28`", text)
        self.assertIn("`asset_list`", text)
        self.assertIn("`place_asset`", text)
        self.assertNotIn("native_component_registry_identity_metadata_missing", text)
        self.assertIn("SHA-256", text)
        self.assertIn("native_version", text)
        self.assertIn("artifact_seal", text)
        self.assertIn("create_mesh", text)

    def test_solidworks_map_tracks_current_public_provider_without_overclaiming_seal(self):
        data = yaml.safe_load((ROOT / "software/solidworks/engine-map.yaml").read_text(encoding="utf-8"))
        snapshot = data["source_snapshot"]
        self.assertEqual("CDT-SolidWorks", snapshot["repository"])
        self.assertEqual("9537cc313020ffb26eb21cfd9ab6810a2671a5dc", snapshot["head"])
        self.assertEqual("0.1.0", snapshot["provider_version"])
        self.assertEqual("0.1.0", snapshot["contract_version"])
        self.assertEqual(149, snapshot["public_tool_count"])
        self.assertEqual(125, snapshot["public_capability_count"])
        self.assertFalse(snapshot["runtime_proof"])
        self.assertEqual("accepted", snapshot["native_acceptance"])
        self.assertEqual("accepted", snapshot["engineer_closed_loop_acceptance"])
        self.assertEqual("aba46838a9ab898d34388948d1a16d6addded95b", snapshot["engineer_revision"])

        by_semantic = {row["semantic"]: row for row in data["capability_mappings"]}
        expected = {
            "solid.feature.create",
            "solid.boolean",
            "model.query",
            "checkpoint.create",
            "model_3d.measure",
            "topology.inspect",
            "artifact.native_save",
            "artifact.reopen",
            "artifact.exchange_export",
        }
        for semantic in expected:
            self.assertEqual("expected", by_semantic[semantic]["support"], semantic)
            self.assertTrue(by_semantic[semantic]["expected_public_tools"], semantic)

        self.assertIn("part_create_rect_extrude", by_semantic["solid.feature.create"]["expected_public_tools"])
        self.assertIn("body_combine", by_semantic["solid.boolean"]["expected_public_tools"])
        self.assertIn("document_reconcile", by_semantic["checkpoint.create"]["expected_public_tools"])
        self.assertIn("evaluation_measure", by_semantic["model_3d.measure"]["expected_public_tools"])
        self.assertIn("topology_inspect", by_semantic["topology.inspect"]["expected_public_tools"])
        self.assertIn("export_document", by_semantic["artifact.exchange_export"]["expected_public_tools"])

        seal = by_semantic["artifact.seal"]
        self.assertEqual("blocked", seal["support"])
        self.assertEqual([], seal["expected_public_tools"])
        blockers = {row["code"] for row in data["known_blockers"]}
        self.assertNotIn("provider_not_implemented", blockers)
        self.assertIn("artifact_seal_missing", blockers)
        self.assertIn("source_snapshot_not_runtime_proof", blockers)

    def test_solidworks_source_map_remains_fail_closed_without_runtime_discovery(self):
        from execution.stage_runner import capability_facts_from_engine_maps

        data = yaml.safe_load((ROOT / "software/solidworks/engine-map.yaml").read_text(encoding="utf-8"))
        facts = capability_facts_from_engine_maps([data])

        self.assertEqual("unknown", facts["solid.feature.create"]["result"])
        self.assertIn(
            "runtime_fact_required:solidworks:solid.feature.create",
            facts["solid.feature.create"]["reason_codes"],
        )
        self.assertEqual("unknown", facts["model_3d.measure"]["result"])
        self.assertEqual("blocked", facts["artifact.seal"]["result"])
        self.assertIn(
            "source_map_blocked:solidworks:artifact.seal",
            facts["artifact.seal"]["reason_codes"],
        )

    def test_native_benchmarks_define_recovery_and_current_typed_blockers(self):
        building = (ROOT / "domains/building-architecture/benchmark-pack.md").read_text(encoding="utf-8")
        self.assertIn("asset_list", building)
        self.assertIn("place_asset", building)
        self.assertNotIn("native_component_registry_identity_metadata_missing", building)
        self.assertIn("native_mapping_unresolved", building)
        self.assertIn("early", building.lower())
        self.assertIn("middle", building.lower())
        self.assertIn("late", building.lower())
        self.assertIn("uncertain", building.lower())

        site = (ROOT / "domains/site-reconstruction/benchmark-pack.md").read_text(encoding="utf-8")
        for token in ["early", "middle", "late", "uncertain"]:
            self.assertIn(token, site.lower())
        self.assertIn("external hash", site.lower())

        mechanical = (ROOT / "domains/mechanical-reconstruction/benchmark-pack.md").read_text(encoding="utf-8")
        self.assertNotIn("provider_not_implemented", mechanical)
        self.assertIn("artifact_seal_missing", mechanical)
        self.assertIn("document_reconcile", mechanical)
        self.assertIn("evaluation_measure", mechanical)
        self.assertIn("topology_inspect", mechanical)
        self.assertIn("W-CDTE closed-loop acceptance: ACCEPTED", mechanical)
        self.assertIn("9537cc313020ffb26eb21cfd9ab6810a2671a5dc", mechanical)
        for token in ["early", "middle", "late", "uncertain"]:
            self.assertIn(token, mechanical.lower())


if __name__ == "__main__":
    unittest.main()
