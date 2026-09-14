"""Interior fit-out/casework contract and deterministic regression tests."""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from domains.building_architecture.guards import (
    evaluate_casework_box,
    evaluate_casework_compartments,
    evaluate_corner_casework,
    evaluate_rectangular_fit,
)

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'domains'/'building-architecture'/'skills'/'interior-casework-layout'
CATALOG=ROOT/'catalogs'/'building-components'/'catalog.json'
CATALOG_SCHEMA=ROOT/'catalogs'/'schemas'/'engineering-asset-catalog.schema.json'


class BuildingInteriorFitoutTests(unittest.TestCase):
    def test_casework_box_derives_clear_envelope_without_hidden_defaults(self):
        result=evaluate_casework_box(
            {
                'id':'base-01',
                'width':900,
                'height':720,
                'depth':600,
                'panels':{'left':18,'right':18,'top':18,'bottom':18,'back':9},
            },
            {'minimum_clear_width':850,'minimum_clear_height':680,'minimum_clear_depth':580},
        )
        self.assertEqual('pass',result['result'])
        self.assertEqual(864,result['clear_width'])
        self.assertEqual(684,result['clear_height'])
        self.assertEqual(591,result['clear_depth'])

        bad=evaluate_casework_box(
            {
                'id':'base-02',
                'width':500,
                'height':700,
                'depth':560,
                'panels':{'left':18,'right':18,'top':18,'bottom':18,'back':9},
            },
            {'minimum_clear_width':480},
        )
        self.assertEqual('fail',bad['result'])
        self.assertIn('clear_width_below_requirement',bad['reason_codes'])

    def test_casework_compartments_reconcile_partitioned_clear_span(self):
        result=evaluate_casework_compartments(
            clear_span=864,
            compartment_widths=[423,423],
            partition_thickness=18,
        )
        self.assertEqual('pass',result['result'])
        self.assertEqual(864,result['modeled_span'])
        bad=evaluate_casework_compartments(
            clear_span=864,
            compartment_widths=[420,420],
            partition_thickness=18,
        )
        self.assertEqual('fail',bad['result'])
        self.assertIn('compartment_span_mismatch',bad['reason_codes'])

    def test_corner_casework_requires_physically_valid_l_footprint(self):
        result=evaluate_corner_casework(
            {'id':'corner-01','leg_a':1000,'leg_b':900,'depth_a':600,'depth_b':550,'height':720}
        )
        self.assertEqual('pass',result['result'])
        self.assertEqual(1000*600+900*550-600*550,result['footprint_area'])
        bad=evaluate_corner_casework(
            {'id':'corner-02','leg_a':500,'leg_b':900,'depth_a':600,'depth_b':550,'height':720}
        )
        self.assertEqual('fail',bad['result'])
        self.assertIn('corner_leg_a_not_beyond_return_depth',bad['reason_codes'])

    def test_drawer_and_appliance_fit_use_explicit_clearances(self):
        opening={'width':600,'height':700,'depth':580}
        clearances={'left':5,'right':5,'top':5,'bottom':5,'front':0,'back':10}
        drawer=evaluate_rectangular_fit(opening,{'width':580,'height':680,'depth':560},clearances)
        self.assertEqual('pass',drawer['result'])
        appliance=evaluate_rectangular_fit(opening,{'width':595,'height':680,'depth':560},clearances)
        self.assertEqual('fail',appliance['result'])
        self.assertIn('item_exceeds_clear_width',appliance['reason_codes'])

    def test_skill_package_and_inputs_schema_exist(self):
        for name in ['SKILL.md','inputs.schema.json','workflow.yaml']:
            self.assertTrue((SKILL/name).is_file(),name)
        schema=json.loads((SKILL/'inputs.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        evidence=lambda value: {'status':'specified','value':value,'source_ref':'drawing-A3','approved_by':None}
        fixture={
            'schema_version':'0.2.0',
            'system_id':'kitchen-01',
            'units':'mm',
            'release_target':'design_review',
            'source_refs':['drawing-A3'],
            'modules':[{
                'id':'base-01','kind':'base_cabinet',
                'geometry':{'type':'box','width':evidence(900),'height':evidence(720),'depth':evidence(600)},
                'panels':{key:evidence(value) for key,value in {'left':18,'right':18,'top':18,'bottom':18,'back':9}.items()},
                'component_resolution':'custom_allowed','component_id':None,
            }],
            'equipment':[],
        }
        self.assertEqual([],list(Draft202012Validator(schema).iter_errors(fixture)))

    def test_catalog_contains_fitout_semantic_families_without_fake_native_identity(self):
        schema=json.loads(CATALOG_SCHEMA.read_text(encoding='utf-8'))
        catalog=json.loads(CATALOG.read_text(encoding='utf-8'))
        self.assertEqual([],list(Draft202012Validator(schema).iter_errors(catalog)))
        assets=catalog['assets']
        families={asset['family'] for asset in assets}
        for family in ['casework_panel_system','drawer_system','appliance_envelope','casework_anchor_system']:
            self.assertIn(family,families)
        for asset in assets:
            if asset['family'] not in {'casework_panel_system','drawer_system','appliance_envelope','casework_anchor_system'}:
                continue
            mapping=asset['native_mappings'].get('sketchup')
            self.assertIsNotNone(mapping)
            self.assertEqual('unresolved',mapping['state'])
            self.assertNotIn('sha256',mapping)
            self.assertNotIn('native_version',mapping)

    def test_workflow_declares_semantic_chunks_identity_readback_and_uncertain_retry_policy(self):
        text=(SKILL/'workflow.yaml').read_text(encoding='utf-8')
        for token in [
            'feature_based_chunk_streaming',
            'casework_module',
            'drawer_group',
            'equipment_instance',
            'reconcile_state',
            'restart_from_checkpoint',
            'never_blind_retry',
            'persistent_id',
            'definition_guid',
        ]:
            self.assertIn(token,text)

    def test_offline_fixture_cases_match_expected_oracles(self):
        data=json.loads((SKILL/'benchmark'/'fixtures.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(data['cases']),7)
        for case in data['cases']:
            kind=case['kind']
            inputs=case['input']
            if kind=='casework_box':
                result=evaluate_casework_box(inputs['module'],inputs['requirements'])
            elif kind=='compartments':
                result=evaluate_casework_compartments(**inputs)
            elif kind=='corner_casework':
                result=evaluate_corner_casework(inputs['module'])
            elif kind=='rectangular_fit':
                result=evaluate_rectangular_fit(inputs['opening'],inputs['item'],inputs['clearances'])
            else:
                self.fail(f'unknown fixture kind: {kind}')
            expected=case['expected']
            self.assertEqual(expected['result'],result['result'],case['case_id'])
            if 'reason_code' in expected:
                self.assertIn(expected['reason_code'],result['reason_codes'],case['case_id'])
            for key in ('clear_width','clear_height','clear_depth','modeled_span','footprint_area'):
                if key in expected:
                    self.assertEqual(expected[key],result[key],case['case_id'])

    def test_public_benchmark_mentions_casework_positive_and_negative_cases(self):
        text=(ROOT/'domains'/'building-architecture'/'benchmark-pack.md').read_text(encoding='utf-8').lower()
        for token in ['casework box','corner casework','drawer fit','appliance fit','duplicate instance']:
            self.assertIn(token,text)


if __name__=='__main__':
    unittest.main()
