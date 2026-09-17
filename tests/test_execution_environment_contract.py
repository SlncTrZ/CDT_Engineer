"""Execution environment contract validation tests.
Wing: code | Topic: execution-environment | Updated: 2026-09-17
"""
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'docs'/'schemas'/'execution-environment.schema.json'

class ExecutionEnvironmentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads(SCHEMA.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.v=Draft202012Validator(cls.schema)

    def base(self):
        return {
          'schema_version':'0.1.0','host_id':'pc-windows','observed_at':'2026-09-12T12:00:00+07:00',
          'os':{'family':'windows','version':'11','architecture':'x86_64'},
          'applications':[],'providers':[]
        }

    def assert_valid(self,x): self.assertEqual([],list(self.v.iter_errors(x)))
    def assert_invalid(self,x): self.assertTrue(list(self.v.iter_errors(x)))

    def test_absent_application_is_explicit_and_has_no_fake_version(self):
        x=self.base(); x['applications']=[{'software_id':'autocad','status':'not_installed','install_path':None,'executable_path':None,'version':None,'build':None,'edition':None,'discovery_method':'registry','observed_at':x['observed_at']}]; self.assert_valid(x)

    def test_installed_application_requires_path_and_version(self):
        x=self.base(); x['applications']=[{'software_id':'autocad','status':'installed','install_path':'C:/Program Files/Autodesk/AutoCAD 2027','executable_path':'C:/Program Files/Autodesk/AutoCAD 2027/acad.exe','version':'2027','build':'R25.2','edition':'full','discovery_method':'registry+file-version','observed_at':x['observed_at']}]; self.assert_valid(x)
        x['applications'][0]['version']=None; self.assert_invalid(x)

    def test_provider_ready_is_independent_from_software_installed(self):
        x=self.base(); x['applications']=[{'software_id':'solidworks','status':'installed','install_path':'C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS','executable_path':'C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS/SLDWORKS.exe','version':'2026','build':None,'edition':None,'discovery_method':'file-version','observed_at':x['observed_at']}]
        x['providers']=[{'provider_id':'cdt-solidworks','software_id':'solidworks','status':'not_ready','provider_version':'0.1.0','contract_version':'1','discovered_capabilities':[],'observed_at':x['observed_at']}]; self.assert_valid(x)

    def test_ready_provider_requires_runtime_version_and_capabilities(self):
        x=self.base(); x['providers']=[{'provider_id':'cdt-autocad','software_id':'autocad','status':'ready','provider_version':None,'contract_version':'1','discovered_capabilities':[],'observed_at':x['observed_at']}]; self.assert_invalid(x)

if __name__=='__main__': unittest.main()
