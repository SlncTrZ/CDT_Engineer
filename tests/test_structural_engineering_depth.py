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


INTERFACE_CONTEXT={
    'current_revisions':{
        'building-architecture':'arch-r4',
        'building-structural':'struct-r2',
    },
    'expected_unit_system':'mm',
    'expected_coordinate_frame_id':'project-grid-A',
}


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

    def test_load_combination_rejects_nonfinite_intermediate_or_output(self):
        cases={
            'positive':{'evidence_status':'specified','effects':{'N_kN':1e308}},
            'negative':{'evidence_status':'specified','effects':{'N_kN':-1e308}},
        }
        combination={'combination_id':'overflow','factors':{'positive':2.0,'negative':2.0},'basis':VERIFIED_BASIS}
        with self.assertRaises(GuardInputError):
            evaluate_load_combination(cases,combination)

    def test_load_combination_normal_cancellation_remains_finite(self):
        cases={
            'positive':{'evidence_status':'specified','effects':{'N_kN':1e10}},
            'negative':{'evidence_status':'specified','effects':{'N_kN':-1e10}},
        }
        combination={'combination_id':'cancel','factors':{'positive':1.0,'negative':1.0},'basis':VERIFIED_BASIS}
        result=evaluate_load_combination(cases,combination)
        self.assertEqual('pass',result['result'])
        self.assertEqual(0.0,result['combined_effects']['N_kN'])


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
            'handoff_revision':'coord-r7',
            'unit_system':'mm',
            'coordinate_frame_id':'project-grid-A',
            'conflict_state':'none',
            'evidence_refs':['measurement:opening-01','decision:struct-17'],
        }]
        self.assertEqual(
            'pass',
            evaluate_architecture_structural_interfaces(accepted,**INTERFACE_CONTEXT)['result'],
        )

        open_item=[{**accepted[0],'status':'open','verification_state':'unverified','evidence_refs':[]}]
        result=evaluate_architecture_structural_interfaces(open_item,**INTERFACE_CONTEXT)
        self.assertEqual('blocked',result['result'])
        self.assertIn('required_interface_unresolved:stair-slab-01',result['reason_codes'])

    def test_required_not_applicable_interface_requires_verified_current_evidence(self):
        base={
            'interface_id':'na-01','from_discipline':'building-architecture','to_discipline':'building-structural',
            'interface_type':'facade_support','owner_discipline':'building-structural','required':True,
            'status':'not_applicable','verification_state':'verified','source_revision':'arch-r4',
            'handoff_revision':'coord-r8','unit_system':'mm','coordinate_frame_id':'project-grid-A',
            'conflict_state':'none','evidence_refs':['decision:na-01'],
        }
        self.assertEqual(
            'pass',
            evaluate_architecture_structural_interfaces([base],**INTERFACE_CONTEXT)['result'],
        )
        for patch,reason in [
            ({'verification_state':'unverified'},'not_applicable_interface_not_verified:na-01'),
            ({'verification_state':'stale'},'interface_evidence_stale:na-01'),
            ({'evidence_refs':[]},'not_applicable_interface_without_evidence:na-01'),
        ]:
            result=evaluate_architecture_structural_interfaces(
                [{**base,**patch}],**INTERFACE_CONTEXT
            )
            self.assertEqual('blocked',result['result'])
            self.assertIn(reason,result['reason_codes'])


    def test_interface_stale_revision_invalidates_verified_handoff(self):
        record={
            'interface_id':'stair-slab-02','from_discipline':'building-architecture',
            'to_discipline':'building-structural','interface_type':'stair_slab_opening',
            'owner_discipline':'building-structural','required':True,'status':'accepted',
            'verification_state':'verified','source_revision':'arch-r3','handoff_revision':'coord-r9',
            'unit_system':'mm','coordinate_frame_id':'project-grid-A','conflict_state':'none',
            'evidence_refs':['measurement:opening-02'],
        }
        result=evaluate_architecture_structural_interfaces([record],**INTERFACE_CONTEXT)
        self.assertEqual('blocked',result['result'])
        self.assertIn('interface_source_revision_stale:stair-slab-02',result['reason_codes'])

    def test_interface_units_frame_and_open_conflict_are_hard_gates(self):
        record={
            'interface_id':'facade-01','from_discipline':'building-architecture',
            'to_discipline':'building-structural','interface_type':'facade_support',
            'owner_discipline':'building-structural','required':True,'status':'accepted',
            'verification_state':'verified','source_revision':'arch-r4','handoff_revision':'coord-r10',
            'unit_system':'inch','coordinate_frame_id':'local-origin','conflict_state':'open',
            'evidence_refs':['measurement:facade-01'],
        }
        result=evaluate_architecture_structural_interfaces([record],**INTERFACE_CONTEXT)
        self.assertEqual('blocked',result['result'])
        self.assertIn('interface_unit_system_mismatch:facade-01',result['reason_codes'])
        self.assertIn('interface_coordinate_frame_mismatch:facade-01',result['reason_codes'])
        self.assertIn('interface_conflict_open:facade-01',result['reason_codes'])

    def test_resolved_conflict_requires_owner_and_evidence(self):
        base={
            'interface_id':'column-opening-01','from_discipline':'building-architecture',
            'to_discipline':'building-structural','interface_type':'column_opening',
            'owner_discipline':'building-structural','required':True,'status':'accepted',
            'verification_state':'verified','source_revision':'arch-r4','handoff_revision':'coord-r11',
            'unit_system':'mm','coordinate_frame_id':'project-grid-A','conflict_state':'resolved',
            'evidence_refs':['measurement:column-opening-01'],
        }
        result=evaluate_architecture_structural_interfaces([base],**INTERFACE_CONTEXT)
        self.assertEqual('blocked',result['result'])
        self.assertIn('resolved_conflict_owner_missing:column-opening-01',result['reason_codes'])
        self.assertIn('resolved_conflict_evidence_missing:column-opening-01',result['reason_codes'])

        resolved={
            **base,
            'conflict_owner_discipline':'building-architecture',
            'conflict_evidence_refs':['decision:coord-44'],
        }
        self.assertEqual(
            'pass',
            evaluate_architecture_structural_interfaces([resolved],**INTERFACE_CONTEXT)['result'],
        )

    def test_architecture_structural_interface_rejects_scope_creep(self):
        with self.assertRaises(GuardInputError):
            evaluate_architecture_structural_interfaces([{
                'interface_id':'mep-01','from_discipline':'building-structural','to_discipline':'mep',
                'interface_type':'penetration','owner_discipline':'mep','required':True,'status':'accepted',
                'verification_state':'verified','source_revision':'mep-r1','handoff_revision':'coord-r1',
                'unit_system':'mm','coordinate_frame_id':'project-grid-A','conflict_state':'none',
                'evidence_refs':['x'],
            }],**INTERFACE_CONTEXT)

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
