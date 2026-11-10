import json,hashlib,unittest
from pathlib import Path
R=Path(__file__).resolve().parent.parent
P=R/'private-assets/exports/p15-18-mode-comparison'
Q=json.loads((P/'qa.json').read_text())
class ModeCompare(unittest.TestCase):
 def test_three_modes_and_five_frames(self):
  self.assertEqual(set(Q['modes']),{'anatomy','anatomy-strokes','stroke-wide'})
  for mode in Q['modes'].values():self.assertEqual(len(mode['frames']),5)
 def test_stroke_wide_keeps_continuity(self):
  p=Q['modes']['stroke-wide']['pairs']
  self.assertEqual(len(p),4);self.assertTrue(all(x>=.95 for x in p))
 def test_anatomy_strokes_is_noop(self):
  self.assertEqual(Q['modes']['anatomy']['pairs'],Q['modes']['anatomy-strokes']['pairs'])
  self.assertEqual(Q['modes']['anatomy-strokes']['strokeAnchorsUsed'],9)
 def test_stroke_wide_is_distinct(self):
  self.assertEqual(Q['modes']['stroke-wide']['strokeAnchorsUsed'],12)
  self.assertNotEqual(Q['modes']['stroke-wide']['frames'][2]['sha256'],Q['modes']['anatomy']['frames'][2]['sha256'])
 def test_no_artistic_promotion(self):
  self.assertFalse(Q['artisticAcceptance'])
  self.assertEqual(Q['approvedIndependentPaintings'],0)
  self.assertEqual(Q['approvedHiddenUnderpainting'],0)
 def test_all_rasters_integrity(self):
  for m in Q['modes'].values():
   for f in m['frames']:
    p=P/f['path'];self.assertTrue(p.is_file())
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['sha256'])
if __name__=='__main__':unittest.main()
