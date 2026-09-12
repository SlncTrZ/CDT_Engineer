"""Acceptance tests for bounded Building Structural engineering depth.
Wing: code | Topic: structural-engineering-depth | Updated: 2026-09-12 22:40
"""
import unittest

from domains.building_structural.calculations import (
    evaluate_demand_capacity_checks,
    evaluate_load_combination,
)
from domains.building_structural.interfaces import evaluate_architecture_structural_interfaces
from domains.building_structural.standards import evaluate_standard_applicability
from domains.guard_primitives import GuardInputError


VERIFIED_BASIS={
    'source_class':'project_rule',
    'record_id':'project-structural-basis',
    'record_version':'1.0.0',
    'clause_or_rule_ref':'LR-01',
    'verification_state':'verified',
}


class StructuralEngineeringDepthTests(unittest.TestCase):
    def test_load_combination_is_explicit_source_bound_and_deterministic(self):
        cases={
            'dead':{'evidence_status':'specified','effects':{'axial_kN':100.0,'moment_kNm':10.0}},
            'live':{'evidence_status':'specified','effects':{'axial_kN':40.0,'moment_kNm':6.0}},
        }
        combination={
            'combination_id':'project-combo-01',
            'factors':{'dead':1.2,'live':1.5},
            'basis':VERIFIED_BASIS,
        }
        result=evaluate_load_combination(cases,combination)
        self.assertEqual('pass',result['result'])
        self.assertAlmostEqual(180.0,result['combined_effects']['axial_kN'])
        self.assertAlmostEqual(21.0,result['combined_effects']['moment_kNm'])
        self.assertEqual('project-structural-basis',result['calculation_evidence']['basis']['record_id'])

    def test_load_combination_blocks_unverified_basis_or_unresolved_case(self):
        cases={'dead':{'evidence_status':'unknown','effects':{'axial_kN':100.0}}}
        combination={
            'combination_id':'combo',
            'factors':{'dead':1.0},
            'basis':{**VERIFIED_BASIS,'verification_state':'metadata_only'},
        }
        result=evaluate_load_combination(cases,combination)
        self.assertEqual('blocked',result['result'])
        self.assertIn('combination_basis_unverified',result['reason_codes'])
        self.assertIn('load_case_evidence_unresolved:dead',result['reason_codes'])
        self.assertNotIn('combined_effects',result)

    def test_load_combination_rejects_component_or_case_omission(self):
        cases={
            'dead':{'evidence_status':'specified','effects':{'axial_kN':100.0,'moment_kNm':10.0}},
            'live':{'evidence_status':'specified','effects':{'axial_kN':40.0}},
        }
        combination={'combination_id':'combo','factors':{'dead':1.0,'live':1.0},'basis':VERIFIED_BASIS}
        with self.assertRaises(GuardInputError):
            evaluate_load_combination(cases,combination)
        with self.assertRaises(GuardInputError):
            evaluate_load_combination(cases,{'combination_id':'combo','factors':{'wind':1.0},'basis':VERIFIED_BASIS})

    def test_calculation_basis_rejects_unknown_source_class(self):
        cases={'dead':{'evidence_status':'specified','effects':{'axial_kN':10.0}}}
        with self.assertRaises(GuardInputError):
            evaluate_load_combination(cases,{
                'combination_id':'combo','factors':{'dead':1.0},
                'basis':{**VERIFIED_BASIS,'source_class':'memory_guess'},
            })

    def test_demand_capacity_check_pass_fail_and_provenance_block(self):
        checks=[
            {
                'check_id':'beam-b1-moment',
                'member_id':'B1',
                'demand':80.0,
                'capacity':100.0,
                'unit':'kNm',
                'limit':1.0,
                'demand_evidence_status':'derived',
                'capacity_evidence_status':'derived',
                'basis':VERIFIED_BASIS,
                'section_ref':'section-B1',
                'material_ref':'material-concrete-01',
            }
        ]
        result=evaluate_demand_capacity_checks(checks)
        self.assertEqual('pass',result['result'])
        self.assertAlmostEqual(0.8,result['checks'][0]['utilization'])

        failing=[{**checks[0],'demand':120.0}]
        result=evaluate_demand_capacity_checks(failing)
        self.assertEqual('fail',result['result'])
        self.assertIn('demand_exceeds_capacity:beam-b1-moment',result['reason_codes'])

        blocked=[{**checks[0],'capacity_evidence_status':'unknown'}]
        result=evaluate_demand_capacity_checks(blocked)
        self.assertEqual('blocked',result['result'])
        self.assertIn('capacity_evidence_unresolved:beam-b1-moment',result['reason_codes'])
        self.assertIsNone(result['checks'][0]['utilization'])

    def test_demand_capacity_check_never_derives_missing_capacity(self):
        with self.assertRaises(GuardInputError):
            evaluate_demand_capacity_checks([{
                'check_id':'B1','member_id':'B1','demand':10.0,'capacity':None,'unit':'kN','limit':1.0,
                'demand_evidence_status':'derived','capacity_evidence_status':'unknown','basis':VERIFIED_BASIS,
                'section_ref':'section-B1','material_ref':'material-01',
            }])

    def test_architecture_structural_interface_requires_owner_evidence_and_disposition(self):
        accepted=[{
            'interface_id':'stair-slab-01',
            'from_discipline':'building-architecture',
            'to_discipline':'building-structural',
            'interface_type':'stair_slab_opening',
            'owner_discipline':'building-structural',
            'required':True,
            'status':'accepted',
            'verification_state':'verified',
            'source_revision':'arch-r4',
            'evidence_refs':['measurement:opening-01','decision:struct-17'],
        }]
        self.assertEqual('pass',evaluate_architecture_structural_interfaces(accepted)['result'])

        open_item=[{**accepted[0],'status':'open','verification_state':'unverified','evidence_refs':[]}]
        result=evaluate_architecture_structural_interfaces(open_item)
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_interface_unresolved:stair-slab-01',result['reason_codes'])

    def test_architecture_structural_interface_rejects_scope_creep(self):
        with self.assertRaises(GuardInputError):
            evaluate_architecture_structural_interfaces([{
                'interface_id':'mep-01','from_discipline':'building-structural','to_discipline':'mep',
                'interface_type':'penetration','owner_discipline':'mep','required':True,'status':'accepted',
                'verification_state':'verified','source_revision':'mep-r1','evidence_refs':['x'],
            }])

    def test_standard_applicability_requires_exact_edition_verified_source_and_clause_mapping(self):
        records=[{
            'standard_id':'STD-PROJECT-STRUCT-01',
            'record_version':'1.0.0',
            'designation':'Project Structural Design Criteria',
            'issuer':'Project authority',
            'edition':'2026-09-01',
            'source':'project-controlled://structural-design-criteria',
            'verification_status':'source_verified',
            'applicability_state':'applicable',
            'clause_refs':['LOAD-01'],
            'reviewer':'lead-structural',
            'decision_reason':'Selected project-controlled design basis for this fixture.',
        }]
        result=evaluate_standard_applicability(records,required_standard_ids=['STD-PROJECT-STRUCT-01'])
        self.assertEqual('pass',result['result'])
        self.assertEqual(['STD-PROJECT-STRUCT-01'],result['applicable_standard_ids'])

        bad=[{**records[0],'edition':'latest','verification_status':'metadata_only','clause_refs':[]}]
        result=evaluate_standard_applicability(bad,required_standard_ids=['STD-PROJECT-STRUCT-01'])
        self.assertEqual('blocked',result['result'])
        self.assertIn('standard_edition_not_exact:STD-PROJECT-STRUCT-01',result['reason_codes'])
        self.assertIn('standard_source_not_verified:STD-PROJECT-STRUCT-01',result['reason_codes'])
        self.assertIn('standard_clause_mapping_missing:STD-PROJECT-STRUCT-01',result['reason_codes'])

    def test_standard_conflict_never_auto_resolves(self):
        records=[{
            'standard_id':'STD-A','record_version':'1','designation':'A','issuer':'Authority A','edition':'2025',
            'source':'authority-a://std-a','verification_status':'source_verified','applicability_state':'conflict',
            'clause_refs':['1.1'],'reviewer':'lead','decision_reason':'Conflict with project requirement remains open.',
        }]
        result=evaluate_standard_applicability(records,required_standard_ids=['STD-A'])
        self.assertEqual('blocked',result['result'])
        self.assertIn('standard_applicability_conflict:STD-A',result['reason_codes'])


if __name__=='__main__':
    unittest.main()
