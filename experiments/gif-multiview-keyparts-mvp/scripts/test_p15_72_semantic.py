import unittest,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-72-semantic-hair'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class ModelSemantics(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-72-semantic-qa.json').read_text())
 def test_original_source(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_actual_input(self):self.assertEqual(sha(R/'private-assets/exports/p15-71-sam-semantic/input-512.png'),self.q['inputSHA256'])
 def test_model_calls(self):self.assertEqual(self.q['providerCalls'],2)
 def test_outputs_are_actual_model_files(self):
  for r in self.q['providerResults']:
   self.assertEqual(r['sha256'],sha(D/r['path']))
   with Image.open(D/r['path']) as im:self.assertEqual(im.size,(512,512))
 def test_segmentation_contaminates_eye(self):self.assertTrue(all(x['nearEyeIncluded'] for x in self.q['providerResults']))
 def test_segmentation_contaminates_cheek(self):self.assertTrue(all(x['cheekIncluded'] for x in self.q['providerResults']))
 def test_hair_present_but_not_isolated(self):self.assertTrue(all(x['hairInteriorIncluded'] for x in self.q['providerResults']))
 def test_model_returned_not_approved(self):
  self.assertTrue(self.q['modelProducedImage'])
  self.assertFalse(self.q['modelProducedUsableFrontHairAlpha'])
 def test_formal_gates(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertTrue(self.q['visualGate'].startswith('FAIL_'))
 def test_comparison_frames_reused_exactly(self):
  for dx in [0,9,18]:
   self.assertEqual(sha(D/f'baseline-eye-{dx:02d}.png'),
    sha(R/f'private-assets/exports/p15-70-seam-repair/eye-shift-{dx:02d}-seam-repaired.png'))
 def test_html_fail_statement(self):
  h=(D/'index.html').read_text()
  self.assertIn('正式视觉门禁 FAIL',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
