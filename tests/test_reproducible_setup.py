"""Clean-environment dependency and validation-claim regression tests."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ReproducibleSetupTests(unittest.TestCase):
    def test_root_requirements_declares_validation_dependencies(self):
        path=ROOT/'requirements.txt'
        self.assertTrue(path.is_file())
        text=path.read_text(encoding='utf-8')
        self.assertIn('jsonschema',text)
        self.assertIn('PyYAML',text)

    def test_foundation_validation_qualifies_pass_as_coverage_bounded(self):
        text=(ROOT/'docs'/'FOUNDATION_VALIDATION.md').read_text(encoding='utf-8').lower()
        self.assertIn('requirements.txt',text)
        self.assertIn('not an exhaustive correctness proof',text)

if __name__=='__main__': unittest.main()
