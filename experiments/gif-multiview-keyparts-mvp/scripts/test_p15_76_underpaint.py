import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-76-seam-source'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1576(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-76-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceHashes']['source'])
 def test_base_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-70-seam-repair/forehead-seam-repaired.png'),self.q['sourceHashes']['base'])
 def test_hair_source(self):self.assertEqual(sha(R/'private-assets/exports/p15-74-bangs-repair/hair.front.alpha-dedup.png'),self.q['sourceHashes']['hair0'])
 def test_clip_source(self):self.assertEqual(sha(R/'private-assets/exports/p15-69-clip-separation/hair-clip-gold-independent.png'),self.q['sourceHashes']['clip'])
 def test_eye_source(self):self.assertEqual(sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['sourceHashes']['eye'])
 def test_guard_hash(self):self.assertEqual(sha(D/'hidden-skin-local-guard.png'),self.q['guardSHA256'])
 def test_underpaint_candidate(self):self.assertEqual(sha(D/'hidden-skin-clean-candidate.png'),self.q['candidateUnderpaintSHA256'])
 def test_guard_geometry(self):
  m=Image.open(D/'hidden-skin-local-guard.png').convert('L')
  self.assertEqual(list(m.getbbox()),self.q['guardBBox'])
  self.assertEqual(sum(x>0 for x in m.getdata()),self.q['guardNonzeroPixels'])
 def test_zero_pose(self):
  src=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  new=Image.open(D/'eye-shift-00.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(src,new).getbbox())
  self.assertTrue(self.q['zeroPosePixelExact'])
 def test_frame_hashes(self):
  self.assertEqual([x['dx'] for x in self.q['frameHashes']],[0,9,18])
  for f in self.q['frameHashes']:
   self.assertEqual(sha(D/f"eye-shift-{f['dx']:02d}.png"),f['frameSHA256'])
   self.assertEqual(sha(D/f"hidden-skin-{f['dx']:02d}.png"),f['underpaintSHA256'])
 def test_mask_external_pixels_intact(self):
  base=Image.open(R/'private-assets/exports/p15-70-seam-repair/forehead-seam-repaired.png').convert('RGBA').tobytes()
  mask=Image.open(D/'hidden-skin-local-guard.png').convert('L').tobytes()
  for dx in (0,9,18):
   new=Image.open(D/f'hidden-skin-{dx:02d}.png').convert('RGBA').tobytes()
   self.assertFalse(any(base[i*4:i*4+4]!=new[i*4:i*4+4] for i,v in enumerate(mask) if v==0))
 def test_no_holes(self):self.assertEqual(self.q['holeCounts'],{'0':0,'9':0,'18':0})
 def test_changed(self):self.assertGreater(self.q['changedFullFramePixels18'],100)
 def test_rgba_dimensions(self):
  for dx in (0,9,18):
   with Image.open(D/f'eye-shift-{dx:02d}.png') as x:self.assertEqual((x.mode,x.size),('RGBA',(1024,1024)))
 def test_formal_assets_unchanged(self):
  self.assertFalse(self.q['fullSemanticHairLayerAccepted'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_review_admits_failure(self):
  h=(D/'index.html').read_text()
  self.assertIn('正式 ArtMesh 视觉门禁 FAIL',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
