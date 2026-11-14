import unittest,json,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'private-assets/exports/p15-42-65-keyart-review'
QA=json.loads((ROOT/'evidence/p15-42-source-and-pose-qa.json').read_text())
class Review(unittest.TestCase):
 def test_character(self):self.assertEqual(QA['characterId'],'p0_character_001')
 def test_source_count(self):self.assertEqual(len(QA['frames']),7)
 def test_generated_count(self):self.assertEqual(QA['newModelPaintings'],3)
 def test_source_provenance_sha(self):
  for row in QA['frames']:
   p=ROOT/row['sourcePath'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'])
 def test_source_canvas(self):
  for row in QA['frames']:
   with Image.open(OUT/row['name']) as im:self.assertEqual(im.size,(1024,1024))
 def test_pose_gate(self):
  self.assertFalse(QA['newKeyframeAdmitted']);self.assertTrue(all(not x['requested65PoseAccepted'] for x in QA['observations']))
 def test_html_ready(self):self.assertIn('KOMA_P15_42',(OUT/'index.html').read_text())
 def test_original_65_retained(self):
  p=ROOT/'private-assets/p15-38-p0-registered-arc/yaw65/composite.png'
  f=next(x for x in QA['frames'] if x['name']=='source-65.png')
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['sha256'])
if __name__=='__main__':unittest.main()
