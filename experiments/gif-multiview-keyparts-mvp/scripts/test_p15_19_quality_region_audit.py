import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q=json.loads((R/'evidence/p15-19-quality-region-qa.json').read_text())
class QualityRegions(unittest.TestCase):
 def test_identity_and_angles(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(Q['angles'],[55,57.5,60,62.5,65])
 def test_90_regions_and_hashes(self):
  self.assertEqual(len(Q['views']),5)
  for v in Q['views']:
   self.assertEqual(len(v['rois']),6)
   for roi in v['rois']:
    self.assertEqual(len(roi['files']),3)
    for name in roi['files'].values():
     with Image.open(P/'exports/p15-19-quality-review'/name) as im:
      self.assertEqual(im.mode,'RGBA')
      self.assertEqual(im.size,(roi['radius']*2,roi['radius']*2))
 def test_stroke_changes_and_side_hair_non_effect(self):
  self.assertGreater(max(r['difference']['changedRgbPixels'] for v in Q['views'] for r in v['rois'] if r['roi']=='front_hair'),10000)
  self.assertTrue(all(r['difference']['changedRgbPixels']==0 for v in Q['views'] for r in v['rois'] if r['roi']=='side_hair'))
 def test_old_arc_fareye_clip_missing(self):
  for v in Q['views']:
   if v['yaw']>=60:
    record={r['roi']:r for r in v['rois']}
    self.assertEqual(record['far_eye']['sourceP15_10PartVisiblePixels'],0)
    self.assertEqual(record['gold_clip']['sourceP15_10PartVisiblePixels'],0)
 def test_no_false_signoff(self):
  self.assertFalse(Q['artisticAcceptance'])
  self.assertEqual(Q['independentPaintingApproved'],0)
  self.assertEqual(Q['hiddenUnderpaintApproved'],0)
 def test_source_hashes(self):
  for v in Q['views']:
   name='yaw'+str(v['yaw']).replace('.','p').replace('p0','')
   for sub,key in [('p15-17-anatomical-5frame','baseSHA256'),('p15-18-stroke-wide-5frame','wideSHA256')]:
    p=P/sub/(name+'.png')
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),v[key])
if __name__=='__main__':unittest.main()
