"""Agent 4 cross-lane integration hard gates."""
import json
import unittest
from pathlib import Path

from execution.catalog_resolver import resolve_catalog_assets
from professional_practice.human_deliverables import assess_human_deliverables

ROOT=Path(__file__).resolve().parents[1]


class ParallelIntegrationContractTests(unittest.TestCase):
    def test_structural_native_mapping_stays_blocked_without_runtime_identity(self):
        catalog=json.loads((ROOT/'catalogs/building-structural/catalog.json').read_text(encoding='utf-8'))
        asset_id='structural.member.prismatic.rectangular.generic.v1'
        result=resolve_catalog_assets(
            catalog,
            software_id='sketchup',
            required_asset_ids=[asset_id],
            registry_evidence={},
            runtime_capability={'result':'pass'},
        )
        self.assertEqual('blocked',result['state'])
        self.assertTrue(any(code.startswith('native_mapping_unresolved:') for code in result['reason_codes']))

    def test_sketchup_map_claims_strong_runtime_route_without_fake_catalog_mapping(self):
        text=(ROOT/'software/sketchup/engine-map.yaml').read_text(encoding='utf-8')
        self.assertIn('semantic: component.library_resolve',text)
        self.assertIn('support: expected',text)
        self.assertNotIn('native_component_registry_identity_metadata_missing',text)
        self.assertIn('asset_list',text)
        self.assertIn('place_asset',text)

    def test_design_review_human_package_fails_when_categories_are_omitted(self):
        result=assess_human_deliverables(
            'design_review', [], {}, package_revision='P1', source_revision='S1'
        )
        self.assertEqual('blocked',result['result'])
        self.assertGreaterEqual(len(result['reason_codes']),9)

    def test_public_docs_promote_deliverable_invariant_but_not_m13_completion(self):
        architecture=(ROOT/'docs/ARCHITECTURE.md').read_text(encoding='utf-8')
        checker=(ROOT/'docs/QA_CHECKER_MODEL.md').read_text(encoding='utf-8')
        skill=(ROOT/'docs/ENGINEERING_SKILL_CONTRACT.md').read_text(encoding='utf-8')
        for text in (architecture,checker,skill):
            self.assertIn('professional_practice.human_deliverables',text)
        self.assertNotIn('M13 Professional Engineering Practice Standard is complete',architecture)


if __name__=='__main__':
    unittest.main()
