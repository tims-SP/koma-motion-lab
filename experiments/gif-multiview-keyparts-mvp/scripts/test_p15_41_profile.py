import unittest,json,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'private-assets/exports/p15-41-profile-candidate'
QA=json.loads((ROOT/'evidence/p15-41-profile-qa.json').read_text())
class Profile(unittest.TestCase):
 def test_registry_identity(self):
  self.assertEqual(QA['characterId'],'p0_character_001');self.assertEqual(QA['layerCount'],13)
 def test_all_rgba(self):
  for role in QA['roles']:
   with Image.open(OUT/'layers'/(role+'.png')) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_clip_exists(self):
  a=np.asarray(Image.open(OUT/'layers/hair.clip.cross_gold.png'))[:,:,3];self.assertGreater(int((a>16).sum()),100)
 def test_source_hash(self):
  p=ROOT/'private-assets/p15-independent-candidates/yaw065-artmesh/qa.json'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),QA['sourceRegistrySHA256'])
 def test_candidate_digest(self):
  p=OUT/'candidate.png';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),QA['candidateSHA256'])
 def test_html(self):self.assertTrue((OUT/'index.html').exists())
 def test_art_gate(self):
  self.assertFalse(QA['yaw65PoseApproved']);self.assertFalse(QA['visualArtApproved']);self.assertFalse(QA['heroSourceApproved'])
if __name__=='__main__':unittest.main()
