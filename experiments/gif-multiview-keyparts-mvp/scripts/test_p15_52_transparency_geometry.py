import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-52-transparency-geometry'
class P1552QA(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-52-transparency-geometry-qa.json').read_text())
 def test_source_hash(self):
  p=R/self.q['sourceAngleLoRA']['sourcePath']
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceAngleLoRA']['sourceSHA256'])
 def test_rgba_hash(self):
  p=R/self.q['output']['path']
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['output']['sha256'])
 def test_rgba_and_dimensions(self):
  with Image.open(D/'camera-plus20-transparent.png') as im:
   self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(1024,1024))
 def test_black_exterior_and_ahoge_interior_removed(self):
  with Image.open(D/'camera-plus20-transparent.png') as im:
   a=im.getchannel('A')
   for xy in [(0,0),(520,80),(530,90),(1023,0)]:
    self.assertEqual(a.getpixel(xy),0)
   self.assertEqual(a.getpixel((590,430)),255)
 def test_alpha_counts_reconcile(self):
  counts=self.q['blackKey']
  self.assertEqual(sum(counts[k] for k in ['opaquePixels','fullyTransparentPixels','partialAlphaPixels']),1024**2)
  self.assertGreater(counts['fullyTransparentPixels'],500000)
 def test_geometry_not_overclaimed(self):
  self.assertFalse(self.q['cameraProxy']['absoluteYaw65Verified'])
  self.assertTrue(self.q['cameraProxy']['anchorCoordinatesAreExpectedNotMeasured'])
 def test_hair_clip_still_fails(self):
  self.assertIn('FAIL',self.q['visualFindings']['goldCrossHairClip'])
 def test_no_artmesh_mutation(self):
  self.assertFalse(self.q['formalKeyframeAccepted']);self.assertFalse(self.q['artMeshModified'])
 def test_review_content(self):
  h=(D/'index.html').read_text()
  for name in ['source45.png','registered65.png','camera-plus20-transparent.png','candidate-anchor-overlay.png','preview-light.png','preview-blue.png','preview-pink.png','silhouette-alpha.png']:
   self.assertTrue((D/name).exists());self.assertIn('src="'+name+'"',h)
if __name__=='__main__':unittest.main()
