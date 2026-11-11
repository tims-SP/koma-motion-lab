"""P15-34 image-grounded feature, constrained mesh and Chromium QA."""
import json,hashlib,unittest,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
import p15_34_ink_landmarks as source
import p15_34_ink_mesh_vdd as mesh

class P15_34_SemanticInk(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ink=json.loads(source.QA.read_text())
  cls.vdd=json.loads(mesh.QA.read_text())
  cls.browser=json.loads((source.R/"evidence/p15-34-browser-qa.json").read_text())
  cls.review=json.loads((source.P/"exports/p15-34-source-ink-mesh-review/qa.json").read_text())

 def test_source_identity_and_five_observations(self):
  self.assertEqual(self.ink["characterId"],"p0_character_001")
  self.assertEqual(len(self.ink["frames"]),5)
  self.assertEqual(self.ink["source45P0SHA256"],
                   source.sha(source.P/"p2-views/whole/yaw045.png"))
  self.assertEqual(self.vdd["sourceFeatureEvidenceSHA256"],source.sha(source.QA))

 def test_named_original_painted_ink_samples(self):
  counts={"eye.far":3,"hair.clip.cross_gold":5,"hair.side":3}
  for f in self.ink["frames"]:
   for role,rec in f["features"].items():
    self.assertEqual(len(rec["featureNames"]),counts[role])
    self.assertEqual(len(rec["points443"]),counts[role])
    rgba=source.read(source.P/rec["sourceRGBA"])
    self.assertEqual(source.sha(source.P/rec["sourceRGBA"]),rec["sourceSHA256"])
    for x,y in rec["points443"][1:]:
     px,py=int(round(x)),int(round(y))
     alpha=rgba[max(0,py-3):min(443,py+4),max(0,px-3):min(443,px+4),3]
     self.assertGreater(int(alpha.max()),20,(role,f["yaw"],(x,y)))
    self.assertFalse(rec["artistApproved"])
    self.assertEqual(source.sha(source.P/rec["annotationPath"]),rec["annotationSHA256"])

 def test_named_role_path_correspondence(self):
  for role in mesh.ROLES:
   names=[f["features"][role]["featureNames"] for f in self.ink["frames"]]
   self.assertTrue(all(x==names[0] for x in names))
   self.assertEqual(len(names[0]),{"eye.far":3,"hair.clip.cross_gold":5,"hair.side":3}[role])
  self.assertEqual(len(self.vdd["angles"]),9)

 def test_reference_keyframes_remain_byte_exact(self):
  self.assertEqual(self.vdd["keyframes"],5)
  for f in self.vdd["frames"]:
   if f["kind"]!="exact-source-keyframe":continue
   folder=source.slug(f["yaw"])
   self.assertEqual((mesh.OUT/folder/"composite.png").read_bytes(),
                    (mesh.REF/folder/"composite.png").read_bytes())
   for role in mesh.ROLES:
    self.assertEqual((mesh.OUT/folder/(role+".png")).read_bytes(),
                     (mesh.REF/folder/(role+".png")).read_bytes())

 def test_role_mesh_quality_and_source_provenance(self):
  mids=[f for f in self.vdd["frames"] if f["kind"]=="ink-observed-constrained-mesh"]
  self.assertEqual(len(mids),4)
  self.assertEqual(self.vdd["triangleFlips"],0)
  self.assertGreater(self.vdd["minimumTriangleAreaRatio"],.28)
  self.assertLess(self.vdd["maximumTrackingResidualPx"],1.8)
  for f in mids:
   self.assertEqual(f["roleCount"],13)
   self.assertGreater(f["changedCompositePixelsVsP15_33"],100)
   for role,d in f["meshDiagnostics"].items():
    self.assertEqual(len(d["featureNames"]),d["featureCount"])
    self.assertFalse(d["artistApproved"])
    for side in ("left","right"):
     self.assertEqual(d[side]["triangleFlips"],0)
     self.assertGreater(d[side]["minAreaRatio"],.28)
     self.assertLess(d[side]["maxConstraintResidualPx"],1.8)
    self.assertEqual(mesh.sha(mesh.OUT/source.slug(f["yaw"])/(role+".png")),d["sha256"])

 def test_other_ten_mesh_roles_identical(self):
  for f in self.vdd["frames"]:
   if f["kind"]!="ink-observed-constrained-mesh":continue
   angle=source.slug(f["yaw"])
   for part in next(v["parts"] for v in json.loads(mesh.BASE.read_text())["frames"]
                    if v["yaw"]==f["interval"][0]):
    role=part["role"]
    if role in mesh.ROLES:continue
    self.assertEqual((mesh.OUT/angle/(role+".png")).read_bytes(),
                     (mesh.REF/angle/(role+".png")).read_bytes())

 def test_review_and_chromium(self):
  self.assertEqual(len(self.review["frames"]),9)
  self.assertEqual(self.browser["status"],"NINE_FRAME_ROLE_MESH_REVIEW_VERIFIED")
  self.assertEqual(self.browser["viewportChecks"],18)
  self.assertEqual(self.browser["imageLoads"],126)
  self.assertEqual(self.browser["screenshotCount"],6)
  self.assertFalse(self.browser["errors"])
  self.assertFalse(self.browser["failedRequests"])
  for pic in self.browser["screenshots"]:
   self.assertEqual(source.sha(source.P/"exports/p15-34-source-ink-mesh-review"/pic["path"]),
                    pic["sha256"])

 def test_artistic_and_physical_acceptance_independent(self):
  for key in ("physicalFarEyeNoseOcclusionVerified","clipPhysicalHairLockMountVerified",
              "artistLandmarksApproved","newIndependentKeyframePainting",
              "productionRendererChanged","formalArtisticAcceptance"):
   self.assertFalse(self.vdd[key])
  self.assertEqual(self.ink["verifiedIndependentArtistLandmarks"],0)

if __name__=="__main__":unittest.main()
