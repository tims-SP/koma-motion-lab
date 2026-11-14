#!/usr/bin/env python3
"""Evidence tests for 52.5-to-75 P0 semantic-anchor correspondence study."""
from pathlib import Path
from PIL import Image
import hashlib,json,math,unittest
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-98-vdd-review'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1598(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((R/'evidence/p15-98-anchor-vdd-qa.json').read_text())
  cls.g=json.loads((R/'evidence/p15-98-landmarks.json').read_text())
  cls.b=json.loads((R/'evidence/p15-98-browser-qa.json').read_text())
  cls.prior=json.loads((R/'evidence/p15-97-multiview-motion-qa.json').read_text())
 def test_correspondence_semantics(self):
  self.assertEqual(len(self.g['correspondenceRoles']),15)
  self.assertEqual(set(self.g['viewLandmarks']),{'52p5','60','75'})
  self.assertFalse(self.g['geometryMeasured'])
 def test_landmarks_inside_canvas(self):
  names=self.g['correspondenceRoles']
  for view,positions in self.g['viewLandmarks'].items():
   self.assertTrue(all(k in positions for k in names))
   for point in positions.values():
    self.assertEqual(len(point),2)
    self.assertTrue(all(0<=v<=1024 for v in point))
 def test_original_source_hashes(self):
  for view,q in self.prior['views'].items():
   p=P/'p15-97-multiview-motion'/f'yaw{view}-frame-06.png'
   self.assertEqual(self.q['sourceHashes'][view],sha(p))
   self.assertEqual(q['frames']['6']['sha256'],sha(p))
 def test_all_variant_files(self):
  self.assertEqual(len(self.q['methodFrames']),5)
  self.assertEqual(len(self.q['anglesDegrees']),9)
  for method,angles in self.q['methodFrames'].items():
   self.assertEqual(len(angles),9)
   for info in angles.values():
    path=R/info['relativePath']
    self.assertEqual(info['sha256'],sha(path))
    with Image.open(path) as im:
     self.assertEqual(im.size,(1024,1024))
     self.assertEqual(im.mode,'RGBA')
 def test_keyframe_pixel_exact(self):
  for method,frames in self.q['methodFrames'].items():
   for angle,view in [('52.5','52p5'),('60','60'),('75','75')]:
    self.assertEqual(frames[angle]['sha256'],self.q['sourceHashes'][view])
 def test_anchor_topology(self):
  n=0
  for item in self.q['landmarkQA'].values():
   if 'sourceA' not in item:continue
   n+=1
   for key in ('sourceA','sourceB'):
    diag=item[key]
    self.assertEqual(diag['negativeJacobianFractionInFaceROI'],0)
    self.assertGreater(diag['minJacobianFaceROI'],0)
  self.assertEqual(n,6)
 def test_quantitative_metrics(self):
  for method,info in self.q['methodMetrics'].items():
   self.assertEqual(len(info['faceAdjacentMAE']),8)
   self.assertTrue(all(math.isfinite(v) and v>=0 for v in info['faceAdjacentMAE']))
   self.assertTrue(0 < info['keyview60BoundaryRatio'] < 100)
 def test_review_animations(self):
  self.assertEqual(len(self.q['animated']),5)
  for m,info in self.q['animated'].items():
   self.assertEqual(info['sha256'],sha(R/info['relativePath']))
 def test_html(self):
  s=(D/'index.html').read_text()
  for id in ('id="method"','id="yaw"','id="loop"','id="current"'):
   self.assertIn(id,s)
 def test_browser(self):
  self.assertEqual(self.b['status'],'PASS')
  self.assertEqual(len(self.b['checks']),90)
  self.assertFalse(self.b['errors'])
 def test_visual_gate(self):
  self.assertFalse(self.q['continuousYawVisualAccepted'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
if __name__=='__main__':unittest.main()
