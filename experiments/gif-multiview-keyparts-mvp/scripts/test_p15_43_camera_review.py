import unittest,json,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
QA=json.loads((ROOT/'evidence/p15-43-camera-pose-qa.json').read_text())
D=ROOT/'private-assets/exports/p15-43-camera-pose-review'
class Review(unittest.TestCase):
 def test_identity(self):self.assertEqual(QA['characterId'],'p0_character_001')
 def test_camera_anchors(self):self.assertEqual(len(QA['cameraAnchors']),6)
 def test_image_sources(self):self.assertEqual(len(QA['sourceImages']),5)
 def test_hashes(self):
  for row in QA['sourceImages']:
   src=ROOT/'private-assets'/row['source'];self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),row['sha256'])
 def test_canvases(self):
  for f in ('registered-65.png','pose-locked-candidate.png','yaw65-anchor-overlay.png'):
   with Image.open(D/f) as img:self.assertEqual(img.size,(1024,1024))
 def test_pose_gate(self):self.assertFalse(QA['generatedPoseAccepted']);self.assertFalse(QA['new65KeyframeCommitted'])
 def test_art_gate(self):self.assertFalse(QA['approvedHeroSHA256Verified']);self.assertFalse(QA['artisticAcceptance'])
 def test_html(self):self.assertIn('KOMA_P15_43',(D/'index.html').read_text())
if __name__=='__main__':unittest.main()
