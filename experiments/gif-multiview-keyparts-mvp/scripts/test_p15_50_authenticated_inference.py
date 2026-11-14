import contextlib, importlib.util, io, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

S=Path(__file__).parent/'p15_47_controlnet_inference.py'
spec=importlib.util.spec_from_file_location('p15_50_under_test', S)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FakeResponse:
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return b'{"ok":true}'

class AuthIntegration(unittest.TestCase):
    def test_bearer_header_on_origin_only(self):
        def capture(request,timeout):
            self.assertEqual(request.get_header('Authorization'),'Bearer hf_synthetic_test_only')
            self.assertEqual(request.get_header('Content-type'),'application/json')
            return FakeResponse()
        with patch.dict(os.environ,{'HF_TOKEN':'hf_synthetic_test_only'}):
            with patch.object(mod.urllib.request,'urlopen',side_effect=capture):
                self.assertEqual(mod.request(mod.SPACE+'/gradio_api/call/generate',obj={'data':[]}),b'{"ok":true}')

    def test_token_never_forwarded_to_other_hostname(self):
        def capture(request,timeout):
            self.assertIsNone(request.get_header('Authorization'))
            return FakeResponse()
        with patch.dict(os.environ,{'HF_TOKEN':'hf_synthetic_test_only'}):
            with patch.object(mod.urllib.request,'urlopen',side_effect=capture):
                mod.request('https://example.org/asset.png')

    def test_no_network_when_missing_token(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            with patch.object(mod,'R',folder),patch.dict(os.environ,{},clear=True):
                (folder/'evidence').mkdir()
                with patch('sys.argv',['script','--evidence-stage','p15-50']):
                    with patch.object(mod.urllib.request,'urlopen',side_effect=AssertionError('unexpected network')):
                        with contextlib.redirect_stdout(io.StringIO()) as out:
                            self.assertEqual(mod.main(),3)
                self.assertIn('BLOCKED_HF_TOKEN_NOT_CONFIGURED',out.getvalue())
                evidence=json.loads((folder/'evidence/p15-50-inference-qa.json').read_text())
                self.assertFalse(evidence['newImageGenerated'])
                self.assertNotIn('tokenValue',evidence)
                self.assertFalse(evidence['artMeshModified'])

    def test_no_credentials_in_persistent_evidence(self):
        doc=json.loads((mod.R/'evidence/p15-50-inference-qa.json').read_text())
        self.assertEqual(doc['status'],'BLOCKED_HF_TOKEN_NOT_CONFIGURED')
        self.assertFalse(doc['tokenPresent'])
        self.assertNotIn('hf_',json.dumps(doc).replace('HF_TOKEN',''))
if __name__=='__main__':unittest.main()
