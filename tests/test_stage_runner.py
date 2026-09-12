"""Acceptance tests for the deterministic Agent Profile stage runner."""
import unittest

from execution.stage_runner import run_profile

PROFILE={
 'profile_id':'demo','release_target':'ready_for_professional_review','stages':[
  {'stage_id':'preflight','depends_on':[],'required_capabilities':['env.ready'],'checkpoint':'env'},
  {'stage_id':'registration','depends_on':['preflight'],'required_capabilities':['model.measure'],'checkpoint':'reg'},
  {'stage_id':'handoff','depends_on':['registration'],'required_capabilities':['artifact.reopen'],'checkpoint':'out'},
 ]}

class StageRunnerTests(unittest.TestCase):
 def test_unknown_capability_fails_closed(self):
  r=run_profile(PROFILE,capabilities={},stage_checks={})
  self.assertEqual('unknown',r['stages'][0]['assessment_result'])
  self.assertEqual('blocked',r['stages'][1]['release_result'])
  self.assertEqual('blocked',r['result'])

 def test_dependency_does_not_hide_stage_diagnostic(self):
  caps={'env.ready':{'result':'blocked','reason_codes':['runtime_unknown']},'model.measure':{'result':'pass'},'artifact.reopen':{'result':'blocked','reason_codes':['native_reopen_unproven']}}
  checks={'registration':{'result':'unknown','reason_codes':['approved_tolerance_unresolved']}}
  r=run_profile(PROFILE,capabilities=caps,stage_checks=checks)
  reg=r['stages'][1]; hand=r['stages'][2]
  self.assertEqual('unknown',reg['assessment_result'])
  self.assertEqual('blocked',reg['release_result'])
  self.assertIn('dependency_not_released',reg['release_reason_codes'])
  self.assertEqual('blocked',hand['assessment_result'])
  self.assertIn('native_reopen_unproven',hand['assessment_reason_codes'])

 def test_all_pass_releases_in_dependency_order(self):
  caps={k:{'result':'pass'} for k in ['env.ready','model.measure','artifact.reopen']}
  checks={k:{'result':'pass'} for k in ['preflight','registration','handoff']}
  r=run_profile(PROFILE,capabilities=caps,stage_checks=checks)
  self.assertEqual('pass',r['result'])
  self.assertTrue(all(s['release_result']=='pass' for s in r['stages']))

 def test_fail_has_precedence_over_unknown(self):
  caps={'env.ready':{'result':'pass'},'model.measure':{'result':'unknown'},'artifact.reopen':{'result':'pass'}}
  checks={'registration':{'result':'fail','reason_codes':['residual_exceeds_tolerance']}}
  r=run_profile(PROFILE,capabilities=caps,stage_checks=checks)
  self.assertEqual('fail',r['stages'][1]['assessment_result'])

 def test_not_applicable_dependency_does_not_block_dependents(self):
  profile={'profile_id':'na','release_target':'x','stages':[
   {'stage_id':'optional','depends_on':[],'required_capabilities':['local.optional'],'checkpoint':'a'},
   {'stage_id':'required','depends_on':['optional'],'required_capabilities':['local.required'],'checkpoint':'b'},
  ]}
  caps={'local.optional':{'result':'not_applicable'},'local.required':{'result':'pass'}}
  checks={'optional':{'result':'not_applicable'},'required':{'result':'pass'}}
  r=run_profile(profile,capabilities=caps,stage_checks=checks)
  self.assertEqual('pass',r['stages'][1]['release_result'])
  self.assertEqual('pass',r['result'])

 def test_released_failure_is_not_masked_by_downstream_dependency_block(self):
  caps={'env.ready':{'result':'pass'},'model.measure':{'result':'pass'},'artifact.reopen':{'result':'pass'}}
  checks={'preflight':{'result':'pass'},'registration':{'result':'fail','reason_codes':['measured_failure']},'handoff':{'result':'pass'}}
  r=run_profile(PROFILE,capabilities=caps,stage_checks=checks)
  self.assertEqual('fail',r['stages'][1]['release_result'])
  self.assertEqual('blocked',r['stages'][2]['release_result'])
  self.assertEqual('fail',r['result'])

if __name__=='__main__': unittest.main()

class EngineMapFactTests(unittest.TestCase):
 def test_source_expected_is_unknown_without_runtime_proof(self):
  from execution.stage_runner import capability_facts_from_engine_maps
  maps=[{'software_id':'cad','source_snapshot':{'runtime_proof':False},'capability_mappings':[{'semantic':'model.query','support':'expected'}]}]
  facts=capability_facts_from_engine_maps(maps)
  self.assertEqual('unknown',facts['model.query']['result'])
  self.assertIn('runtime_fact_required:cad:model.query',facts['model.query']['reason_codes'])

 def test_source_map_runtime_flag_cannot_promote_expected_capability_to_pass(self):
  from execution.stage_runner import capability_facts_from_engine_maps
  maps=[{'software_id':'cad','source_snapshot':{'runtime_proof':True},'capability_mappings':[{'semantic':'model.query','support':'expected'}]}]
  facts=capability_facts_from_engine_maps(maps)
  self.assertEqual('unknown',facts['model.query']['result'])
  self.assertIn('runtime_fact_required:cad:model.query',facts['model.query']['reason_codes'])

 def test_source_blocked_remains_blocked(self):
  from execution.stage_runner import capability_facts_from_engine_maps
  maps=[{'software_id':'cad','source_snapshot':{'runtime_proof':False},'capability_mappings':[{'semantic':'artifact.reopen','support':'blocked'}]}]
  facts=capability_facts_from_engine_maps(maps)
  self.assertEqual('blocked',facts['artifact.reopen']['result'])

class SoftwareBoundCapabilityTests(unittest.TestCase):

 def test_cross_software_flattening_is_rejected(self):
  from execution.stage_runner import capability_facts_from_engine_maps
  maps=[
   {'software_id':'autocad','source_snapshot':{'runtime_proof':False},'capability_mappings':[]},
   {'software_id':'sketchup','source_snapshot':{'runtime_proof':False},'capability_mappings':[]},
  ]
  with self.assertRaises(ValueError): capability_facts_from_engine_maps(maps)
 def test_blocked_engine_does_not_poison_alternative_candidate(self):
  profile={'profile_id':'multi','release_target':'x','stages':[{'stage_id':'s','depends_on':[],'software_candidates':['autocad','sketchup'],'required_capabilities':['artifact.seal'],'checkpoint':'c'}]}
  by_sw={'autocad':{'artifact.seal':{'result':'pass'}},'sketchup':{'artifact.seal':{'result':'blocked','reason_codes':['artifact_seal_missing']}}}
  r=run_profile(profile,capabilities_by_software=by_sw,stage_checks={'s':{'result':'pass'}})
  self.assertEqual('pass',r['stages'][0]['assessment_result'])
 def test_single_selected_engine_preserves_blocker(self):
  profile={'profile_id':'one','release_target':'x','stages':[{'stage_id':'s','depends_on':[],'software_candidates':['sketchup'],'required_capabilities':['artifact.seal'],'checkpoint':'c'}]}
  by_sw={'sketchup':{'artifact.seal':{'result':'blocked','reason_codes':['artifact_seal_missing']}}}
  r=run_profile(profile,capabilities_by_software=by_sw,stage_checks={'s':{'result':'pass'}})
  self.assertEqual('blocked',r['stages'][0]['assessment_result'])

class ConflictRegressionTests(unittest.TestCase):
 def test_multi_software_stage_requires_one_candidate_to_cover_all_software_semantics(self):
  profile={'profile_id':'mix','release_target':'x','stages':[{'stage_id':'s','depends_on':[],'software_candidates':['autocad','sketchup'],'required_capabilities':['cap.a','cap.b'],'checkpoint':'c'}]}
  by_sw={
   'autocad':{'cap.a':{'result':'pass'},'cap.b':{'result':'blocked','reason_codes':['no_b']}},
   'sketchup':{'cap.a':{'result':'blocked','reason_codes':['no_a']},'cap.b':{'result':'pass'}},
  }
  r=run_profile(profile,capabilities_by_software=by_sw,stage_checks={'s':{'result':'pass'}})
  self.assertNotEqual('pass',r['stages'][0]['assessment_result'])

 def test_global_fact_cannot_override_software_bound_fact(self):
  profile={'profile_id':'bound','release_target':'x','stages':[{'stage_id':'s','depends_on':[],'software_candidates':['sketchup'],'required_capabilities':['artifact.seal'],'checkpoint':'c'}]}
  by_sw={'sketchup':{'artifact.seal':{'result':'blocked','reason_codes':['artifact_seal_missing']}}}
  r=run_profile(profile,capabilities={'artifact.seal':{'result':'pass'}},capabilities_by_software=by_sw,stage_checks={'s':{'result':'pass'}})
  self.assertEqual('blocked',r['stages'][0]['assessment_result'])

 def test_global_fact_cannot_override_missing_runtime_fact_for_software_semantic(self):
  profile={'profile_id':'bound-missing','release_target':'x','stages':[{'stage_id':'s','depends_on':[],'software_candidates':['sketchup'],'required_capabilities':['artifact.seal'],'checkpoint':'c'}]}
  r=run_profile(profile,capabilities={'artifact.seal':{'result':'pass'}},capabilities_by_software={'sketchup':{}},stage_checks={'s':{'result':'pass'}})
  self.assertEqual('unknown',r['stages'][0]['assessment_result'])
  self.assertNotEqual('pass',r['result'])

 def test_source_unproven_is_typed_blocker(self):
  from execution.stage_runner import capability_facts_from_engine_maps
  maps=[{'software_id':'cad','source_snapshot':{'runtime_proof':False},'capability_mappings':[{'semantic':'topology.inspect','support':'unproven'}]}]
  facts=capability_facts_from_engine_maps(maps)
  self.assertEqual('blocked',facts['topology.inspect']['result'])
  self.assertIn('source_map_unproven:cad:topology.inspect',facts['topology.inspect']['reason_codes'])
