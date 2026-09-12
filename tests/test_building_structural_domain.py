"""Contract tests for the Building Structural v1 production vertical."""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT/'domains'/'building-structural'
PROFILE_SCHEMA=json.loads((ROOT/'docs'/'schemas'/'agent-profile.schema.json').read_text(encoding='utf-8'))


class BuildingStructuralDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads((DOMAIN/'domain.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator=Draft202012Validator(cls.schema)

    def make_job(self):
        return {
            'schema_version':'0.1.0',
            'job_id':'struct-01',
            'domain_id':'building-structural',
            'release_target':'design_review',
            'source_manifest':[{'source_id':'arch-1','locator':'architecture.json','sha256':'a'*64,'status':'available','role':'architectural_handoff'}],
            'units':'m',
            'scope':{'included':['structural intent','architecture coordination'],'excluded':['final member capacity design','reinforcement detailing']},
            'assumptions':[],
            'standards':[],
            'structural_basis':{
                'structural_system':{'status':'specified','value':'frame'},
                'materials':{'status':'unknown','value':None},
                'loads':{'status':'unknown','value':None},
                'standards_state':{'status':'unknown','value':None},
            },
            'grid':{'x':[0.0,4.0,8.0],'y':[0.0,3.5,7.0]},
            'members':[
                {'id':'C1','kind':'column','level_id':'L1','bounds':[1.0,1.0,1.4,1.4],'evidence_status':'inferred'},
            ],
            'load_path':{
                'graph':{'roof':['C1'],'C1':['foundation-interface'],'foundation-interface':['ground'],'ground':[]},
                'loaded_nodes':['roof'],
                'terminal_nodes':['ground']
            },
            'architecture_interface':{
                'openings':[{'id':'O1','bounds':[2.0,2.0,3.0,3.0]}],
                'clearance':0.0
            },
        }

    def test_design_review_intent_job_is_structurally_valid_with_unknown_adequacy_inputs(self):
        errors=list(self.validator.iter_errors(self.make_job()))
        self.assertEqual([],errors,'\n'.join(e.message for e in errors))

    def test_hidden_material_loads_may_remain_unknown(self):
        job=self.make_job()
        self.assertEqual('unknown',job['structural_basis']['materials']['status'])
        self.assertEqual([],list(self.validator.iter_errors(job)))

    def test_profile_validates_and_separates_design_review_from_final_analysis(self):
        profile=json.loads((DOMAIN/'agent-profile.json').read_text(encoding='utf-8'))
        errors=list(Draft202012Validator(PROFILE_SCHEMA).iter_errors(profile))
        self.assertEqual([],errors,'\n'.join(e.message for e in errors))
        by_id={stage['stage_id']:stage for stage in profile['stages']}
        deps={d['dependency_id'] for d in by_id['structural_basis']['dependency_requirements']}
        self.assertIn('domain.skills.building-structural',deps)
        coord={d['dependency_id'] for d in by_id['architecture_coordination']['dependency_requirements']}
        self.assertIn('discipline.architecture-interface',coord)
        final_analysis=next(d for d in by_id['release_gate']['dependency_requirements'] if d['dependency_id']=='analysis.structural-capacity-route')
        self.assertEqual('fabrication_or_construction_candidate',final_analysis['required_from_release'])

    def test_five_pack_and_initial_skills_exist(self):
        for name in ['domain.schema.json','rule-pack.md','template-pack.md','benchmark-pack.md','review-rubric.md','agent-profile.json']:
            self.assertTrue((DOMAIN/name).is_file(),name)
        for skill in ['structural-system-intent','load-path-check','architecture-structural-coordination','structural-qa']:
            path=DOMAIN/'skills'/skill/'SKILL.md'
            self.assertTrue(path.is_file(),str(path))
            text=path.read_text(encoding='utf-8')
            self.assertIn('## Deterministic checks',text)
            self.assertIn('## Negative cases',text)

    def test_rule_pack_explicitly_refuses_adequacy_claim_without_inputs(self):
        text=(DOMAIN/'rule-pack.md').read_text(encoding='utf-8').lower()
        self.assertIn('structural adequacy',text)
        self.assertIn('must not',text)
        self.assertIn('str-04',text)
        self.assertIn('str-06',text)


if __name__=='__main__':
    unittest.main()
