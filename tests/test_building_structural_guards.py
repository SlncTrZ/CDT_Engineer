"""Deterministic guard tests for Building Structural v1 intent/coordination."""
import unittest

from domains.building_structural.guards import (
    evaluate_architecture_clashes,
    evaluate_interface_inventory,
    evaluate_release_evidence,
    validate_grid,
    validate_load_path,
)
from domains.guard_primitives import GuardInputError


class BuildingStructuralGuardTests(unittest.TestCase):
    def test_grid_axes_are_unique_finite_and_ordered(self):
        result=validate_grid({'x':[0.0,4.0,8.0],'y':[0.0,3.5,7.0]})
        self.assertEqual('pass',result['result'])
        self.assertEqual(9,result['intersection_count'])
        self.assertEqual('fail',validate_grid({'x':[0.0,0.0],'y':[0.0,3.0]})['result'])
        with self.assertRaises(GuardInputError):
            validate_grid({'x':[False,4.0],'y':[0.0,3.0]})

    def test_load_path_requires_every_loaded_node_to_reach_foundation_or_ground(self):
        graph={
            'roof':['beam-1'],
            'beam-1':['column-1'],
            'column-1':['foundation-1'],
            'foundation-1':['ground'],
            'ground':[],
        }
        result=validate_load_path(graph,loaded_nodes=['roof'],terminal_nodes=['ground'])
        self.assertEqual('pass',result['result'])
        broken=dict(graph)
        broken['column-1']=[]
        result=validate_load_path(broken,loaded_nodes=['roof'],terminal_nodes=['ground'])
        self.assertEqual('fail',result['result'])
        self.assertIn('load_path_does_not_reach_terminal:roof',result['reason_codes'])

    def test_load_path_requires_every_reachable_branch_to_reach_terminal(self):
        graph={'roof':['C1','C2'],'C1':['ground'],'C2':[],'ground':[]}
        result=validate_load_path(graph,loaded_nodes=['roof'],terminal_nodes=['ground'])
        self.assertEqual('fail',result['result'])
        self.assertIn('load_path_branch_terminates_before_terminal:roof:C2',result['reason_codes'])


    def test_load_path_cycle_fails(self):
        graph={'beam':['column'],'column':['beam']}
        result=validate_load_path(graph,loaded_nodes=['beam'],terminal_nodes=['ground'])
        self.assertEqual('fail',result['result'])
        self.assertIn('load_path_cycle',result['reason_codes'])

    def test_architecture_column_opening_clash_is_detected(self):
        columns=[{'id':'C1','bounds':[1.0,1.0,1.4,1.4]}]
        openings=[{'id':'O1','bounds':[1.2,0.8,1.8,1.6]}]
        result=evaluate_architecture_clashes(columns=columns,openings=openings,clearance=0.0)
        self.assertEqual('fail',result['result'])
        self.assertIn('column_opening_clash:C1:O1',result['reason_codes'])
        clear=evaluate_architecture_clashes(columns=columns,openings=[{'id':'O2','bounds':[2,2,3,3]}],clearance=0.1)
        self.assertEqual('pass',clear['result'])

    def test_required_cross_discipline_interface_inventory_blocks_omission(self):
        items=[
            {'item_id':'stair-slab-interface','required':True,'implementation_state':'implemented','verification_state':'verified'},
            {'item_id':'facade-support-interface','required':True,'implementation_state':'missing','verification_state':'unverified'},
        ]
        result=evaluate_interface_inventory(items)
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_missing:facade-support-interface',result['reason_codes'])

    def test_design_review_can_preserve_unknown_loads_but_not_claim_structural_adequacy(self):
        evidence={'structural_system':'specified','materials':'unknown','loads':'unknown','standards':'unknown'}
        result=evaluate_release_evidence(evidence,release_target='design_review')
        self.assertEqual('pass',result['result'])
        self.assertIn('structural_adequacy_unclaimed',result['limitations'])
        stronger=evaluate_release_evidence(evidence,release_target='fabrication_or_construction_candidate')
        self.assertEqual('blocked',stronger['result'])
        self.assertIn('materials_unresolved',stronger['reason_codes'])
        self.assertIn('loads_unresolved',stronger['reason_codes'])
        self.assertIn('standards_unresolved',stronger['reason_codes'])


if __name__=='__main__':
    unittest.main()
