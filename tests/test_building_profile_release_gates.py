"""Profile-level negative benchmarks for semantic dependency release gates."""
import copy
import json
import unittest
from pathlib import Path

from execution.catalog_resolver import resolve_catalog_assets
from execution.stage_runner import LOCAL_CAPABILITIES, run_profile

ROOT=Path(__file__).resolve().parents[1]


def load_profile(domain: str):
    return json.loads((ROOT/'domains'/domain/'agent-profile.json').read_text(encoding='utf-8'))


def all_pass_inputs(profile):
    capabilities={semantic:{'result':'pass'} for semantic in LOCAL_CAPABILITIES}
    by_software={}
    for stage in profile['stages']:
        for software in stage.get('software_candidates',[]):
            bucket=by_software.setdefault(software,{})
            for semantic in stage.get('required_capabilities',[]):
                if semantic not in LOCAL_CAPABILITIES:
                    bucket[semantic]={'result':'pass'}
    stage_checks={stage['stage_id']:{'result':'pass'} for stage in profile['stages']}
    dependencies={}
    for stage in profile['stages']:
        states={}
        for requirement in stage.get('dependency_requirements',[]):
            states[requirement['dependency_id']]={'state':'resolved'}
        if states:
            dependencies[stage['stage_id']]=states
    return capabilities,by_software,stage_checks,dependencies


class BuildingProfileReleaseGateTests(unittest.TestCase):
    def test_architecture_all_runtime_facts_pass_but_missing_catalog_still_blocks(self):
        profile=load_profile('building-architecture')
        capabilities,by_software,checks,deps=all_pass_inputs(profile)
        deps['component_resolution']['catalog.building-components']={
            'state':'proxy_allowed_for_scope',
            'reason_codes':['native_mapping_unresolved'],
        }
        result=run_profile(
            profile,
            capabilities=capabilities,
            capabilities_by_software=by_software,
            stage_checks=checks,
            dependency_states=deps,
        )
        self.assertEqual('blocked',result['result'])
        self.assertEqual('concept',result['recommended_release_target'])
        stage=next(x for x in result['stages'] if x['stage_id']=='component_resolution')
        self.assertIn('scope_reduction_required:catalog.building-components:concept',stage['assessment_reason_codes'])

    def test_architecture_runtime_proxy_maximum_cannot_override_profile_ceiling(self):
        profile=load_profile('building-architecture')
        capabilities,by_software,checks,deps=all_pass_inputs(profile)
        deps['component_resolution']['catalog.building-components']={
            'state':'proxy_allowed_for_scope',
            'maximum_release':'ready_for_professional_review',
        }
        result=run_profile(profile,capabilities=capabilities,capabilities_by_software=by_software,stage_checks=checks,dependency_states=deps)
        self.assertEqual('blocked',result['result'])
        self.assertEqual('concept',result['recommended_release_target'])


    def test_current_building_catalog_deterministically_blocks_design_review(self):
        profile=load_profile('building-architecture')
        catalog=json.loads((ROOT/'catalogs'/'building-components'/'catalog.json').read_text(encoding='utf-8'))
        capabilities,by_software,checks,deps=all_pass_inputs(profile)
        catalog_state=resolve_catalog_assets(
            catalog,
            software_id='sketchup',
            required_asset_ids=['door.generic.single.v1'],
            registry_evidence={},
            runtime_capability={'result':'pass'},
        )
        deps['component_resolution']['catalog.building-components']=catalog_state
        result=run_profile(
            profile,
            capabilities=capabilities,
            capabilities_by_software=by_software,
            stage_checks=checks,
            dependency_states=deps,
        )
        self.assertEqual('blocked',result['result'])
        stage=next(x for x in result['stages'] if x['stage_id']=='component_resolution')
        self.assertIn('dependency_blocked:catalog.building-components',stage['assessment_reason_codes'])
        self.assertIn('native_mapping_unresolved:door.generic.single.v1:sketchup',stage['assessment_reason_codes'])

    def test_architecture_missing_structural_interface_blocks_even_with_clean_geometry_runtime(self):
        profile=load_profile('building-architecture')
        capabilities,by_software,checks,deps=all_pass_inputs(profile)
        deps['semantic_building_plan']['discipline.structural-interface']={'state':'blocked','reason_codes':['structural_handoff_missing']}
        result=run_profile(profile,capabilities=capabilities,capabilities_by_software=by_software,stage_checks=checks,dependency_states=deps)
        self.assertEqual('blocked',result['result'])
        stage=next(x for x in result['stages'] if x['stage_id']=='semantic_building_plan')
        self.assertIn('dependency_blocked:discipline.structural-interface',stage['assessment_reason_codes'])

    def test_architecture_can_release_only_when_declared_dependencies_and_runtime_facts_pass(self):
        profile=load_profile('building-architecture')
        capabilities,by_software,checks,deps=all_pass_inputs(profile)
        result=run_profile(profile,capabilities=capabilities,capabilities_by_software=by_software,stage_checks=checks,dependency_states=deps)
        self.assertEqual('pass',result['result'])
        self.assertIsNone(result['recommended_release_target'])

    def test_structural_construction_candidate_activates_analysis_material_and_standard_dependencies(self):
        profile=load_profile('building-structural')
        profile=copy.deepcopy(profile)
        profile['release_target']='fabrication_or_construction_candidate'
        capabilities,by_software,checks,deps=all_pass_inputs(profile)
        for dependency_id in [
            'analysis.structural-capacity-route',
            'evidence.structural-materials-loads',
            'standards.structural-applicability',
        ]:
            deps['release_gate'].pop(dependency_id,None)
        result=run_profile(profile,capabilities=capabilities,capabilities_by_software=by_software,stage_checks=checks,dependency_states=deps)
        self.assertEqual('blocked',result['result'])
        stage=next(x for x in result['stages'] if x['stage_id']=='release_gate')
        self.assertIn('dependency_state_unknown:analysis.structural-capacity-route',stage['assessment_reason_codes'])
        self.assertIn('dependency_state_unknown:evidence.structural-materials-loads',stage['assessment_reason_codes'])
        self.assertIn('dependency_state_unknown:standards.structural-applicability',stage['assessment_reason_codes'])


if __name__=='__main__':
    unittest.main()
