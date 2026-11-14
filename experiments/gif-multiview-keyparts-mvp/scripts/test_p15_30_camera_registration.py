import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-30-tracked-qa.json').read_text())
O=P/'exports/p15-30-tracked-review'
class TrackedArtmesh(unittest.TestCase):
 def test_five_real_anchor_views(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(Q['angles'],[55.,57.5,60.,62.5,65.])
  self.assertEqual(len(Q['frames']),5)
 def test_clip_registration_improves(self):
  for frame in Q['frames']:
   self.assertGreater(frame['clipCentroidErrorBefore'],12)
   self.assertLess(frame['clipCentroidErrorAfter'],.05)
   self.assertLess(frame['clipCentroidErrorAfter'],frame['clipCentroidErrorBefore']*.005)
 def test_iris_relative_motion_not_centroid_equating(self):
  for frame in Q['frames']:
   self.assertLess(frame['eyeRelativeMotionErrorPx'],.03)
   self.assertGreater(frame['eyeSourceCentroid'][1],430)
   self.assertNotEqual(frame['eyeSourceCentroid'][1],frame['anchorEye'][1])
 def test_source_alpha_preservation(self):
  for frame in Q['frames']:
   self.assertGreater(frame['eyeRetainedAlphaFraction'],.98)
   self.assertGreater(frame['clipRetainedAlphaFraction'],.98)
 def test_all_png_sha_and_dimensions(self):
  for frame in Q['frames']:
   yaw=frame['yaw'];slug='yaw'+(str(int(yaw)) if yaw%1==0 else str(yaw).replace('.','p'))
   self.assertEqual(len(frame['images']),6)
   for n,digest in frame['images'].items():
    file=P/'p15-30-camera-tracked'/slug/(n+'.png')
    self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),digest)
    with Image.open(file) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_no_false_3d_or_art_promotion(self):
  self.assertFalse(Q['formalArtAccepted'])
  self.assertFalse(Q['originalIndependentPaint'])
  self.assertFalse(Q['productionVddModified'])
 def test_intermediate_frames_diagnostic_only(self):
  review=json.loads((O/'qa.json').read_text())
  self.assertEqual(len(review['timeline']),9)
  self.assertEqual(sum(x['mode']=='diagnostic-linear-full-frame' for x in review['timeline']),4)
  self.assertFalse(review['intermediateFramesAreTrueVdd'])
  for f in review['timeline']:
   with Image.open(O/f['src']) as im:self.assertEqual(im.size,(1024,1024))
 def test_frame_alpha_iou_reasonable(self):
  for f in Q['frames']:
   self.assertGreater(f['wholeFrameAlphaIoUToP15_21'],.995)
   self.assertLess(f['wholeFrameAlphaIoUToP15_21'],1)
 def test_archive_integrity(self):
  with zipfile.ZipFile(P/'exports/p15-30-tracked-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertIn('index.html',z.namelist())
   self.assertGreaterEqual(len(z.namelist()),41)
if __name__=='__main__':unittest.main()
