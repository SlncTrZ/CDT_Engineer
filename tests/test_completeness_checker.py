"""Rule-of-Two tests for the domain-neutral requirement/feature completeness checker."""
import unittest

from execution.completeness_checker import assess_inventory


class CompletenessCheckerTests(unittest.TestCase):
    def test_architecture_required_detail_omission_blocks(self):
        result=assess_inventory([
            {'item_id':'door-main','required':True,'implementation_state':'implemented','verification_state':'verified'},
            {'item_id':'facade-louver','required':True,'implementation_state':'missing','verification_state':'unverified'},
        ])
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_missing:facade-louver',result['reason_codes'])

    def test_structural_required_interface_unverified_blocks(self):
        result=assess_inventory([
            {'item_id':'stair-slab-interface','required':True,'implementation_state':'implemented','verification_state':'unverified'},
            {'item_id':'facade-support-interface','required':False,'implementation_state':'not_applicable','verification_state':'not_applicable'},
        ])
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_unverified:stair-slab-interface',result['reason_codes'])

    def test_required_not_applicable_is_missing_even_if_marked_verified(self):
        result=assess_inventory([
            {'item_id':'front-door','required':True,'implementation_state':'not_applicable','verification_state':'verified'},
        ])
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_missing:front-door',result['reason_codes'])


    def test_optional_missing_item_does_not_block(self):
        result=assess_inventory([
            {'item_id':'optional-render-detail','required':False,'implementation_state':'missing','verification_state':'unverified'},
        ])
        self.assertEqual('pass',result['result'])

    def test_duplicate_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            assess_inventory([
                {'item_id':'x','required':True,'implementation_state':'implemented','verification_state':'verified'},
                {'item_id':'x','required':True,'implementation_state':'implemented','verification_state':'verified'},
            ])

    def test_evidence_coverage_is_reported(self):
        result=assess_inventory([
            {'item_id':'a','required':True,'implementation_state':'implemented','verification_state':'verified'},
            {'item_id':'b','required':True,'implementation_state':'implemented','verification_state':'verified'},
            {'item_id':'c','required':False,'implementation_state':'missing','verification_state':'unverified'},
        ])
        self.assertEqual(2,result['required_count'])
        self.assertEqual(2,result['verified_required_count'])
        self.assertEqual(1.0,result['required_verification_coverage'])


if __name__=='__main__':
    unittest.main()
