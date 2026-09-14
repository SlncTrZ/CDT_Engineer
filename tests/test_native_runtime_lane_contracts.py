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

    def test_solidworks_map_fails_closed_on_provider_skeleton(self):
        data = yaml.safe_load((ROOT / "software/solidworks/engine-map.yaml").read_text(encoding="utf-8"))
        snapshot = data["source_snapshot"]
        self.assertEqual("CDT-SolidWorks", snapshot["repository"])
        self.assertEqual("3bd2bfb2e6527cf2440fa8d2e23610ed4d77a6ab", snapshot["head"])
        self.assertEqual(0, snapshot["public_tool_count"])
        for row in data["capability_mappings"]:
            self.assertEqual("blocked", row["support"], row["semantic"])
            self.assertEqual([], row["expected_public_tools"], row["semantic"])
        blockers = {row["code"] for row in data["known_blockers"]}
        self.assertIn("provider_not_implemented", blockers)

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
        self.assertIn("provider_not_implemented", mechanical)
        for token in ["early", "middle", "late", "uncertain"]:
            self.assertIn(token, mechanical.lower())


if __name__ == "__main__":
    unittest.main()
