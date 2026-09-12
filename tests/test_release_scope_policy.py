"""Acceptance tests for fail-closed semantic dependency and release-scope policy."""
import unittest

from execution.release_scope import assess_dependencies
from execution.stage_runner import run_profile


class ReleaseScopePolicyTests(unittest.TestCase):
    def test_missing_required_dependency_blocks_requested_release(self):
        requirements=[{'dependency_id':'domain.skill.wall-system','required_from_release':'design_review'}]
        result=assess_dependencies('design_review',requirements,{})
        self.assertEqual('blocked',result['result'])
        self.assertIn('dependency_state_unknown:domain.skill.wall-system',result['reason_codes'])

    def test_proxy_cannot_satisfy_release_above_declared_limit(self):
        requirements=[{
            'dependency_id':'catalog.window-family',
            'required_from_release':'technical_draft',
            'proxy_allowed_through':'concept',
        }]
        states={'catalog.window-family':{'state':'proxy_allowed_for_scope','reason_codes':['asset_missing']}}
        result=assess_dependencies('design_review',requirements,states)
        self.assertEqual('blocked',result['result'])
        self.assertEqual('concept',result['recommended_release_target'])
        self.assertIn('scope_reduction_required:catalog.window-family:concept',result['reason_codes'])

    def test_proxy_is_allowed_only_when_requested_scope_is_within_limit(self):
        requirements=[{
            'dependency_id':'catalog.window-family',
            'required_from_release':'concept',
            'proxy_allowed_through':'concept',
        }]
        states={'catalog.window-family':{'state':'proxy_allowed_for_scope'}}
        result=assess_dependencies('concept',requirements,states)
        self.assertEqual('pass',result['result'])
        self.assertEqual('concept',result['effective_release_target'])
        self.assertTrue(result['limitations'])

    def test_explicit_reduced_scope_never_passes_original_stronger_request(self):
        requirements=[{'dependency_id':'standard.applicability','required_from_release':'design_review'}]
        states={'standard.applicability':{'state':'reduced_scope','maximum_release':'technical_draft'}}
        result=assess_dependencies('ready_for_professional_review',requirements,states)
        self.assertEqual('blocked',result['result'])
        self.assertEqual('technical_draft',result['recommended_release_target'])

    def test_resolved_and_custom_allowed_dependencies_pass(self):
        requirements=[
            {'dependency_id':'domain.skill.feature-plan','required_from_release':'technical_draft'},
            {'dependency_id':'catalog.custom-bracket','required_from_release':'technical_draft'},
        ]
        states={
            'domain.skill.feature-plan':{'state':'resolved'},
            'catalog.custom-bracket':{'state':'custom_allowed','reason_codes':['bounded_custom_feature']},
        }
        result=assess_dependencies('design_review',requirements,states)
        self.assertEqual('pass',result['result'])
        self.assertIn('custom_allowed:catalog.custom-bracket',result['limitations'])


class StageRunnerDependencyGateTests(unittest.TestCase):
    PROFILE={
        'profile_id':'dependency-gate',
        'release_target':'design_review',
        'stages':[{
            'stage_id':'semantic_execution',
            'depends_on':[],
            'required_capabilities':['local.ready'],
            'dependency_requirements':[
                {'dependency_id':'catalog.approved-component','required_from_release':'design_review'}
            ],
            'checkpoint':'semantic_checkpoint',
        }],
    }

    def test_dependency_blocker_overrides_capability_and_stage_pass(self):
        result=run_profile(
            self.PROFILE,
            capabilities={'local.ready':{'result':'pass'}},
            stage_checks={'semantic_execution':{'result':'pass'}},
            dependency_states={},
        )
        stage=result['stages'][0]
        self.assertEqual('blocked',stage['assessment_result'])
        self.assertIn('dependency_state_unknown:catalog.approved-component',stage['assessment_reason_codes'])
        self.assertEqual('blocked',result['result'])

    def test_proxy_reports_recommended_release_without_false_pass(self):
        result=run_profile(
            self.PROFILE,
            capabilities={'local.ready':{'result':'pass'}},
            stage_checks={'semantic_execution':{'result':'pass'}},
            dependency_states={
                'semantic_execution':{
                    'catalog.approved-component':{
                        'state':'proxy_allowed_for_scope',
                        'reason_codes':['catalog_missing'],
                    }
                }
            },
        )
        self.assertEqual('blocked',result['result'])
        self.assertEqual('concept',result['recommended_release_target'])


if __name__=='__main__':
    unittest.main()
