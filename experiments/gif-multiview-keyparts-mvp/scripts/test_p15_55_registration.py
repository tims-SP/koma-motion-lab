import hashlib,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-55-registration'
class ClipRegister(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-55-registration-qa.json').read_text())
 def test_source_hash(self):
  p=R/'private-assets/exports/p15-52-transparency-geometry/camera-plus20-transparent.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceCandidateSHA256'])
 def test_source_clip_hash(self):
  p=R/'private-assets/exports/p15-53-gold-clip-repair/hair.clip.cross_gold.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceIndependentClipSHA256'])
 def test_selected_candidate_hash(self):
  p=D/'candidate--28.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['selectedCandidateSHA256'])
 def test_separate_clip_layer(self):
  with Image.open(D/'clip--28.png') as im:
   self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(1024,1024))
   self.assertEqual(list(im.getchannel('A').getbbox()),self.q['selectedClipBBox'])
 def test_rgba_composite_determinism(self):
  under=Image.open(D/'underlay--28.png').convert('RGBA')
  clip=Image.open(D/'clip--28.png').convert('RGBA')
  candidate=Image.open(D/'candidate--28.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(Image.alpha_composite(under,clip),candidate).getbbox())
 def test_clip_moves_toward_hair(self):
  self.assertLess(self.q['variants']['-28']['clip_bbox'][2],self.q['variants']['-22']['clip_bbox'][2])
  self.assertEqual(self.q['selectedOffsetFromP1553Px'],-28)
 def test_damaged_roi_only(self):
  original=Image.open(R/'private-assets/exports/p15-52-transparency-geometry/camera-plus20-transparent.png').convert('RGBA')
  corrected=Image.open(D/'underlay--28.png').convert('RGBA')
  for box in [(0,0,723,1024),(814,0,1024,1024),(723,0,814,265),(723,406,814,1024)]:
   self.assertIsNone(ImageChops.difference(original.crop(box),corrected.crop(box)).getbbox())
 def test_visual_gates_unpassed(self):
  self.assertFalse(self.q['formalArtMeshChanged'])
  self.assertFalse(self.q['poseAbsolute65Verified'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['visualIdentityApproved'])
 def test_proxy_not_used_as_calibration(self):
  self.assertIn('NOT_CALIBRATED',self.q['proxyComparisonStatus'])
 def test_three_backgrounds(self):
  for suffix in ['light','blue','pink']:
   with Image.open(D/f'preview--28-{suffix}.png') as im:self.assertEqual(im.size,(1024,1024))
 def test_html_all_assets(self):
  html=(D/'index.html').read_text()
  for name in ['crop-former.png','crop--22.png','crop--28.png','clip--28.png','underlay--28.png','candidate--28.png','preview--28-light.png']:
   self.assertIn('src="'+name+'"',html)
if __name__=='__main__':unittest.main()
