"""Evidence-gated vertical-readiness preparation tests.
Wing: code | Topic: vertical-readiness | Updated: 2026-09-12 22:35
"""
import unittest

from professional_practice.vertical_readiness import assess_vertical_readiness


class VerticalReadinessTests(unittest.TestCase):
    def complete_evidence(self):
        return {
            'source_evidence': {'state':'verified','evidence_refs':['source:fixture-01']},
            'skill_evidence': {'state':'verified','evidence_refs':['skill:pilot-01']},
            'rule_evidence': {'state':'verified','evidence_refs':['rule:test-01']},
            'benchmark_evidence': {
                'state':'verified',
                'evidence_refs':['benchmark:run-01'],
                'positive_cases':2,
                'negative_cases':3,
                'measurable_acceptance':True,
            },
            'reviewer_evidence': {
                'state':'verified',
                'evidence_refs':['review:independent-01'],
                'independent':True,
            },
        }

    def test_complete_evidence_only_reaches_pilot_definition_readiness(self):
        result=assess_vertical_readiness(
            'civil-infrastructure',
            self.complete_evidence(),
            foundation_dependencies=[{'dependency_id':'building-native-pilot','state':'resolved'}],
        )
        self.assertEqual('ready_for_pilot_definition',result['readiness_state'])
        self.assertNotIn('production_ready',str(result))

    def test_missing_negative_benchmark_case_blocks(self):
        evidence=self.complete_evidence()
        evidence['benchmark_evidence']['negative_cases']=0
        result=assess_vertical_readiness('manufacturing',evidence,foundation_dependencies=[])
        self.assertEqual('blocked',result['readiness_state'])
        self.assertIn('vertical_benchmark_negative_cases_missing',result['reason_codes'])

    def test_self_review_is_not_independent_reviewer_evidence(self):
        evidence=self.complete_evidence()
        evidence['reviewer_evidence']['independent']=False
        result=assess_vertical_readiness('electrical',evidence,foundation_dependencies=[])
        self.assertEqual('blocked',result['readiness_state'])
        self.assertIn('vertical_independent_reviewer_missing',result['reason_codes'])

    def test_unresolved_active_pilot_foundation_blocks_expansion(self):
        result=assess_vertical_readiness(
            'interior-landscape-visualization',
            self.complete_evidence(),
            foundation_dependencies=[{'dependency_id':'building-native-pilot','state':'blocked'}],
        )
        self.assertEqual('blocked',result['readiness_state'])
        self.assertIn('vertical_foundation_blocked:building-native-pilot',result['reason_codes'])

    def test_unknown_required_evidence_blocks(self):
        evidence=self.complete_evidence()
        evidence['rule_evidence']={'state':'unknown','evidence_refs':[]}
        result=assess_vertical_readiness('electronics-embedded',evidence,foundation_dependencies=[])
        self.assertEqual('blocked',result['readiness_state'])
        self.assertIn('vertical_evidence_unknown:rule_evidence',result['reason_codes'])

    def test_production_ready_request_is_explicitly_out_of_scope(self):
        result=assess_vertical_readiness(
            'manufacturing',
            self.complete_evidence(),
            foundation_dependencies=[],
            requested_state='production_ready',
        )
        self.assertEqual('blocked',result['readiness_state'])
        self.assertIn('vertical_production_readiness_not_authorized',result['reason_codes'])


if __name__=='__main__':
    unittest.main()
