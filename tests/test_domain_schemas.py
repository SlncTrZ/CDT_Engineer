import copy
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

def load_schema(domain):
    return json.loads((ROOT / 'domains' / domain / 'domain.schema.json').read_text(encoding='utf-8'))

def base_common(domain_id):
    return {
        'schema_version': '0.2.0', 'job_id': 'job-test', 'domain_id': domain_id,
        'source_manifest': [{'source_id':'src-1','locator':'fixture.dwg','sha256':'a'*64,'status':'available','role':'primary'}],
        'units':'mm',
        'coordinate_frame': {'source_frame':'WCS','target_frame':'WCS','transform':[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],'status':'verified','source_units':'mm','target_units':'mm'},
        'scope': {'included':['test scope'],'excluded':[]}, 'assumptions':[], 'standards':[],
        'output_requirements':[{'format':'native','purpose':'test','required':True}],
    }

def ev(status, value, unit='mm', source_ref=None, approved_by=None):
    return {'status':status,'value':value,'unit':unit,'source_ref':source_ref,'approved_by':approved_by}

class SiteSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = Draft202012Validator(load_schema('site-reconstruction'))
    def make_job(self):
        j=base_common('site-reconstruction')
        j['registration']={
            'control_points':[{'id':'p1','source':[0,0,0],'target':[0,0,0]},{'id':'p2','source':[10,0,0],'target':[10,0,0]},{'id':'p3','source':[0,10,0],'target':[0,10,0]}],
            'tolerance':ev('unresolved',None),'dependency_ids':[],
            'layer_mapping':[{'source_layer':'0','semantic_role':'base','target_organization':'base'}],
            'fit_model':'identity_wcs','holdout_points':[{'id':'h1','source':[5,5,0],'target':[5,5,0]}]}
        return j
    def assert_valid(self,j):
        e=list(self.validator.iter_errors(j)); self.assertEqual([],e,'\n'.join(x.message for x in e))
    def assert_invalid(self,j): self.assertTrue(list(self.validator.iter_errors(j)))
    def test_unresolved_registration_tolerance_is_structurally_valid(self): self.assert_valid(self.make_job())
    def test_identity_wcs_is_canonical_fit_model(self):
        self.assert_valid(self.make_job()); j=self.make_job(); j['registration']['fit_model']='IDENTITY_WCS'; self.assert_invalid(j)
    def test_approved_registration_tolerance_requires_positive_value_and_approver(self):
        j=self.make_job(); j['registration']['tolerance']=ev('approved',0.005,source_ref='DB-REG-TOL-001',approved_by='reviewer-1'); self.assert_valid(j)
        for v in (None,0,-0.1):
            b=copy.deepcopy(j); b['registration']['tolerance']['value']=v; self.assert_invalid(b)
        b=copy.deepcopy(j); b['registration']['tolerance']['approved_by']=None; self.assert_invalid(b)

class MechanicalSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.validator=Draft202012Validator(load_schema('mechanical-reconstruction'))
    def make_job(self):
        j=base_common('mechanical-reconstruction')
        j['feature_plan']={'projection_convention':'third_angle','dimensions':[{'id':'d1','value':25.0,'tolerance':ev('unresolved',None),'source_ref':'view-front:dim-1'}], 'features':[{'id':'f1','kind':'base_extrude','depends_on':[],'dimension_ids':['d1'],'evidence_status':'observed'}]}
        return j
    def assert_valid(self,j):
        e=list(self.validator.iter_errors(j)); self.assertEqual([],e,'\n'.join(x.message for x in e))
    def assert_invalid(self,j): self.assertTrue(list(self.validator.iter_errors(j)))
    def test_unknown_manufacturing_tolerance_is_structurally_valid(self): self.assert_valid(self.make_job())
    def test_specified_tolerance_requires_nonnegative_value_and_source(self):
        j=self.make_job(); j['feature_plan']['dimensions'][0]['tolerance']=ev('specified',0.1,source_ref='drawing:tol-1'); self.assert_valid(j)
        b=copy.deepcopy(j); b['feature_plan']['dimensions'][0]['tolerance']['value']=-0.01; self.assert_invalid(b)
        b=copy.deepcopy(j); b['feature_plan']['dimensions'][0]['tolerance']['source_ref']=None; self.assert_invalid(b)
    def test_approved_tolerance_requires_approver(self):
        j=self.make_job(); j['feature_plan']['dimensions'][0]['tolerance']=ev('approved',0.05,source_ref='project:tolerance-1',approved_by='reviewer-1'); self.assert_valid(j)
        b=copy.deepcopy(j); b['feature_plan']['dimensions'][0]['tolerance']['approved_by']=None; self.assert_invalid(b)

if __name__=='__main__': unittest.main()

class PackContractTests(unittest.TestCase):
    def test_site_pack_preserves_unresolved_release_block(self):
        text=(ROOT/'domains/site-reconstruction/rule-pack.md').read_text(encoding='utf-8')
        self.assertIn('`unresolved` is structurally valid input but SITE-03 remains BLOCK/unknown', text)

    def test_mechanical_pack_preserves_unresolved_release_block(self):
        text=(ROOT/'domains/mechanical-reconstruction/rule-pack.md').read_text(encoding='utf-8')
        self.assertIn('`unresolved` is structurally valid input but a critical dimension remains BLOCK/unknown', text)
