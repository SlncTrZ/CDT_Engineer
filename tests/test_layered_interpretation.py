"""Layered-interpretation tests: a layout-to-3D job must never drop a covered background layer."""
import unittest

from execution.completeness_checker import assess_layer_ledger
from professional_practice.layered_interpretation import order_layer_chunks


def frozen_two_layer_layout():
    return [
        {'item_id':'slab-base','layer_id':'A-NEN','visibility':'visible','evidence_state':'observed','required':True},
        {'item_id':'wall-cover','layer_id':'A-TUONG','visibility':'visible','evidence_state':'observed','required':True},
        {'item_id':'pipe-behind-wall','layer_id':'M-NUOC','visibility':'occluded','evidence_state':'unknown','required':True},
    ]


class LayerCarryTests(unittest.TestCase):
    def test_3d_missing_background_layer_blocks(self):
        final={
            'wall-cover':{'implementation_state':'implemented','verification_state':'verified'},
            'pipe-behind-wall':{'implementation_state':'implemented','verification_state':'verified'},
        }
        result=assess_layer_ledger(frozen_two_layer_layout(),final)
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_dropped:slab-base',result['reason_codes'])

    def test_occluded_required_item_left_unknown_blocks(self):
        final={
            'slab-base':{'implementation_state':'implemented','verification_state':'verified'},
            'wall-cover':{'implementation_state':'implemented','verification_state':'verified'},
            'pipe-behind-wall':{'implementation_state':'implemented','verification_state':'verified'},
        }
        result=assess_layer_ledger(frozen_two_layer_layout(),final)
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_occluded_unresolved:pipe-behind-wall',result['reason_codes'])

    def test_approved_occluded_item_carried_passes(self):
        frozen=[
            {'item_id':'slab-base','layer_id':'A-NEN','visibility':'visible','evidence_state':'observed','required':True},
            {'item_id':'pipe-behind-wall','layer_id':'M-NUOC','visibility':'occluded','evidence_state':'approved_assumption','required':True},
        ]
        final={
            'slab-base':{'implementation_state':'implemented','verification_state':'verified'},
            'pipe-behind-wall':{'implementation_state':'implemented','verification_state':'verified'},
        }
        result=assess_layer_ledger(frozen,final)
        self.assertEqual('pass',result['result'])

    def test_explicit_scope_reduction_does_not_block(self):
        frozen=[
            {'item_id':'slab-base','layer_id':'A-NEN','visibility':'visible','evidence_state':'observed','required':True},
            {'item_id':'decorative-trim','layer_id':'A-TRIM','visibility':'visible','evidence_state':'observed','required':False},
        ]
        final={'slab-base':{'implementation_state':'implemented','verification_state':'verified'}}
        result=assess_layer_ledger(frozen,final)
        self.assertEqual('pass',result['result'])

    def test_occlusion_is_never_recorded_as_absent(self):
        with self.assertRaises(ValueError):
            assess_layer_ledger(
                [{'item_id':'x','layer_id':'L','visibility':'visible','evidence_state':'guessed','required':True}],
                {},
            )


class LayerOrderTests(unittest.TestCase):
    def test_base_commits_before_covering_foreground(self):
        order=order_layer_chunks([
            {'item_id':'wall-cover','hosted_on':['slab-base']},
            {'item_id':'slab-base','hosted_on':[]},
            {'item_id':'paint-finish','hosted_on':['wall-cover']},
        ])
        self.assertLess(order.index('slab-base'),order.index('wall-cover'))
        self.assertLess(order.index('wall-cover'),order.index('paint-finish'))

    def test_host_cycle_fails_closed(self):
        with self.assertRaises(ValueError):
            order_layer_chunks([
                {'item_id':'a','hosted_on':['b']},
                {'item_id':'b','hosted_on':['a']},
            ])

    def test_unknown_host_fails_closed(self):
        with self.assertRaises(ValueError):
            order_layer_chunks([{'item_id':'a','hosted_on':['ghost-layer']}])


if __name__=='__main__':
    unittest.main()
