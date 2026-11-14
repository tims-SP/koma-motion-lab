import unittest,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-70-seam-repair'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Seam(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-70-seam-qa.json').read_text())
 def test_original_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_previous_base_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-69-clip-separation/clip-and-eye-free-underpaint.png'),self.q['oldBaseSHA256'])
 def test_reference_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-55-registration/underlay--28.png'),self.q['referenceSHA256'])
 def test_eye_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['eyeSHA256'])
 def test_clip_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-69-clip-separation/hair-clip-gold-independent.png'),self.q['clipSHA256'])
 def test_hair_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-69-clip-separation/hair-front-no-gold-candidate.png'),self.q['hairSHA256'])
 def test_new_base_sha(self):self.assertEqual(sha(D/'forehead-seam-repaired.png'),self.q['newBaseSHA256'])
 def test_mask_sha(self):self.assertEqual(sha(D/'forehead-repair-mask.png'),self.q['repairMaskSHA256'])
 def test_mask_external_rgba_exact(self):
  old=Image.open(R/'private-assets/exports/p15-69-clip-separation/clip-and-eye-free-underpaint.png').convert('RGBA').tobytes()
  new=Image.open(D/'forehead-seam-repaired.png').convert('RGBA').tobytes()
  m=Image.open(D/'forehead-repair-mask.png').convert('L').tobytes()
  self.assertEqual(sum(old[i*4:i*4+4]!=new[i*4:i*4+4] for i,a in enumerate(m) if a==0),0)
  self.assertEqual(self.q['outsideMaskChangedPixels'],0)
 def test_changes_material(self):self.assertGreater(self.q['changedRGBApixels'],10000)
 def test_three_frames(self):
  self.assertEqual([x['dx'] for x in self.q['frames']],[0,9,18])
  for f in self.q['frames']:self.assertEqual(sha(D/f['file']),f['sha256'])
 def test_three_frames_no_holes(self):self.assertEqual(self.q['transparentHolesByOffset'],{'0':0,'9':0,'18':0})
 def test_rgba_sizes(self):
  for name in ['forehead-seam-repaired.png','eye-shift-00-seam-repaired.png','eye-shift-09-seam-repaired.png','eye-shift-18-seam-repaired.png']:
   with Image.open(D/name) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_gating(self):
  self.assertFalse(self.q['fullFrontHairSemanticApproved'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_html(self):
  h=(D/'index.html').read_text()
  self.assertIn('id="shift"',h)
  self.assertIn('正式 ArtMesh 尚未通过',h)
if __name__=='__main__':unittest.main()
