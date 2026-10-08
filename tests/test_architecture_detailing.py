"""Deterministic tests for release-aware architectural detail completeness."""
import unittest

from domains.building_architecture.detailing import required_details_for_release, evaluate_detail_inventory


class ArchitectureDetailingTests(unittest.TestCase):
    def test_concept_does_not_require_design_review_junction_details(self):
        required=required_details_for_release(['opening','facade_system','parapet'],release_target='concept')
        self.assertEqual([],required)

    def test_design_review_requires_critical_system_junction_intent(self):
        required=required_details_for_release(
            ['opening','door','facade_system','parapet','railing','stair'],
            release_target='design_review',
        )
        for detail_id in [
            'opening.head-jamb-sill-intent',
            'door.threshold-intent',
            'facade.support-edge-intent',
            'parapet.roof-junction-intent',
            'railing.support-intent',
            'stair.landing-handrail-intent',
        ]:
            self.assertIn(detail_id,required)

    def test_construction_candidate_adds_waterproofing_and_connection_detail_requirements(self):
        required=required_details_for_release(['facade_system','parapet','balcony'],release_target='fabrication_or_construction_candidate')
        self.assertIn('facade.anchor-subframe-detail',required)
        self.assertIn('parapet.waterproofing-termination-detail',required)
        self.assertIn('balcony.edge-waterproofing-detail',required)

    def test_missing_required_detail_blocks(self):
        items=[
            {'item_id':'opening.head-jamb-sill-intent','required':True,'implementation_state':'implemented','verification_state':'verified'},
            {'item_id':'door.threshold-intent','required':True,'implementation_state':'missing','verification_state':'unverified'},
        ]
        result=evaluate_detail_inventory(['opening','door'],release_target='design_review',items=items)
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_detail_missing:door.threshold-intent',result['reason_codes'])

    def test_unrelated_extra_detail_does_not_substitute_for_required_one(self):
        items=[
            {'item_id':'decorative.extra','required':False,'implementation_state':'implemented','verification_state':'verified'},
        ]
        result=evaluate_detail_inventory(['parapet'],release_target='design_review',items=items)
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_detail_missing:parapet.roof-junction-intent',result['reason_codes'])


if __name__=='__main__':
    unittest.main()
