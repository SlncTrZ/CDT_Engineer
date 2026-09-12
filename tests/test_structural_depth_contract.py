"""Contract tests for Building Structural v0.2 bounded engineering depth.
Wing: code | Topic: structural-engineering-depth | Updated: 2026-09-12 22:52
"""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT/'domains'/'building-structural'


class StructuralDepthContractTests(unittest.TestCase):
    def test_five_pack_declares_bounded_depth_rules(self):
        rule=(DOMAIN/'rule-pack.md').read_text(encoding='utf-8')
        for rule_id in ['STR-09','STR-10','STR-11','STR-12','STR-13']:
            self.assertIn(rule_id,rule)
        self.assertIn('evaluate_load_combination',rule)
        self.assertIn('evaluate_demand_capacity_checks',rule)
        self.assertIn('evaluate_standard_applicability',rule)

    def test_new_skills_exist_with_required_safety_sections(self):
        skills=[
            'load-combination-check',
            'member-demand-capacity-check',
            'structural-standards-applicability',
        ]
        for skill in skills:
            text=(DOMAIN/'skills'/skill/'SKILL.md').read_text(encoding='utf-8')
            for heading in ['## Intent','## Preconditions / inputs','## Decision boundary','## Deterministic checks','## Workflow','## QA / outputs','## Negative cases']:
                self.assertIn(heading,text,f'{skill}: {heading}')
            self.assertIn('must not',text.lower())

    def test_schema_v02_can_represent_exact_analysis_evidence_without_requiring_it_for_design_review(self):
        schema=json.loads((DOMAIN/'domain.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        self.assertEqual('0.2.0',schema['properties']['schema_version']['const'])
        self.assertIn('analysis_evidence',schema['properties'])
        self.assertNotIn('analysis_evidence',schema['required'])
        analysis=schema['properties']['analysis_evidence']['properties']
        for key in ['load_cases','load_combinations','materials','sections','demand_capacity_checks']:
            self.assertIn(key,analysis)

    def test_schema_accepts_source_bound_analysis_evidence_and_rejects_weak_standard_record(self):
        schema=json.loads((DOMAIN/'domain.schema.json').read_text(encoding='utf-8'))
        validator=Draft202012Validator(schema)
        job={
            'schema_version':'0.2.0','job_id':'struct-analysis-01','domain_id':'building-structural','release_target':'fabrication_or_construction_candidate',
            'source_manifest':[{'source_id':'basis','locator':'basis.json','sha256':'a'*64,'status':'available','role':'structural_basis'}],
            'units':'m','scope':{'included':['bounded member check'],'excluded':['connection design']},'assumptions':[],
            'standards':[{'standard_id':'STD-PROJECT-01','record_version':'1.0.0','designation':'Project structural criteria','issuer':'Project authority','source':'project-controlled://criteria','edition':'2026-09-01','verification_status':'source_verified','applicability_state':'applicable','clause_refs':['LOAD-01'],'reviewer':'lead-structural','decision_reason':'Frozen project basis.'}],
            'structural_basis':{'structural_system':{'status':'specified','value':'frame'},'materials':{'status':'specified','value':'material-01'},'loads':{'status':'derived','value':'analysis-01'},'standards_state':{'status':'specified','value':'STD-PROJECT-01'}},
            'analysis_evidence':{
                'load_cases':[{'case_id':'dead','evidence_status':'derived','effects':{'axial_kN':100.0},'source_refs':['analysis:dead']}],
                'load_combinations':[{'combination_id':'combo-01','factors':{'dead':1.2},'basis':{'source_class':'project_rule','record_id':'STD-PROJECT-01','record_version':'1.0.0','clause_or_rule_ref':'LOAD-01','verification_state':'verified'}}],
                'materials':[{'material_id':'material-01','evidence_status':'specified','source_ref':'material-schedule','properties':{'grade':'project-specified'}}],
                'sections':[{'section_id':'section-B1','evidence_status':'specified','source_ref':'section-schedule','material_ref':'material-01','properties':{'width_mm':300,'depth_mm':500}}],
                'demand_capacity_checks':[{'check_id':'B1-axial','member_id':'B1','demand':120.0,'capacity':180.0,'unit':'kN','limit':1.0,'demand_evidence_status':'derived','capacity_evidence_status':'derived','section_ref':'section-B1','material_ref':'material-01','basis':{'source_class':'calculation_method','record_id':'calc-route-01','record_version':'1.0.0','clause_or_rule_ref':'CHECK-01','verification_state':'verified'}}]
            },
            'grid':{'x':[0.0,4.0],'y':[0.0,4.0]},'members':[{'id':'B1','kind':'beam','level_id':'L1','bounds':[0.0,0.0,4.0,0.3],'evidence_status':'specified','section':{'section_id':'section-B1'},'material_ref':'material-01'}],
            'load_path':{'graph':{'B1':['foundation-interface'],'foundation-interface':['ground'],'ground':[]},'loaded_nodes':['B1'],'terminal_nodes':['ground']},
            'architecture_interface':{'openings':[],'clearance':0.0}
        }
        self.assertEqual([],list(validator.iter_errors(job)))
        weak=json.loads(json.dumps(job))
        weak['standards']=[{'standard_id':'STD-WEAK','record_version':'1','source':'somewhere','edition':'latest','applicability':'maybe','status':'proposed'}]
        self.assertTrue(list(validator.iter_errors(weak)))

    def test_release_gate_names_bounded_calculation_skills_for_stronger_release(self):
        profile=json.loads((DOMAIN/'agent-profile.json').read_text(encoding='utf-8'))
        release=next(stage for stage in profile['stages'] if stage['stage_id']=='release_gate')
        deps={item['dependency_id']:item for item in release['dependency_requirements']}
        for dep in ['domain.skill.load-combination-check','domain.skill.member-demand-capacity-check','domain.skill.structural-standards-applicability']:
            self.assertIn(dep,deps)
            self.assertEqual('fabrication_or_construction_candidate',deps[dep]['required_from_release'])

    def test_benchmarks_cover_arithmetic_failure_provenance_and_interfaces(self):
        text=(DOMAIN/'benchmark-pack.md').read_text(encoding='utf-8').lower()
        for phrase in ['load combination','demand/capacity','unverified standard','connection/foundation interface']:
            self.assertIn(phrase,text)


if __name__=='__main__':
    unittest.main()
