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

    def test_solidworks_map_tracks_frozen_parallel_contract_but_remains_runtime_gated(self):
        data = yaml.safe_load((ROOT / "software/solidworks/engine-map.yaml").read_text(encoding="utf-8"))
        snapshot = data["source_snapshot"]
        self.assertEqual("CDT-SolidWorks", snapshot["repository"])
        self.assertEqual("51e5ecfc6376b4146266811b7cd3f36020a89967", snapshot["head"])
        self.assertEqual("inter-agent-contract-v1", snapshot["contract_version"])
        self.assertFalse(snapshot["runtime_proof"])
        self.assertEqual("parallel_contract_runtime_gated", snapshot["provider_state"])
        by_semantic = {row["semantic"]: row for row in data["capability_mappings"]}
        self.assertEqual("expected", by_semantic["solid.feature.create"]["support"])
        self.assertIn("part_cut_extrude", by_semantic["solid.feature.create"]["expected_public_tools"])
        self.assertIn("body_combine", by_semantic["solid.boolean"]["expected_public_tools"])
        self.assertIn("evaluation_measure", by_semantic["model_3d.measure"]["expected_public_tools"])
        self.assertIn("reconstruction_step_to_editable", by_semantic["reconstruction.step_to_editable"]["expected_public_tools"])
        self.assertEqual("unproven", by_semantic["artifact.seal"]["support"])
        for row in data["capability_mappings"]:
            self.assertTrue(row["runtime_gate"]["required"], row["semantic"])
        blockers = {row["code"] for row in data["known_blockers"]}
        self.assertNotIn("provider_not_implemented", blockers)
        self.assertIn("parallel_integration_not_accepted", blockers)
        self.assertIn("exact_transaction_mode_unproven", blockers)

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
        self.assertIn("reconstruction_step_to_editable", mechanical)
        self.assertIn("runtime discovery", mechanical.lower())
        for token in ["early", "middle", "late", "uncertain"]:
            self.assertIn(token, mechanical.lower())


if __name__ == "__main__":
    unittest.main()
