import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-46-anchor-guides'
class AnchorGuides(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-46-anchor-guides-qa.json').read_text())
 def test_guide_hash(self):self.assertEqual(hashlib.sha256((D/'facial-geometry-guide-65.png').read_bytes()).hexdigest(),self.q['guide']['sha256'])
 def test_mask_hash(self):self.assertEqual(hashlib.sha256((D/'face-mask-narrow-65.png').read_bytes()).hexdigest(),self.q['mask']['sha256'])
 def test_dimensions(self):
  for n in ['facial-geometry-guide-65.png','face-mask-narrow-65.png']:
   with Image.open(D/n) as im:self.assertEqual(im.size,(1024,1024))
 def test_all_anchor_roles(self):self.assertEqual(set(self.q['anchors']),{'eye.near.iris','eye.far.iris','nose','mouth','face.jaw.near','face.chin','hair.clip.center'})
 def test_no_generation_or_art_mutation(self):self.assertFalse(self.q['modelInferenceAttempted'])
if __name__=='__main__':unittest.main()
