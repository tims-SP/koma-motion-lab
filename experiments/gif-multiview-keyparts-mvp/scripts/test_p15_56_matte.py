import hashlib,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-56-edge-matting'
class MatteQA(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-56-alpha-matte-qa.json').read_text())
 def test_source_clip_unchanged(self):
  p=R/'private-assets/exports/p15-55-registration/clip--28.png';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceClipSHA256'])
 def test_underlay_unchanged(self):
  p=R/'private-assets/exports/p15-55-registration/underlay--28.png';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['underlaySHA256'])
 def test_rgb_preserved(self):
  a=Image.open(R/'private-assets/exports/p15-55-registration/clip--28.png').convert('RGBA')
  b=Image.open(D/'clip-erode-2.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox())
 def test_alpha_monotonic(self):
  src=Image.open(R/'private-assets/exports/p15-55-registration/clip--28.png').getchannel('A')
  a1=Image.open(D/'clip-erode-1.png').getchannel('A');a2=Image.open(D/'clip-erode-2.png').getchannel('A');a3=Image.open(D/'clip-erode-3.png').getchannel('A')
  self.assertIsNone(ImageChops.subtract(a1,src).getbbox())
  self.assertIsNone(ImageChops.subtract(a2,a1).getbbox())
  self.assertIsNone(ImageChops.subtract(a3,a2).getbbox())
 def test_selected_hash(self):
  p=D/'candidate-erode-2.png';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['selectedCandidateSHA256'])
 def test_selected_clip_bbox(self):
  im=Image.open(D/'clip-erode-2.png');self.assertEqual(list(im.getchannel('A').getbbox()),self.q['selectedClipBBox'])
 def test_all_variants_present(self):
  for n in [1,2,3]:self.assertTrue((D/f'candidate-erode-{n}.png').exists())
 def test_three_backgrounds(self):
  for n in ['light','blue','pink']:
   with Image.open(D/f'preview-2-{n}.png') as im:self.assertEqual(im.size,(1024,1024))
 def test_rgba_composite(self):
  base=Image.open(R/'private-assets/exports/p15-55-registration/underlay--28.png').convert('RGBA')
  clip=Image.open(D/'clip-erode-2.png').convert('RGBA');out=Image.open(D/'candidate-erode-2.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(Image.alpha_composite(base,clip),out).getbbox())
 def test_not_formally_accepted(self):
  self.assertFalse(self.q['formalArtMeshChanged']);self.assertFalse(self.q['absoluteYaw65Verified']);self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_review_assets(self):
  h=(D/'index.html').read_text()
  for n in ['crop-erode-1.png','crop-erode-2.png','crop-erode-3.png','preview-2-light.png','preview-2-blue.png','preview-2-pink.png']:self.assertIn(n,h)
if __name__=='__main__':unittest.main()
