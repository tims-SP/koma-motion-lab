#!/usr/bin/env python3
"""Native-view geometry, source-hidden exposure, provenance and browser QA."""
from pathlib import Path
from PIL import Image
import hashlib,math,json,unittest
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class SourceOwnedVisibility(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.geom=json.loads((R/'evidence/p15-112-render-qa.json').read_text())
  cls.reveal=json.loads((R/'evidence/p15-112-reveal-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-112-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-112-browser-qa.json').read_text())
  cls.native=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
  cls.hidden=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
  cls.vision=json.loads((R/'evidence/p15-110-vision-qa.json').read_text())
 def test_p0_sources(self):
  self.assertEqual(self.geom['character'],'p0_character_001')
  self.assertEqual(self.geom['sourceAngles'],[60,67.5,75])
 def test_verified_source_art(self):
  self.assertEqual(self.geom['sourceVisionSHA256'],sha(R/'evidence/p15-110-vision-qa.json'))
  self.assertEqual(self.geom['sourceHiddenSHA256'],sha(R/'evidence/p15-111-source-qa.json'))
  for view,entry in self.vision['sourceImages'].items():
   self.assertEqual(self.geom['nativeSourceImageHashes'][view],sha(R/entry['path']))
 def test_keyviews(self):
  self.assertEqual(len(self.geom['methods']),3)
  for method,frames in self.geom['methods'].items():
   for angle in ('60','67.5','75'):
    self.assertEqual(frames[angle]['sha256'],self.native['methods']['companion_direct_native_keys'][angle]['sha256'])
 def test_actual_27_frames(self):
  for method,frames in self.geom['methods'].items():
   self.assertEqual(len(frames),9)
   for rec in frames.values():
    file=R/rec['path']
    self.assertEqual(rec['sha256'],sha(file))
    with Image.open(file) as image:
     self.assertEqual(image.mode,'RGBA')
     self.assertEqual(image.size,(1024,1024))
 def test_nofold_yaw_warps(self):
  for frames in self.geom['methods'].values():
   for angle,rec in frames.items():
    if 'minJacobian' in rec['diagnostics']:
     self.assertGreater(rec['diagnostics']['minJacobian'],0)
     self.assertEqual(rec['diagnostics']['negativeWarpJacobianSamples'],0)
 def test_comparable_metrics(self):
  self.assertEqual(len(self.geom['metrics']),6)
  for method,regions in self.geom['metrics'].items():
   for region,item in regions.items():
    self.assertEqual(len(item['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(v) and v>=0 for v in item['adjacentRGBMAE']))
 def test_hidden_source_model(self):
  self.assertTrue(self.geom['newMaterialArtInferred'])
  self.assertEqual(self.hidden['nativeImageCount'],6)
 def test_reveal_views_and_poses(self):
  self.assertEqual(set(self.reveal['viewRecords']),{'60','67.5','75'})
  self.assertEqual(len(self.reveal['poseLabels']),5)
 def test_zero_pose_image_exact(self):
  for view,item in self.reveal['viewRecords'].items():
   self.assertLess(item['poseMetrics']['neutral']['zeroPoseSourceRGBAMAEPixel'],0.2)
 def test_positive_new_exposure(self):
  for view,item in self.reveal['viewRecords'].items():
   for key,rec in item['poseMetrics'].items():
    if key=='neutral':continue
    self.assertGreater(rec['newlyExposedSourceOwnedPixels'],250)
    self.assertGreater(rec['donorAlphaCoveredExposedPixels'],200)
    self.assertGreater(rec['opaquePixelsWithHidden'],rec['opaquePixelsWithoutHidden'])
 def test_material_coverage_by_owner(self):
  for view,item in self.reveal['viewRecords'].items():
   for key,rec in item['poseMetrics'].items():
    if key=='neutral':continue
    self.assertEqual(rec['movingOccluder'],'bowFabric' if key.startswith('bow') else 'jewel')
    self.assertEqual(rec['exposureDonor'],'collar' if key.startswith('bow') else 'bow')
 def test_reveal_pixel_provenance(self):
  for view,item in self.reveal['viewRecords'].items():
   self.assertEqual(item['sourceSHA256'],sha(R/item['sourceImage']))
   for pose,paths in item['files'].items():
    for mode,rec in paths.items():
     self.assertEqual(rec['sha256'],sha(R/rec['path']))
     with Image.open(R/rec['path']) as image:self.assertEqual(image.size,(1024,1024))
 def test_review_files(self):
  self.assertEqual(len(self.review['renderMethods']),6)
  self.assertEqual(len(self.review['animations']),6)
  for m,frames in self.review['renderMethods'].items():
   self.assertEqual(len(frames),9)
   for angle,file in frames.items():
    self.assertTrue((P/'p15-112-visibility-vdd'/file).resolve().is_file())
 def test_review_gifs(self):
  for rec in self.review['animations'].values():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html_controls(self):
  html=(P/'p15-112-visibility-vdd/index.html').read_text()
  for identifier in ('id="method"','id="yaw"','id="frame"','id="motion"','id="sourceView"','id="pose"','id="revealOff"','id="revealOn"'):
   self.assertIn(identifier,html)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['yawChecks']),108)
  self.assertEqual(len(self.browser['revealChecks']),30)
  self.assertFalse(self.browser['errors'])
 def test_visual_gate(self):
  self.assertFalse(self.geom['artistVisualAccepted'])
  self.assertFalse(self.review['fullYawVisualAccepted'])
  self.assertFalse(self.reveal['artisticHiddenSurfaceApproval'])
if __name__=='__main__':unittest.main()
