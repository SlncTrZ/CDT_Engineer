"""Contract tests for the Building Architecture v1 production vertical."""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT/'domains'/'building-architecture'
PROFILE_SCHEMA=json.loads((ROOT/'docs'/'schemas'/'agent-profile.schema.json').read_text(encoding='utf-8'))


class BuildingArchitectureDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.domain_schema=json.loads((DOMAIN/'domain.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.domain_schema)
        cls.validator=Draft202012Validator(cls.domain_schema)

    def make_job(self):
        return {
            'schema_version':'0.2.0',
            'job_id':'house-01',
            'domain_id':'building-architecture',
            'release_target':'design_review',
            'source_manifest':[{'source_id':'img-1','locator':'reference.jpg','sha256':'a'*64,'status':'available','role':'primary_visual_reference'}],
            'units':'m',
            'scope':{'included':['low-rise residential architectural reconstruction'],'excluded':['structural adequacy design']},
            'assumptions':[],
            'standards':[],
            'output_requirements':[{'format':'skp','purpose':'design_review','required':True}],
            'building':{
                'levels':[
                    {'id':'L1','elevation':0.0,'evidence_status':'specified'},
                    {'id':'L2','elevation':3.6,'evidence_status':'specified'},
                ],
                'spaces':[{'id':'S1','level_id':'L1','boundary':[[0,0],[4,0],[4,3],[0,3]],'evidence_status':'derived','requirements':{}}],
                'walls':[{'id':'W1','level_id':'L1','length':4.0,'height':3.2,'thickness':0.2,'evidence_status':'specified','structural_role':'unknown'}],
                'openings':[{'id':'O1','host_wall_id':'W1','kind':'door','offset':1.0,'width':1.0,'height':2.2,'sill_height':0.0,'evidence_status':'specified','component_resolution':'resolved','component_id':'door.generic.single.v1'}],
                'stairs':[],
                'feature_inventory':[{'item_id':'door-main','semantic_family':'door','required':True,'source_evidence':['img-1'],'resolution_state':'resolved','implementation_state':'implemented','verification_state':'verified'}],
            },
        }

    def test_minimal_design_review_job_is_structurally_valid(self):
        errors=list(self.validator.iter_errors(self.make_job()))
        self.assertEqual([],errors,'\n'.join(e.message for e in errors))

    def test_unknown_structural_role_is_valid_but_not_invented(self):
        job=self.make_job()
        job['building']['walls'][0]['structural_role']='unknown'
        self.assertEqual([],list(self.validator.iter_errors(job)))

    def test_component_resolution_is_explicit(self):
        job=self.make_job()
        del job['building']['openings'][0]['component_resolution']
        self.assertTrue(list(self.validator.iter_errors(job)))

    def test_required_feature_cannot_be_schema_marked_not_applicable(self):
        job=self.make_job()
        job['building']['feature_inventory'][0]['implementation_state']='not_applicable'
        self.assertTrue(list(self.validator.iter_errors(job)))


    def test_profile_validates_and_declares_fail_closed_dependencies(self):
        profile=json.loads((DOMAIN/'agent-profile.json').read_text(encoding='utf-8'))
        validator=Draft202012Validator(PROFILE_SCHEMA)
        self.assertEqual([],list(validator.iter_errors(profile)))
        self.assertEqual('environment_preflight',profile['stages'][0]['stage_id'])
        by_id={s['stage_id']:s for s in profile['stages']}
        deps={d['dependency_id'] for d in by_id['semantic_building_plan']['dependency_requirements']}
        self.assertIn('domain.skills.building-architecture',deps)
        component_deps={d['dependency_id'] for d in by_id['component_resolution']['dependency_requirements']}
        self.assertIn('catalog.building-components',component_deps)
        self.assertEqual('concept',next(d['proxy_allowed_through'] for d in by_id['component_resolution']['dependency_requirements'] if d['dependency_id']=='catalog.building-components'))

    def test_five_pack_and_initial_skills_exist(self):
        for name in ['domain.schema.json','rule-pack.md','template-pack.md','benchmark-pack.md','review-rubric.md','agent-profile.json']:
            self.assertTrue((DOMAIN/name).is_file(),name)
        for skill in ['building-source-interpretation','storey-space-plan','opening-hosting','vertical-circulation','facade-component-layout','building-qa']:
            path=DOMAIN/'skills'/skill/'SKILL.md'
            self.assertTrue(path.is_file(),str(path))
            text=path.read_text(encoding='utf-8')
            self.assertIn('## Deterministic checks',text)
            self.assertIn('## Negative cases',text)

    def test_rule_pack_forbids_silent_primitive_substitution(self):
        text=(DOMAIN/'rule-pack.md').read_text(encoding='utf-8')
        self.assertIn('silent primitive substitution',text.lower())
        self.assertIn('ARCH-06',text)
        self.assertIn('ARCH-07',text)


if __name__=='__main__':
    unittest.main()
