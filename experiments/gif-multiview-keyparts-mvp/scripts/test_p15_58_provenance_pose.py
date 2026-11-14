import json,hashlib,unittest,zipfile
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-58-provenance-pose'
class ProvenancePose(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-58-provenance-pose-qa.json').read_text())
 def test_canonical_image_hash(self):
  p=R/'private-assets/p2-views/whole/yaw045.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['canonical45']['sha256'])
 def test_all_copies_identical(self):
  d=self.q['canonical45']['verifiedIdenticalCopies']
  self.assertEqual(len(d),5)
  self.assertEqual(set(d.values()),{self.q['canonical45']['sha256']})
 def test_archive_entry_matches(self):
  x=self.q['canonical45']['verifiedArchiveEntry']
  with zipfile.ZipFile(R/x['zip']) as z:self.assertEqual(hashlib.sha256(z.read(x['entry'])).hexdigest(),x['sha256'])
 def test_old_recovery_pixel_parity(self):
  self.assertTrue(self.q['canonical45']['recoveryPixelParityClaimMatches'])
 def test_hero_provenance_unresolved(self):
  self.assertFalse(self.q['canonical45']['approvedHeroBytesValidated'])
  self.assertIn('NOT_PROVEN',self.q['canonical45']['heroTo45ProvenanceLevel'])
 def test_raw_candidate_hash_matches(self):
  raw=R/'private-assets/exports/p15-51-qwen-angle-plus20deg.webp'
  self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),self.q['candidate']['rawModelOutputSHA256'])
 def test_matting_candidate_hash_matches(self):
  candidate=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
  self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(),self.q['candidate']['selectedP1556SHA256'])
 def test_relative_not_absolute(self):
  self.assertEqual(self.q['candidate']['cameraCommandRelativeDegrees'],20)
  self.assertIsNone(self.q['candidate']['absoluteYawDegrees'])
  self.assertFalse(self.q['candidate']['absoluteYawVerified'])
 def test_feature_coverage(self):
  self.assertEqual(len(self.q['features']),6)
 def test_historical90_not_calibration(self):
  self.assertIn('not camera calibration',self.q['historic90']['role'])
 def test_no_formal_artmesh(self):
  self.assertFalse(self.q['formalArtMeshModified'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_visual_review_files(self):
  h=(D/'index.html').read_text()
  for n in ['canonical45.png','relative-plus20-candidate.png','historical90.png','canonical45-face.png','relative-plus20-candidate-face.png','relative-plus20-candidate-clip.png']:
   self.assertTrue((D/n).exists());self.assertIn('src="'+n+'"',h)
if __name__=='__main__':unittest.main()
