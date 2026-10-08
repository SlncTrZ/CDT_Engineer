"""Contract tests for the Building Structural semantic asset catalog.
Wing: code | Topic: structural-asset-catalog | Updated: 2026-09-12 22:47
"""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from execution.catalog_resolver import resolve_catalog_assets

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_PATH=ROOT/'catalogs'/'schemas'/'engineering-asset-catalog.schema.json'
CATALOG_PATH=ROOT/'catalogs'/'building-structural'/'catalog.json'


class StructuralAssetCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator=Draft202012Validator(cls.schema)
        cls.catalog=json.loads(CATALOG_PATH.read_text(encoding='utf-8'))

    def test_structural_catalog_validates(self):
        errors=list(self.validator.iter_errors(self.catalog))
        self.assertEqual([],errors,'\n'.join(e.message for e in errors))

    def test_priority_structural_families_are_semantic_not_capacity_claims(self):
        assets=self.catalog['assets']
        families={asset['family'] for asset in assets}
        for family in ['structural_member','connection_interface','foundation_interface']:
            self.assertIn(family,families)
        for asset in assets:
            self.assertNotIn('ready_for_professional_review',asset['applicability']['release_classes'])
            self.assertIn('not',asset['applicability']['notes'].lower())

    def test_unresolved_native_mappings_have_reason_and_no_fabricated_identity(self):
        for asset in self.catalog['assets']:
            for software,mapping in asset['native_mappings'].items():
                self.assertEqual('unresolved',mapping['state'],f'{asset["asset_id"]}:{software}')
                self.assertTrue(mapping['reason'])
                for key in ['asset_key','sha256','native_version']:
                    self.assertNotIn(key,mapping,f'{asset["asset_id"]}:{software}')



    def test_structural_native_resolution_stays_blocked_without_runtime_identity(self):
        result=resolve_catalog_assets(
            self.catalog,
            software_id='autocad',
            required_asset_ids=['structural.member.prismatic.rectangular.generic.v1'],
            registry_evidence={},
            runtime_capability={'result':'pass'},
        )
        self.assertEqual('blocked',result['state'])
        self.assertIn('native_mapping_unresolved:structural.member.prismatic.rectangular.generic.v1:autocad',result['reason_codes'])




if __name__=='__main__':
    unittest.main()
