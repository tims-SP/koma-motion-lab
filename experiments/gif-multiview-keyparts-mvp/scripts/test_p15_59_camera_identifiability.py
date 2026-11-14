import unittest,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-59-camera-identifiability'
class CameraIdentifiability(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-59-camera-identifiability-qa.json').read_text())
 def test_source_proxy_hash(self):
  p=R/'evidence/p15-12-camera-proxy-qa.json'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceCameraProxySHA256'])
 def test_landmark_registry_hash(self):
  p=R/'private-assets/p5-see-through/mv-candidate/landmark-qa.json'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['underlyingLandmarkRegistrySHA256'])
 def test_source_nominal_0_45_90(self):self.assertEqual(self.q['proxySourceAngles'],[0,45,90])
 def test_observation_sources_not_measured_depth(self):
  sources={x['source'] for x in self.q['sampleObservationOrigins']}
  self.assertIn('PSD_ALPHA_CONNECTED_COMPONENT',sources)
  self.assertIn('P0_GIF_ARTMESH_SOURCE_ANCHOR',sources)
 def test_proxy_modes(self):
  self.assertEqual(self.q['modelCounts'],{'three_view_orthographic_proxy':10,'two_view_linear_extrapolation':2})
 def test_far_eye_and_clip_are_extrapolated(self):
  self.assertEqual(set(self.q['linearlyExtrapolatedKeys']),{'eye.far.iris','hair.clip.center'})
 def test_gauge_symmetry(self):
  self.assertEqual([x['gaugeRotationDeg'] for x in self.q['gaugeSymmetryExperiment']],[-30,-20,0,20,30])
  self.assertTrue(all(x['maxProjectionDifferencePx']<1e-9 for x in self.q['gaugeSymmetryExperiment']))
 def test_manual_landmarks_not_independent(self):
  self.assertTrue(all(not x['independentlyDetected'] for x in self.q['landmarkDiagnostics']))
 def test_underdetermined(self):
  for key in ['cameraIntrinsicsAvailable','independentMeasuredWorldPointsAvailable','physicalDepthScaleCalibrated','independentAbsoluteCameraReferenceAvailable','absoluteYaw65Identifiable','absoluteYaw65Verified']:
   self.assertFalse(self.q[key])
 def test_model_command_not_physical_angle(self):
  self.assertEqual(self.q['relativeCommandDeg'],20)
  self.assertFalse(self.q['relativeCommandVerifiedAsPhysicalRotation'])
 def test_candidate_identity(self):
  p=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['candidateSHA256'])
 def test_artmesh_unchanged(self):
  self.assertFalse(self.q['formalArtMeshModified'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_html_assets(self):
  html=(D/'index.html').read_text()
  for file in ['canonical45.png','candidate-relative20.png','gauge-equivalence.png']:
   self.assertIn('src="'+file+'"',html)
   with Image.open(D/file) as im:self.assertGreater(im.width,0)
if __name__=='__main__':unittest.main()
