"""Mechanical deterministic guard acceptance tests."""
import unittest

from domains.guard_primitives import GuardInputError
from domains.mechanical_reconstruction.guards import (
    evaluate_dimension,
    evaluate_exactness,
    evaluate_topology,
    validate_feature_dag,
)

class DimensionGuardTests(unittest.TestCase):
    def test_unresolved_tolerance_is_unknown(self):
        r=evaluate_dimension(25.0,25.0,{'status':'unresolved','value':None,'unit':'mm','source_ref':None,'approved_by':None},'mm')
        self.assertEqual('unknown',r['result'])

    def test_measured_dimension_outside_approved_tolerance_fails(self):
        tol={'status':'approved','value':0.1,'unit':'mm','source_ref':'drawing:D1','approved_by':'reviewer'}
        r=evaluate_dimension(25.0,25.2,tol,'mm')
        self.assertEqual('fail',r['result'])
        self.assertIn('dimension_outside_tolerance',r['reason_codes'])

    def test_exact_match_with_approved_tolerance_passes(self):
        tol={'status':'approved','value':0.1,'unit':'mm','source_ref':'drawing:D1','approved_by':'reviewer'}
        self.assertEqual('pass',evaluate_dimension(25.0,25.0,tol,'mm')['result'])

class FeatureDagTests(unittest.TestCase):
    def test_valid_dag_returns_build_order(self):
        features=[{'id':'base','depends_on':[]},{'id':'hole','depends_on':['base']},{'id':'fillet','depends_on':['hole']}]
        r=validate_feature_dag(features)
        self.assertEqual('pass',r['result'])
        self.assertLess(r['build_order'].index('base'),r['build_order'].index('hole'))

    def test_missing_dependency_blocks(self):
        r=validate_feature_dag([{'id':'hole','depends_on':['base']}])
        self.assertEqual('fail',r['result']); self.assertIn('missing_dependency',r['reason_codes'])

    def test_cycle_blocks(self):
        r=validate_feature_dag([{'id':'a','depends_on':['b']},{'id':'b','depends_on':['a']}])
        self.assertEqual('fail',r['result']); self.assertIn('cycle_detected',r['reason_codes'])

    def test_duplicate_feature_id_blocks(self):
        r=validate_feature_dag([{'id':'a','depends_on':[]},{'id':'a','depends_on':[]}])
        self.assertEqual('fail',r['result']); self.assertIn('duplicate_feature_id',r['reason_codes'])

    def test_string_dependency_list_is_rejected_as_malformed_input(self):
        with self.assertRaises(GuardInputError):
            validate_feature_dag([{'id':'a','depends_on':[]},{'id':'b','depends_on':'a'}])

    def test_duplicate_dependencies_are_rejected(self):
        with self.assertRaises(GuardInputError):
            validate_feature_dag([{'id':'a','depends_on':[]},{'id':'b','depends_on':['a','a']}])

class ExactnessGuardTests(unittest.TestCase):
    def test_required_exact_sampled_geometry_blocks(self):
        r=evaluate_exactness(required='exact',representation='sampled',approved_max_deviation=None,measured_max_deviation=None)
        self.assertEqual('fail',r['result']); self.assertIn('sampled_representation_not_exact',r['reason_codes'])

    def test_approved_approximation_passes_with_measured_deviation(self):
        r=evaluate_exactness(required='approximation_allowed',representation='sampled',approved_max_deviation=0.05,measured_max_deviation=0.02)
        self.assertEqual('pass',r['result'])

    def test_unmeasured_approximation_is_unknown(self):
        r=evaluate_exactness(required='approximation_allowed',representation='sampled',approved_max_deviation=0.05,measured_max_deviation=None)
        self.assertEqual('unknown',r['result'])

class TopologyGuardTests(unittest.TestCase):
    def test_expected_single_valid_solid_passes(self):
        r=evaluate_topology(expected_body_count=1,observed_body_count=1,all_bodies_valid=True,unexpected_cavities=0,missing_required_treatments=[])
        self.assertEqual('pass',r['result'])

    def test_body_count_or_invalid_body_blocks(self):
        r=evaluate_topology(expected_body_count=1,observed_body_count=2,all_bodies_valid=False,unexpected_cavities=0,missing_required_treatments=[])
        self.assertEqual('fail',r['result']); self.assertIn('body_count_mismatch',r['reason_codes']); self.assertIn('invalid_solid_topology',r['reason_codes'])

    def test_topology_rejects_truthy_string_instead_of_treating_it_as_valid(self):
        with self.assertRaises(GuardInputError):
            evaluate_topology(expected_body_count=1,observed_body_count=1,all_bodies_valid='false',unexpected_cavities=0,missing_required_treatments=[])

    def test_topology_rejects_boolean_counts(self):
        with self.assertRaises(GuardInputError):
            evaluate_topology(expected_body_count=True,observed_body_count=1,all_bodies_valid=True,unexpected_cavities=0,missing_required_treatments=[])

if __name__=='__main__': unittest.main()
