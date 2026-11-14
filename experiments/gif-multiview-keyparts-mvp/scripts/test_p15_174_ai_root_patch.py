import importlib.util,unittest,numpy as np
from pathlib import Path
p=Path(__file__).with_name('p15_174_ai_root_patch.py')
s=importlib.util.spec_from_file_location('p15_174_ai_root_patch',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class AIRootPatchTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.run(save=False)
 def test_only_the_source_owned_anchor_is_changed(self):
  src,out,info=m.apply()
  self.assertTrue(np.array_equal(src[...,3],out[...,3]))
  self.assertTrue(info['outsidePatchPixelExact'])
  self.assertLessEqual(info['changedPixels'],196)
  self.assertEqual(info['bbox'],[251,70,264,83])
 def test_character_keyview_source_is_preserved(self):
  src=m.keyframes()[112.5]
  self.assertEqual(self.q['diagnostics']['sourceSha256'],m.apply()[2]['sourceSha256'])
  self.assertEqual(src.shape,(443,443,4))
 def test_model_edit_is_used_only_as_patch_donor(self):
  self.assertIn('Only 14x14 patch',self.q['modelOutputScope'])
  self.assertTrue((m.ASSET/'flux-kontextual-edit.png').exists())
  self.assertTrue((m.ASSET/'source-crop.jpg').exists())
  self.assertEqual(self.q['diagnostics']['patchSize'],[14,14])
 def test_visual_gate_remains_separate(self):
  self.assertTrue(self.q['gate']['candidateRendered'])
  self.assertFalse(self.q['gate']['rootAttachmentVisuallyAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['canonicalRendererUpdated'])
if __name__=='__main__':unittest.main()
