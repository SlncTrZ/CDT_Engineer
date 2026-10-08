"""Professional human-deliverable acceptance tests.
Wing: code | Topic: human-deliverables | Updated: 2026-09-12 22:35
"""
import unittest

from professional_practice.human_deliverables import (
    DELIVERABLE_CATEGORIES,
    assess_human_deliverables,
)


class HumanDeliverableTests(unittest.TestCase):
    def requirement(self, category, *, gate='hard', independent=True, floor=None):
        return {
            'requirement_id': f'pkg.{category}',
            'category': category,
            'required_from_release': floor or ('technical_draft' if category in {
                'plans_views','datums_references','revision_issue_identity','scale_readability'
            } else 'design_review'),
            'gate': gate,
            'reviewer_role': 'documentation_checker',
            'requires_independent_review': independent,
        }

    def passing_evidence(self, *, package_revision='D2', source_revision='M2'):
        return {
            'applicability': 'applicable',
            'implementation_state': 'implemented',
            'verification_state': 'verified',
            'acceptance_state': 'pass',
            'reviewer': 'checker-01',
            'reviewer_role': 'documentation_checker',
            'independent': True,
            'artifact_revision': package_revision,
            'source_revision': source_revision,
            'evidence_refs': ['finding:verified'],
        }

    def design_review_requirements(self):
        return [self.requirement(category) for category in DELIVERABLE_CATEGORIES]

    def design_review_evidence(self):
        return {
            requirement['requirement_id']: self.passing_evidence()
            for requirement in self.design_review_requirements()
        }

    def test_design_review_requires_every_baseline_category_to_be_accounted(self):
        requirements=self.design_review_requirements()
        requirements=[r for r in requirements if r['category']!='schedules_bom']
        evidence={r['requirement_id']:self.passing_evidence() for r in requirements}
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('deliverable_category_unaccounted:schedules_bom',result['reason_codes'])

    def test_explicit_not_applicable_is_allowed_only_with_reason_and_approval(self):
        requirements=self.design_review_requirements()
        evidence=self.design_review_evidence()
        evidence['pkg.schedules_bom']={
            'applicability':'not_applicable',
            'implementation_state':'not_applicable',
            'verification_state':'not_applicable',
            'acceptance_state':'not_applicable',
            'na_reason':'No scheduled components exist in declared architectural review scope.',
            'na_approved_by':'lead-architect',
            'reviewer':'checker-01',
            'reviewer_role':'documentation_checker',
            'independent':True,
            'artifact_revision':'D2',
            'source_revision':'M2',
            'evidence_refs':['decision:na-01'],
        }
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('pass',result['result'])

        evidence['pkg.schedules_bom'].pop('na_approved_by')
        blocked=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',blocked['result'])
        self.assertIn('deliverable_na_unapproved:pkg.schedules_bom',blocked['reason_codes'])

    def test_not_applicable_disposition_still_requires_independent_review_when_declared(self):
        requirements=self.design_review_requirements()
        evidence=self.design_review_evidence()
        evidence['pkg.schedules_bom']={
            'applicability':'not_applicable',
            'implementation_state':'not_applicable',
            'verification_state':'not_applicable',
            'acceptance_state':'not_applicable',
            'na_reason':'No scheduled components exist in declared architectural review scope.',
            'na_approved_by':'lead-architect',
            'reviewer':'producer-01',
            'reviewer_role':'documentation_checker',
            'independent':False,
            'artifact_revision':'D2',
            'source_revision':'M2',
            'evidence_refs':['decision:na-01'],
        }
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('deliverable_independent_review_missing:pkg.schedules_bom',result['reason_codes'])

    def test_active_baseline_category_cannot_be_score_only(self):
        requirements=self.design_review_requirements()
        for requirement in requirements:
            if requirement['category']=='sections_details':
                requirement['gate']='score'
                requirement['requires_independent_review']=False
        evidence={r['requirement_id']:self.passing_evidence() for r in requirements}
        evidence['pkg.sections_details']['independent']=False
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('deliverable_category_hard_gate_missing:sections_details',result['reason_codes'])

    def test_reviewer_role_must_match_declared_requirement(self):
        requirements=self.design_review_requirements()
        evidence=self.design_review_evidence()
        evidence['pkg.dimensions_tolerances']['reviewer_role']='producer'
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('deliverable_reviewer_role_mismatch:pkg.dimensions_tolerances',result['reason_codes'])

    def test_correct_model_cannot_override_missing_required_section_detail(self):
        requirements=self.design_review_requirements()
        evidence=self.design_review_evidence()
        evidence['pkg.sections_details']['implementation_state']='missing'
        evidence['pkg.sections_details']['verification_state']='unverified'
        evidence['pkg.sections_details']['acceptance_state']='fail'
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_missing:pkg.sections_details',result['reason_codes'])
        self.assertIn('deliverable_hard_gate_fail:pkg.sections_details',result['reason_codes'])

    def test_unverified_required_dimension_evidence_blocks(self):
        requirements=self.design_review_requirements()
        evidence=self.design_review_evidence()
        evidence['pkg.dimensions_tolerances']['verification_state']='unverified'
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_item_unverified:pkg.dimensions_tolerances',result['reason_codes'])

    def test_stale_artifact_or_source_revision_blocks(self):
        requirements=self.design_review_requirements()
        evidence=self.design_review_evidence()
        evidence['pkg.revision_issue_identity']['artifact_revision']='D1'
        evidence['pkg.notes_specifications_legends']['source_revision']='M1'
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('deliverable_artifact_revision_stale:pkg.revision_issue_identity',result['reason_codes'])
        self.assertIn('deliverable_source_revision_stale:pkg.notes_specifications_legends',result['reason_codes'])

    def test_required_independent_review_cannot_be_self_certified(self):
        requirements=self.design_review_requirements()
        evidence=self.design_review_evidence()
        evidence['pkg.downstream_usability']['independent']=False
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',result['result'])
        self.assertIn('deliverable_independent_review_missing:pkg.downstream_usability',result['reason_codes'])

    def test_score_items_report_quality_but_cannot_override_hard_gate(self):
        requirements=self.design_review_requirements()
        requirements.append(self.requirement('plans_views',gate='score',independent=False,floor='concept') | {
            'requirement_id':'quality.graphic_hierarchy'
        })
        evidence=self.design_review_evidence()
        evidence['quality.graphic_hierarchy']=self.passing_evidence()
        evidence['quality.graphic_hierarchy']['acceptance_state']='fail'
        evidence['quality.graphic_hierarchy']['independent']=False
        result=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('pass',result['result'])
        self.assertEqual(0.0,result['quality_score'])
        self.assertIn('deliverable_quality_fail:quality.graphic_hierarchy',result['quality_findings'])

        evidence['pkg.sections_details']['acceptance_state']='fail'
        blocked=assess_human_deliverables(
            'design_review',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('blocked',blocked['result'])
        self.assertEqual(0.0,blocked['quality_score'])

    def test_technical_draft_has_smaller_category_floor_than_design_review(self):
        categories={'plans_views','datums_references','revision_issue_identity','scale_readability'}
        requirements=[self.requirement(category) for category in categories]
        evidence={r['requirement_id']:self.passing_evidence() for r in requirements}
        result=assess_human_deliverables(
            'technical_draft',requirements,evidence,
            package_revision='D2',source_revision='M2',
        )
        self.assertEqual('pass',result['result'])
        self.assertNotIn('schedules_bom',result['required_categories'])


if __name__=='__main__':
    unittest.main()
