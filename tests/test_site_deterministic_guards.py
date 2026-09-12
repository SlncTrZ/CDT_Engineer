"""Site deterministic guard acceptance tests."""
import math
import unittest

from domains.site_reconstruction.guards import (
    GuardInputError,
    apply_affine_point,
    compose_affine,
    evaluate_registration,
    inspect_affine,
    validate_nested_graph,
)

I=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

class AffineGuardTests(unittest.TestCase):
    def test_identity_is_valid_right_handed(self):
        r=inspect_affine(I,'m','m')
        self.assertEqual('pass',r['result'])
        self.assertAlmostEqual(1.0,r['determinant_3x3'])
        self.assertFalse(r['reflection'])

    def test_singular_transform_blocks(self):
        m=[0,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
        self.assertEqual('fail',inspect_affine(m,'m','m')['result'])

    def test_global_reflection_blocks_unless_explicitly_allowed(self):
        m=[-1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
        self.assertEqual('fail',inspect_affine(m,'m','m')['result'])
        self.assertEqual('pass',inspect_affine(m,'m','m',allow_reflection=True)['result'])

    def test_duplicate_unit_scale_is_detected(self):
        m=[0.001,0,0,0, 0,0.001,0,0, 0,0,0.001,0, 0,0,0,1]
        r=inspect_affine(m,'mm','m')
        self.assertEqual('pass',r['result'])
        self.assertTrue(r['unit_scale_consistent'])
        r2=inspect_affine(m,'m','m')
        self.assertEqual('fail',r2['result'])
        self.assertFalse(r2['unit_scale_consistent'])

    def test_nested_insert_order_translation_rotation_scale(self):
        t=[1,0,0,10, 0,1,0,20, 0,0,1,0, 0,0,0,1]
        a=math.radians(90); r=[math.cos(a),-math.sin(a),0,0, math.sin(a),math.cos(a),0,0, 0,0,1,0, 0,0,0,1]
        s=[2,0,0,0, 0,3,0,0, 0,0,1,0, 0,0,0,1]
        world=compose_affine(t,r,s)
        p=apply_affine_point(world,[1,2,0])
        self.assertAlmostEqual(4,p[0]); self.assertAlmostEqual(22,p[1])

class RegistrationGuardTests(unittest.TestCase):
    def test_collinear_controls_block(self):
        pts=[{'source':[0,0,0],'target':[0,0,0]},{'source':[1,0,0],'target':[1,0,0]},{'source':[2,0,0],'target':[2,0,0]}]
        r=evaluate_registration(I,pts,[{'source':[0,1,0],'target':[0,1,0]}],{'status':'approved','value':0.01,'unit':'m','source_ref':'P','approved_by':'R'},'m')
        self.assertEqual('fail',r['result'])
        self.assertIn('degenerate_controls',r['reason_codes'])

    def test_unresolved_tolerance_is_unknown_not_pass(self):
        pts=[{'source':[0,0,0],'target':[0,0,0]},{'source':[1,0,0],'target':[1,0,0]},{'source':[0,1,0],'target':[0,1,0]}]
        tol={'status':'unresolved','value':None,'unit':'m','source_ref':None,'approved_by':None}
        r=evaluate_registration(I,pts,[{'source':[1,1,0],'target':[1,1,0]}],tol,'m')
        self.assertEqual('unknown',r['result'])
        self.assertEqual(0.0,r['max_control_residual'])

    def test_holdout_above_approved_tolerance_blocks(self):
        pts=[{'source':[0,0,0],'target':[0,0,0]},{'source':[1,0,0],'target':[1,0,0]},{'source':[0,1,0],'target':[0,1,0]}]
        tol={'status':'approved','value':0.01,'unit':'m','source_ref':'P','approved_by':'R'}
        r=evaluate_registration(I,pts,[{'source':[1,1,0],'target':[1.02,1,0]}],tol,'m')
        self.assertEqual('fail',r['result'])
        self.assertGreater(r['max_holdout_residual'],0.01)

    def test_nonfinite_target_cannot_pass_registration(self):
        pts=[{'source':[0,0,0],'target':[0,0,0]},{'source':[1,0,0],'target':[1,0,0]},{'source':[0,1,0],'target':[0,1,0]}]
        tol={'status':'approved','value':0.01,'unit':'m','source_ref':'P','approved_by':'R'}
        with self.assertRaises(GuardInputError):
            evaluate_registration(I,pts,[{'source':[1,1,0],'target':[math.nan,1,0]}],tol,'m')


class RegistrationSyntheticRegressionTests(unittest.TestCase):
    def test_identity_registration_has_zero_residual_but_unresolved_tolerance_is_unknown(self):
        controls=[
            {'source':[0.0,0.0,0.0],'target':[0.0,0.0,0.0]},
            {'source':[10.0,0.0,0.0],'target':[10.0,0.0,0.0]},
            {'source':[0.0,10.0,0.0],'target':[0.0,10.0,0.0]},
        ]
        holdouts=[{'source':[5.0,5.0,0.0],'target':[5.0,5.0,0.0]}]
        tol={'status':'unresolved','value':None,'unit':'m','source_ref':None,'approved_by':None}
        r=evaluate_registration(I,controls,holdouts,tol,'m')
        self.assertEqual('unknown',r['result'])
        self.assertAlmostEqual(0.0,r['max_control_residual'])
        self.assertAlmostEqual(0.0,r['max_holdout_residual'])

class NestedGraphGuardTests(unittest.TestCase):
    def test_cycle_blocks(self):
        r=validate_nested_graph({'A':['B'],'B':['A']},['A'],100)
        self.assertEqual('fail',r['result']); self.assertIn('cycle_detected',r['reason_codes'])

    def test_budget_truncation_blocks(self):
        r=validate_nested_graph({'A':['B','C'],'B':[],'C':[]},['A'],2)
        self.assertEqual('fail',r['result']); self.assertIn('traversal_budget_exceeded',r['reason_codes'])

    def test_string_children_are_rejected_as_malformed_graph(self):
        with self.assertRaises(GuardInputError):
            validate_nested_graph({'A':'B'},['A'],10)

    def test_string_roots_are_rejected_as_malformed_root_list(self):
        with self.assertRaises(GuardInputError):
            validate_nested_graph({'A':[]},'A',10)

if __name__=='__main__': unittest.main()
