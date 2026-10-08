"""Deterministic guard tests for the Building Architecture v1 vertical."""
import unittest

from domains.building_architecture.guards import (
    EXECUTION_LANES,
    evaluate_feature_inventory,
    evaluate_opening_host,
    evaluate_space,
    evaluate_stair,
    resolve_opening_elevation,
    validate_levels,
    verify_execution_placement,
    verify_opening_placement,
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

    def test_opening_absolute_elevation_binds_wall_level(self):
        levels=[{'id':'L1','elevation':0.0},{'id':'L2','elevation':3600.0}]
        wall={'id':'W1','level_id':'L2','length':6000.0,'height':3600.0}
        opening={'id':'WIN1','host_wall_id':'W1','offset':1000.0,'width':1500.0,'height':1500.0,'sill_height':900.0}
        result=resolve_opening_elevation(levels,wall,opening)
        self.assertEqual('pass',result['result'])
        self.assertEqual(4500.0,result['sill_elevation'])
        self.assertEqual(6000.0,result['head_elevation'])
        self.assertEqual(3600.0,result['wall_base_elevation'])
        self.assertEqual(7200.0,result['wall_top_elevation'])

    def test_opening_head_above_wall_top_fails_absolute_gate(self):
        levels=[{'id':'L2','elevation':3600.0}]
        wall={'id':'W1','level_id':'L2','length':6000.0,'height':3600.0}
        eating_ceiling={'id':'WIN1','host_wall_id':'W1','offset':1000.0,'width':1500.0,'height':1500.0,'sill_height':3000.0}
        result=resolve_opening_elevation(levels,wall,eating_ceiling)
        self.assertEqual('fail',result['result'])
        self.assertIn('head_above_wall_top',result['reason_codes'])

    def test_opening_unresolved_level_is_unknown_not_pass(self):
        levels=[{'id':'L1','elevation':0.0}]
        wall={'id':'W1','level_id':'L2','length':6000.0,'height':3600.0}
        opening={'id':'WIN1','host_wall_id':'W1','offset':1000.0,'width':1500.0,'height':1500.0,'sill_height':900.0}
        result=resolve_opening_elevation(levels,wall,opening)
        self.assertEqual('unknown',result['result'])
        self.assertIn('level_unresolved',result['reason_codes'])
        self.assertIsNone(result['sill_elevation'])

    def test_measured_placement_verifies_against_resolved_elevation(self):
        levels=[{'id':'L2','elevation':3600.0}]
        wall={'id':'W1','level_id':'L2','length':6000.0,'height':3600.0}
        opening={'id':'WIN1','host_wall_id':'W1','offset':1000.0,'width':1500.0,'height':1500.0,'sill_height':900.0}
        resolved=resolve_opening_elevation(levels,wall,opening)
        self.assertEqual('pass',verify_opening_placement(resolved,4500.0,6000.0,1.0)['result'])
        double_added=verify_opening_placement(resolved,8100.0,9600.0,1.0)
        self.assertEqual('fail',double_added['result'])
        self.assertIn('sill_elevation_mismatch',double_added['reason_codes'])
        self.assertIn('head_elevation_mismatch',double_added['reason_codes'])
        unresolved=resolve_opening_elevation([{'id':'L1','elevation':0.0}],wall,opening)
        self.assertEqual('unknown',verify_opening_placement(unresolved,4500.0,6000.0,1.0)['result'])

    def test_3d_intent_through_2d_drafting_lane_fails(self):
        window_3d={'id':'WIN1','intent_3d':True,'coordinates':{'points':[[0.0,0.0],[1.5,0.0]],'level_id':'L1'}}
        result=verify_execution_placement(window_3d,'autocad_2d_drafting')
        self.assertEqual('fail',result['result'])
        self.assertIn('lane_intent_mismatch',result['reason_codes'])
        mesh_3d={'id':'M1','intent_3d':True,'coordinates':{'points':[[0.0,0.0],[1.0,0.0]]}}
        self.assertEqual('fail',verify_execution_placement(mesh_3d,'sketchup_mesh')['result'])

    def test_3d_lane_requires_explicit_z(self):
        flat={'id':'W1','intent_3d':True,'coordinates':{'points':[[0.0,0.0],[6.0,0.0]]}}
        result=verify_execution_placement(flat,'autocad_3d_solid')
        self.assertEqual('fail',result['result'])
        self.assertIn('coordinate_dimension_mismatch',result['reason_codes'])
        no_coords={'id':'W1','intent_3d':True,'coordinates':{}}
        result=verify_execution_placement(no_coords,'autocad_3d_solid')
        self.assertEqual('fail',result['result'])
        self.assertIn('missing_coordinates',result['reason_codes'])
        solid={'id':'W1','intent_3d':True,'coordinates':{'points':[[0.0,0.0,0.0],[6.0,0.0,0.0],[6.0,0.0,3.6]]}}
        self.assertEqual('pass',verify_execution_placement(solid,'autocad_3d_solid')['result'])

    def test_2d_lane_requires_elevation_reference(self):
        plan={'id':'P1','intent_3d':False,'coordinates':{'origin':[0.0,0.0],'level_id':'L1'}}
        self.assertEqual('pass',verify_execution_placement(plan,'autocad_2d_drafting')['result'])
        floating=dict(plan)
        floating['coordinates']={'origin':[0.0,0.0]}
        result=verify_execution_placement(floating,'autocad_2d_drafting')
        self.assertEqual('fail',result['result'])
        self.assertIn('missing_elevation_reference',result['reason_codes'])

    def test_undeclared_intent_or_lane_is_unknown_or_rejected(self):
        no_intent={'id':'X1','coordinates':{'origin':[0.0,0.0,0.0]}}
        result=verify_execution_placement(no_intent,'sketchup_mesh')
        self.assertEqual('unknown',result['result'])
        self.assertIn('intent_undeclared',result['reason_codes'])
        with self.assertRaises(GuardInputError):
            verify_execution_placement(no_intent,'autocad_legacy_plot')
        self.assertEqual(3,len(EXECUTION_LANES))

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
