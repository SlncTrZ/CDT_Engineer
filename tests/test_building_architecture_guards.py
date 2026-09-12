"""Deterministic guard tests for the Building Architecture v1 vertical."""
import unittest

from domains.building_architecture.guards import (
    evaluate_feature_inventory,
    evaluate_opening_host,
    evaluate_space,
    evaluate_stair,
    validate_levels,
)
from domains.guard_primitives import GuardInputError


class BuildingArchitectureGuardTests(unittest.TestCase):
    def test_levels_are_unique_finite_and_strictly_ordered(self):
        result=validate_levels([
            {'id':'L1','elevation':0.0},
            {'id':'L2','elevation':3.6},
            {'id':'L3','elevation':7.2},
        ])
        self.assertEqual('pass',result['result'])
        self.assertEqual(7.2,result['vertical_span'])
        with self.assertRaises(GuardInputError):
            validate_levels([{'id':'L1','elevation':False}])
        self.assertEqual('fail',validate_levels([
            {'id':'L1','elevation':0.0},
            {'id':'L2','elevation':0.0},
        ])['result'])

    def test_space_area_and_clear_dimensions_use_explicit_requirements_only(self):
        boundary=[[0,0],[4,0],[4,3],[0,3]]
        no_requirement=evaluate_space(boundary,{})
        self.assertEqual('pass',no_requirement['result'])
        self.assertAlmostEqual(12.0,no_requirement['area'])
        result=evaluate_space(boundary,{'minimum_area':12.5,'minimum_clear_dimension':2.5})
        self.assertEqual('fail',result['result'])
        self.assertIn('area_below_requirement',result['reason_codes'])
        self.assertNotIn('clear_dimension_below_requirement',result['reason_codes'])

    def test_self_intersecting_space_fails(self):
        result=evaluate_space([[0,0],[4,4],[0,4],[4,0]],{})
        self.assertEqual('fail',result['result'])
        self.assertIn('self_intersecting_boundary',result['reason_codes'])

    def test_opening_must_fit_host_wall(self):
        wall={'id':'W1','length':5.0,'height':3.2}
        opening={'id':'O1','host_wall_id':'W1','offset':1.0,'width':1.2,'height':2.2,'sill_height':0.0}
        self.assertEqual('pass',evaluate_opening_host(wall,opening)['result'])
        bad=dict(opening,offset=4.2,width=1.0)
        result=evaluate_opening_host(wall,bad)
        self.assertEqual('fail',result['result'])
        self.assertIn('opening_exceeds_wall_length',result['reason_codes'])

    def test_stair_uses_level_delta_and_explicit_requirements_not_universal_code_values(self):
        stair={
            'from_elevation':0.0,
            'to_elevation':3.6,
            'riser_count':20,
            'riser_height':0.18,
            'going':0.27,
            'width':1.0,
        }
        result=evaluate_stair(stair,{})
        self.assertEqual('pass',result['result'])
        result=evaluate_stair(stair,{'maximum_riser_height':0.17,'minimum_going':0.25,'minimum_width':0.9})
        self.assertEqual('fail',result['result'])
        self.assertIn('riser_height_above_requirement',result['reason_codes'])

    def test_stair_rejects_inconsistent_level_rise(self):
        stair={
            'from_elevation':0.0,
            'to_elevation':3.6,
            'riser_count':19,
            'riser_height':0.18,
            'going':0.27,
            'width':1.0,
        }
        result=evaluate_stair(stair,{})
        self.assertEqual('fail',result['result'])
        self.assertIn('stair_total_rise_mismatch',result['reason_codes'])

    def test_required_feature_inventory_blocks_omissions_and_unverified_proxy(self):
        items=[
            {'item_id':'door-main','required':True,'resolution_state':'resolved','implementation_state':'implemented','verification_state':'verified'},
            {'item_id':'louver-front','required':True,'resolution_state':'proxy_allowed_for_scope','implementation_state':'proxy','verification_state':'verified'},
        ]
        design_review=evaluate_feature_inventory(items,release_target='design_review')
        self.assertEqual('blocked',design_review['result'])
        self.assertIn('proxy_not_valid_for_release:louver-front',design_review['reason_codes'])
        concept=evaluate_feature_inventory(items,release_target='concept')
        self.assertEqual('pass',concept['result'])
        missing=[{'item_id':'window-1','required':True,'resolution_state':'resolved','implementation_state':'missing','verification_state':'unverified'}]
        self.assertEqual('blocked',evaluate_feature_inventory(missing,release_target='concept')['result'])
    def test_required_feature_not_applicable_is_missing_consistently(self):
        item={'item_id':'front-door','required':True,'resolution_state':'resolved','implementation_state':'not_applicable','verification_state':'verified'}
        result=evaluate_feature_inventory([item],release_target='design_review')
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_feature_missing:front-door',result['reason_codes'])




if __name__=='__main__':
    unittest.main()
