"""Contract tests for domain-neutral Engineering Asset Catalog metadata."""
import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_PATH=ROOT/'catalogs'/'schemas'/'engineering-asset-catalog.schema.json'
CATALOG_PATH=ROOT/'catalogs'/'building-components'/'catalog.json'


class EngineeringAssetCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.catalog=json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
        cls.errors=list(Draft202012Validator(cls.schema).iter_errors(cls.catalog))

    def test_building_catalog_validates(self):
        self.assertEqual([],self.errors,'\n'.join(e.message for e in self.errors))

    def test_asset_ids_are_unique_and_priority_families_exist(self):
        assets=self.catalog['assets']
        ids=[a['asset_id'] for a in assets]
        self.assertEqual(len(ids),len(set(ids)))
        families={a['family'] for a in assets}
        for family in ['door','window','louver','breeze_block_panel','railing','stair']:
            self.assertIn(family,families)

    def test_unresolved_native_mapping_does_not_fake_binary_identity(self):
        for asset in self.catalog['assets']:
            for software,mapping in asset['native_mappings'].items():
                if mapping['state']=='unresolved':
                    self.assertNotIn('asset_key',mapping,f'{asset["asset_id"]}:{software}')
                    self.assertNotIn('sha256',mapping,f'{asset["asset_id"]}:{software}')

    def test_schema_v02_enforces_state_specific_native_identity(self):
        self.assertEqual('0.2.0',self.schema['properties']['schema_version']['const'])
        validator=Draft202012Validator(self.schema)
        unresolved=copy.deepcopy(self.catalog)
        mapping=unresolved['assets'][0]['native_mappings']['sketchup']
        mapping['asset_key']='stale-key'
        mapping['sha256']='a'*64
        mapping['native_version']='stale-v1'
        self.assertTrue(list(validator.iter_errors(unresolved)))

        blocked=copy.deepcopy(self.catalog)
        blocked_mapping=blocked['assets'][0]['native_mappings']['sketchup']
        blocked_mapping.clear()
        blocked_mapping['state']='blocked'
        self.assertTrue(list(validator.iter_errors(blocked)))

        resolved=copy.deepcopy(self.catalog)
        resolved_mapping=resolved['assets'][0]['native_mappings']['sketchup']
        resolved_mapping.clear()
        resolved_mapping.update({'state':'resolved','asset_key':'door-v1','sha256':'b'*64,'native_version':'1.0.0'})
        self.assertEqual([],list(validator.iter_errors(resolved)))

    def test_contract_separates_semantic_catalog_from_native_registry(self):
        text=(ROOT/'catalogs'/'ENGINEERING_ASSET_CATALOG_CONTRACT.md').read_text(encoding='utf-8')
        self.assertIn('semantic identity',text.lower())
        self.assertIn('native registry',text.lower())
        self.assertIn('must not',text.lower())


if __name__=='__main__':
    unittest.main()
