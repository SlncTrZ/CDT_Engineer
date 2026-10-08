"""Contract checks for concrete software operating guides."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SoftwareGuideTests(unittest.TestCase):
 def test_guides_exist_and_cover_required_contract_sections(self):
  required=['Step-0','Compatibility','Semantic capability map','Feature chunks','Transaction and recovery','Chunk budgets','Read-after-write','Artifact lifecycle','Known blockers','Benchmarks']
  for sw in ['autocad','sketchup','solidworks']:
   p=ROOT/'software'/sw/'OPERATING_GUIDE.md'; self.assertTrue(p.is_file(),sw)
   text=p.read_text()
   for token in required: self.assertIn(token,text,(sw,token))
 def test_guides_fail_closed_on_runtime_truth(self):
  for sw in ['autocad','sketchup','solidworks']:
   text=(ROOT/'software'/sw/'OPERATING_GUIDE.md').read_text().lower()
   self.assertIn('runtime proof',text)
   self.assertIn('source',text)
 def test_autocad_guide_uses_current_feature_and_seal_paths(self):
  text=(ROOT/'software/autocad/OPERATING_GUIDE.md').read_text()
  for token in ['feature_execute','native_integrity_status','artifact_seal','10,000']:
   self.assertIn(token,text)
 def test_sketchup_guide_recognizes_native_lifecycle_identity_mesh_and_seal(self):
  text=(ROOT/'software/sketchup/OPERATING_GUIDE.md').read_text()
  for token in ['model_save','model_open','model_export','artifact_seal','artifact_verify','create_mesh','SHA-256','native_version']:
   self.assertIn(token,text)
  self.assertNotIn('artifact_seal_missing',text)
 def test_solidworks_does_not_claim_transaction_atomicity(self):
  text=(ROOT/'software/solidworks/OPERATING_GUIDE.md').read_text()
  self.assertIn('exact_transaction_mode_unproven',text)
  self.assertIn('checkpointed_atomic',text)
  self.assertIn('only after runtime proof',text)
if __name__=='__main__': unittest.main()
