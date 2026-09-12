import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from execution.stage_runner import LOCAL_CAPABILITIES

ROOT=Path(__file__).resolve().parents[1]
PROFILE_SCHEMA=ROOT/'docs'/'schemas'/'agent-profile.schema.json'
PROFILE_PATHS=sorted(ROOT.glob('domains/*/agent-profile.json'))

class AgentProfileAndMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads(PROFILE_SCHEMA.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator=Draft202012Validator(cls.schema)

    def test_profiles_validate_and_begin_with_environment_preflight(self):
        self.assertGreaterEqual(len(PROFILE_PATHS),4)
        for path in PROFILE_PATHS:
            rel=str(path.relative_to(ROOT))
            data=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual([],list(self.validator.iter_errors(data)),rel)
            self.assertEqual('environment_preflight',data['stages'][0]['stage_id'])
            self.assertIn('execution_environment.compatible_or_typed_blocker',data['stages'][0]['required_capabilities'])

    def test_every_stage_has_stop_recovery_and_qa_contract(self):
        for path in PROFILE_PATHS:
            data=json.loads(path.read_text(encoding='utf-8'))
            for stage in data['stages']:
                self.assertTrue(stage['stop_conditions'],stage['stage_id'])
                self.assertTrue(stage['recovery_actions'],stage['stage_id'])
                self.assertTrue(stage['qa_gates'],stage['stage_id'])

    def test_software_maps_are_source_contracts_not_runtime_proof(self):
        for rel in ['software/autocad/engine-map.yaml','software/sketchup/engine-map.yaml','software/solidworks/engine-map.yaml']:
            data=yaml.safe_load((ROOT/rel).read_text(encoding='utf-8'))
            self.assertFalse(data['source_snapshot']['runtime_proof'],rel)
            self.assertTrue(data['runtime_preflight']['required'],rel)
            self.assertIn('version_mismatch',data['runtime_preflight']['blocker_codes'],rel)
            self.assertTrue(data['capability_mappings'],rel)

    def test_profile_software_semantics_resolve_to_selected_maps(self):
        maps={}
        for software in ['autocad','sketchup','solidworks']:
            data=yaml.safe_load((ROOT/'software'/software/'engine-map.yaml').read_text(encoding='utf-8'))
            maps[software]={x['semantic']:x for x in data['capability_mappings']}
        local=set(LOCAL_CAPABILITIES)
        for path in PROFILE_PATHS:
            rel=str(path.relative_to(ROOT))
            data=json.loads(path.read_text(encoding='utf-8'))
            for stage in data['stages']:
                covered=set().union(*(set(maps.get(s,{})) for s in stage['software_candidates'])) if stage['software_candidates'] else set()
                for capability in stage['required_capabilities']:
                    self.assertTrue(capability in local or capability in covered, f"{rel}:{stage['stage_id']} unresolved semantic {capability}")

    def test_map_capabilities_declare_support_state(self):
        for software in ['autocad','sketchup','solidworks']:
            data=yaml.safe_load((ROOT/'software'/software/'engine-map.yaml').read_text(encoding='utf-8'))
            for mapping in data['capability_mappings']:
                self.assertIn(mapping['support'], {'expected','blocked','unproven'})
                self.assertNotIn(mapping['semantic'], LOCAL_CAPABILITIES, f"{software}:{mapping['semantic']} collides with Engineering-OS local capability")

    def test_autocad_map_matches_current_public_contract_identity_and_tools(self):
        data=yaml.safe_load((ROOT/'software/autocad/engine-map.yaml').read_text(encoding='utf-8'))
        self.assertEqual('0.4.0rc1',data['source_snapshot']['provider_version'])
        self.assertEqual('autocad-generic-v1-rc1',data['source_snapshot']['contract_version'])
        self.assertEqual(86,data['source_snapshot']['public_tool_count'])
        tools={t for row in data['capability_mappings'] for t in row.get('expected_public_tools',[])}
        for required in ['feature_execute','document_dependencies','object_get','object_measure','artifact_seal']:
            self.assertIn(required,tools)
        for stale in ['drawing_info','entity_list','entity_get','analysis_measure_entity','drawing_deliver']:
            self.assertNotIn(stale,tools)

    def test_sketchup_map_matches_current_public_contract_and_lifecycle(self):
        data=yaml.safe_load((ROOT/'software/sketchup/engine-map.yaml').read_text(encoding='utf-8'))
        self.assertEqual('0.1.0',data['source_snapshot']['provider_version'])
        self.assertEqual('0.25',data['source_snapshot']['contract_version'])
        self.assertEqual(64,data['source_snapshot']['public_tool_count'])
        by_semantic={x['semantic']:x for x in data['capability_mappings']}
        self.assertEqual('expected',by_semantic['artifact.native_save']['support'])
        self.assertEqual(['model_save','model_save_as'],by_semantic['artifact.native_save']['expected_public_tools'])
        self.assertEqual('expected',by_semantic['artifact.reopen']['support'])
        self.assertIn('model_open',by_semantic['artifact.reopen']['expected_public_tools'])
        self.assertEqual('blocked',by_semantic['artifact.seal']['support'])
        self.assertEqual('unproven',by_semantic['component.library_resolve']['support'])
        for required in ['asset_list','place_asset','definition_info','get_entity_state']:
            self.assertIn(required,by_semantic['component.library_resolve']['expected_public_tools'])
        tools={t for row in data['capability_mappings'] for t in row.get('expected_public_tools',[])}
        for required in ['transform_entity','material_assign','asset_list','place_asset','model_export','model_save','model_open']:
            self.assertIn(required,tools)
        for stale in ['transform_component','set_material','export_scene']:
            self.assertNotIn(stale,tools)

    def test_building_architecture_requires_native_component_registry_route(self):
        data=json.loads((ROOT/'domains/building-architecture/agent-profile.json').read_text(encoding='utf-8'))
        by_id={stage['stage_id']:stage for stage in data['stages']}
        stage=by_id['component_resolution']
        self.assertEqual(['sketchup'],stage['software_candidates'])
        self.assertIn('component.library_resolve',stage['required_capabilities'])
        self.assertIn('dependency.validate',stage['required_capabilities'])

    def test_profile_versions_reflect_breaking_evidence_semantics(self):
        for rel in ['domains/site-reconstruction/agent-profile.json','domains/mechanical-reconstruction/agent-profile.json']:
            data=json.loads((ROOT/rel).read_text(encoding='utf-8'))
            self.assertEqual('1.0.0',data['version'],rel)

    def test_release_critical_evidence_is_machine_required(self):
        site=json.loads((ROOT/'domains/site-reconstruction/agent-profile.json').read_text(encoding='utf-8'))
        by_id={stage['stage_id']:stage for stage in site['stages']}
        self.assertIn('evidence.source_hashes_verified',by_id['source_closure']['required_capabilities'])
        self.assertIn('evidence.artifact_hash_bound',by_id['sketchup_handoff']['required_capabilities'])
        self.assertIn('evidence.sketchup_hash_current',by_id['final_qa_and_seal']['required_capabilities'])
        mech=json.loads((ROOT/'domains/mechanical-reconstruction/agent-profile.json').read_text(encoding='utf-8'))
        by_id={stage['stage_id']:stage for stage in mech['stages']}
        self.assertIn('evidence.source_hashes_verified',by_id['drawing_interpretation']['required_capabilities'])
        self.assertIn('evidence.round_trip_verified',by_id['neutral_export_and_release']['required_capabilities'])

if __name__=='__main__': unittest.main()
