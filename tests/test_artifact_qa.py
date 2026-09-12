"""Executable QA and artifact evidence acceptance tests."""
import unittest

from execution.artifact_evidence import artifact_manifest, evidence_is_stale
from execution.qa_checker import checker_verdict

class ArtifactEvidenceTests(unittest.TestCase):
 def test_manifest_binds_identity_and_versions(self):
  m=artifact_manifest(run_id='r1',artifact_id='a1',sha256='a'*64,source_hashes=['b'*64],versions={'domain':'0.2.0'},reopened=True)
  self.assertEqual('a'*64,m['artifact_sha256']); self.assertTrue(m['reopened'])
 def test_changed_artifact_hash_stales_evidence(self):
  self.assertTrue(evidence_is_stale({'artifact_sha256':'a'*64},current_artifact_sha256='b'*64))
  self.assertFalse(evidence_is_stale({'artifact_sha256':'a'*64},current_artifact_sha256='a'*64))

class CheckerVerdictTests(unittest.TestCase):
 def test_blocker_unknown_blocks_release(self):
  findings=[{'finding_id':'f1','severity':'BLOCKER','result':'unknown','artifact_sha256':'a'*64}]
  r=checker_verdict(findings,current_artifact_sha256='a'*64)
  self.assertEqual('BLOCKED',r['verdict'])
 def test_fail_is_fail(self):
  findings=[{'finding_id':'f1','severity':'MAJOR','result':'fail','artifact_sha256':'a'*64}]
  self.assertEqual('FAIL',checker_verdict(findings,current_artifact_sha256='a'*64)['verdict'])
 def test_stale_precedes_old_pass(self):
  findings=[{'finding_id':'f1','severity':'BLOCKER','result':'pass','artifact_sha256':'a'*64}]
  self.assertEqual('STALE_EVIDENCE',checker_verdict(findings,current_artifact_sha256='b'*64)['verdict'])
 def test_all_pass_can_pass_declared_scope(self):
  findings=[{'finding_id':'f1','severity':'BLOCKER','result':'pass','artifact_sha256':'a'*64},{'finding_id':'f2','severity':'MINOR','result':'not_applicable','artifact_sha256':'a'*64}]
  self.assertEqual('PASS_FOR_DECLARED_SCOPE',checker_verdict(findings,current_artifact_sha256='a'*64)['verdict'])

if __name__=='__main__': unittest.main()

class ExternalArtifactHashTests(unittest.TestCase):
 def test_engine_neutral_file_hash_is_deterministic(self):
  import tempfile
  from pathlib import Path
  from execution.artifact_evidence import sha256_file
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'artifact.bin'; p.write_bytes(b'CDT-Engineer')
   self.assertEqual(sha256_file(p),sha256_file(p))
   self.assertEqual(64,len(sha256_file(p)))
