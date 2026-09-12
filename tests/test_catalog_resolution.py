"""Deterministic native catalog-resolution tests.
Wing: code | Topic: catalog-resolution | Updated: 2026-09-12 20:20
"""
import copy
import json
import unittest
from pathlib import Path

from execution.catalog_resolver import resolve_catalog_assets

ROOT=Path(__file__).resolve().parents[1]


class CatalogResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.building_catalog=json.loads((ROOT/'catalogs'/'building-components'/'catalog.json').read_text(encoding='utf-8'))

    def test_current_building_catalog_blocks_unresolved_sketchup_native_mapping(self):
        result=resolve_catalog_assets(
            self.building_catalog,
            software_id='sketchup',
            required_asset_ids=['door.generic.single.v1'],
            registry_evidence={},
            runtime_capability={'result':'pass'},
        )
        self.assertEqual('blocked',result['state'])
        self.assertIn('native_mapping_unresolved:door.generic.single.v1:sketchup',result['reason_codes'])

    def test_resolved_mapping_requires_matching_registry_hash_and_version(self):
        catalog=copy.deepcopy(self.building_catalog)
        asset=next(a for a in catalog['assets'] if a['asset_id']=='door.generic.single.v1')
        asset['native_mappings']['sketchup']={
            'state':'resolved',
            'asset_key':'doors/generic-single-v1',
            'sha256':'a'*64,
            'native_version':'1.2.3',
        }
        result=resolve_catalog_assets(
            catalog,
            software_id='sketchup',
            required_asset_ids=['door.generic.single.v1'],
            registry_evidence={
                'doors/generic-single-v1':{
                    'available':True,
                    'sha256':'a'*64,
                    'native_version':'1.2.3',
                }
            },
            runtime_capability={'result':'pass'},
        )
        self.assertEqual('resolved',result['state'])
        self.assertEqual(['door.generic.single.v1'],result['resolved_asset_ids'])

    def test_registry_hash_mismatch_blocks(self):
        catalog=copy.deepcopy(self.building_catalog)
        asset=next(a for a in catalog['assets'] if a['asset_id']=='window.generic.fixed.v1')
        asset['native_mappings']['sketchup']={
            'state':'resolved',
            'asset_key':'windows/fixed-v1',
            'sha256':'b'*64,
            'native_version':'2.0.0',
        }
        result=resolve_catalog_assets(
            catalog,
            software_id='sketchup',
            required_asset_ids=['window.generic.fixed.v1'],
            registry_evidence={
                'windows/fixed-v1':{
                    'available':True,
                    'sha256':'c'*64,
                    'native_version':'2.0.0',
                }
            },
            runtime_capability={'result':'pass'},
        )
        self.assertEqual('blocked',result['state'])
        self.assertIn('native_registry_hash_mismatch:window.generic.fixed.v1',result['reason_codes'])

    def test_runtime_library_capability_must_be_released(self):
        catalog=copy.deepcopy(self.building_catalog)
        asset=next(a for a in catalog['assets'] if a['asset_id']=='railing.generic.linear.v1')
        asset['native_mappings']['sketchup']={
            'state':'resolved',
            'asset_key':'railings/linear-v1',
            'sha256':'d'*64,
            'native_version':'1.0.0',
        }
        result=resolve_catalog_assets(
            catalog,
            software_id='sketchup',
            required_asset_ids=['railing.generic.linear.v1'],
            registry_evidence={
                'railings/linear-v1':{
                    'available':True,
                    'sha256':'d'*64,
                    'native_version':'1.0.0',
                }
            },
            runtime_capability={'result':'unknown','reason_codes':['runtime_fact_required:sketchup:component.library_resolve']},
        )
        self.assertEqual('blocked',result['state'])
        self.assertIn('native_library_capability_not_released:sketchup:unknown',result['reason_codes'])

    def test_missing_required_asset_blocks(self):
        result=resolve_catalog_assets(
            self.building_catalog,
            software_id='sketchup',
            required_asset_ids=['missing.asset'],
            registry_evidence={},
            runtime_capability={'result':'pass'},
        )
        self.assertEqual('blocked',result['state'])
        self.assertIn('catalog_asset_missing:missing.asset',result['reason_codes'])

    def test_duplicate_catalog_asset_identity_is_rejected(self):
        catalog=copy.deepcopy(self.building_catalog)
        catalog['assets'].append(copy.deepcopy(catalog['assets'][0]))
        with self.assertRaises(ValueError):
            resolve_catalog_assets(
                catalog,
                software_id='sketchup',
                required_asset_ids=['door.generic.single.v1'],
                registry_evidence={},
                runtime_capability={'result':'pass'},
            )


if __name__=='__main__':
    unittest.main()
