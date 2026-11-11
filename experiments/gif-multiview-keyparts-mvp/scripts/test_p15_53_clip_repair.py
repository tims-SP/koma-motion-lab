import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-53-gold-clip-repair'
class ClipRepair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-53-gold-clip-qa.json').read_text())
 def test_source_sha(self):
  p=R/self.q['sourceRegisteredClip']['path']
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceRegisteredClip']['sha256'])
 def test_candidate_base_sha(self):
  p=R/self.q['sourceTransparentCandidate']['path']
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceTransparentCandidate']['sha256'])
 def test_clip_is_separate_rgba(self):
  with Image.open(D/'hair.clip.cross_gold.png') as x:
   self.assertEqual(x.size,(1024,1024));self.assertEqual(x.mode,'RGBA')
   self.assertEqual(x.getchannel('A').getbbox(),tuple(self.q['independentClip']['bbox']))
 def test_clip_sha(self):
  p=D/'hair.clip.cross_gold.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['independentClip']['sha256'])
 def test_composite_sha(self):
  p=D/'candidate-gold-cross-restored.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['composite']['sha256'])
 def test_compositing(self):
  b=Image.open(D/'underlay-repaired.png').convert('RGBA')
  clip=Image.open(D/'hair.clip.cross_gold.png').convert('RGBA')
  out=Image.open(D/'candidate-gold-cross-restored.png').convert('RGBA')
  from PIL import ImageChops
  self.assertIsNone(ImageChops.difference(Image.alpha_composite(b,clip),out).getbbox())
 def test_background_unchanged_outside_repair(self):
  src=Image.open(R/self.q['sourceTransparentCandidate']['path']).convert('RGBA')
  out=Image.open(D/'underlay-repaired.png').convert('RGBA')
  # Pixel changes restricted to old clip cleanup x744..787/y276..387
  for rect in [(0,0,744,1024),(800,0,1024,1024),(744,0,800,276),(744,388,800,1024)]:
   from PIL import ImageChops
   self.assertIsNone(ImageChops.difference(src.crop(rect),out.crop(rect)).getbbox())
 def test_source_assets_remain_unchanged(self):self.assertFalse(self.q['verification']['artMeshModified'])
 def test_formal_perspective_not_certified(self):self.assertFalse(self.q['verification']['absoluteYaw65Verified']);self.assertFalse(self.q['verification']['formalKeyframeAccepted'])
 def test_clip_cross_has_two_arms(self):self.assertTrue(self.q['verification']['bothCrossingArmsReused'])
 def test_cleanup_changed_small_region(self):
  self.assertGreater(self.q['underlayRepaired']['goldPixelsReplaced'],0)
  self.assertGreater(self.q['underlayRepaired']['detachedTuftAlphaPixelsRemoved'],0)
 def test_html_contains_before_after(self):
  h=(D/'index.html').read_text()
  for n in ['before-clip-zoom.png','after-clip-zoom.png','hair.clip.cross_gold.png','candidate-gold-cross-restored.png']:
   self.assertIn('src="'+n+'"',h)
if __name__=='__main__':unittest.main()
