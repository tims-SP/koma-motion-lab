"""P15-36 registered model paint, source-cel controls and HTML visual QA."""
import json,hashlib,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/"scripts"))
import p15_36_qwen_local_repair as painter
import p15_36_cel_keyparts as vector
from p15_35_depth_mount import ROLES

class P15_36_KeypartPainting(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.paint=json.loads(painter.QA.read_text())
  cls.cel=json.loads(vector.QA.read_text())
  cls.browser=json.loads((R/"evidence/p15-36-browser-qa.json").read_text())
  cls.review=json.loads((painter.P/"exports/p15-36-original-keypart-review/qa.json").read_text())

 def test_identity_references(self):
  self.assertEqual(self.paint["characterId"],"p0_character_001")
  self.assertEqual(self.cel["characterId"],"p0_character_001")
  self.assertEqual(self.paint["sourceP15_35QA_SHA256"],painter.sha(R/"evidence/p15-35-occlusion-mount-qa.json"))
  self.assertEqual(self.cel["sourceP15_35SHA256"],vector.sha(R/"evidence/p15-35-occlusion-mount-qa.json"))

 def test_registered_painted_views(self):
  self.assertEqual(self.paint["angles"],[57.5,60.])
  self.assertEqual(self.cel["angles"],[57.5,60.])
  self.assertEqual(len(self.paint["frames"]),2)
  self.assertEqual(len(self.cel["frames"]),2)
  for frame in self.paint["frames"]:
   self.assertLess(abs(frame["registrationOffset"][0]),25)
   self.assertLess(abs(frame["registrationOffset"][1]),25)
   self.assertEqual(painter.sha(painter.P/frame["donor"]),frame["donorSHA256"])
   self.assertGreater(frame["changedCompositePixels"],10000)
   self.assertLess(frame["changedCompositePixels"],55000)
   self.assertFalse(frame["donorAngleSourceAcceptedAsKeyview"])

 def test_complete_thirteen_separate_rgba_roles(self):
  self.assertEqual(self.paint["semanticRoleCount"],13)
  self.assertEqual(len(self.paint["newModelPaintedROIRoles"]),3)
  for frame in self.paint["frames"]:
   folder=painter.OUT/painter.slug(frame["yaw"])
   for role in ROLES:
    with Image.open(folder/(role+".png")) as img:
     self.assertEqual(img.mode,"RGBA")
     self.assertEqual(img.size,(443,443))
     alpha=np.asarray(img.getchannel("A"))
     self.assertGreater(int(alpha.sum()),0,(role,frame["yaw"]))
     self.assertLess(int(alpha.max()),256)
   with Image.open(folder/"composite.png") as img:
    self.assertEqual(img.mode,"RGBA");self.assertEqual(img.size,(1024,1024))

 def test_other_ten_roles_byte_exact(self):
  for frame in self.paint["frames"]:
   key=painter.slug(frame["yaw"])
   for role in ROLES:
    if role in self.paint["newModelPaintedROIRoles"]:continue
    self.assertEqual((painter.OUT/key/(role+".png")).read_bytes(),
       (painter.SRC/key/(role+".png")).read_bytes())

 def test_three_model_painted_sources_have_new_pixels(self):
  for frame in self.paint["frames"]:
   self.assertEqual(set(frame["newPaintedSemanticRoles"]),{"eye.far","face.skin","hair.front"})
   for role,witness in frame["partDetails"].items():
    self.assertGreater(witness["visibleDonorAlphaPixels"],150)
    self.assertGreater(witness["changedPixels"],100)
    self.assertEqual(painter.sha(painter.P/witness["donorPaintPath"]),witness["donorPaintSHA256"])
    self.assertEqual(painter.sha(painter.OUT/painter.slug(frame["yaw"])/(role+".png")),
                     witness["targetOutputSHA256"])
    self.assertEqual(painter.sha(painter.SRC/painter.slug(frame["yaw"])/(role+".png")),
                     witness["sourceRoleSHA256"])

 def test_hidden_eye_source_preserved(self):
  for frame in self.paint["frames"]:
   folder=painter.OUT/painter.slug(frame["yaw"])
   original=painter.SRC/painter.slug(frame["yaw"])
   self.assertEqual((folder/"eye.far.original-underpaint.png").read_bytes(),
                    (original/"eye.far.original.png").read_bytes())
   self.assertEqual((folder/"eye.far.hidden-original.png").read_bytes(),
                    (original/"eye.far.hidden-underpaint.png").read_bytes())

 def test_local_paint_stays_in_face_region(self):
  for frame in self.paint["frames"]:
   key=painter.slug(frame["yaw"])
   orig=np.array(Image.open(painter.SRC/key/"composite.png").convert("RGBA"))
   img=np.array(Image.open(painter.OUT/key/"composite.png").convert("RGBA"))
   diff=np.any(orig!=img,axis=2)
   total=int(diff.sum());self.assertGreater(total,10000)
   localized=np.zeros(diff.shape,bool)
   localized[325:595,555:900]=True
   self.assertGreater(int((diff&localized).sum())/total,.96)

 def test_new_vector_control_is_independently_authored(self):
  self.assertEqual(self.cel["actualHandAuthoredStrokeRolesPerAngle"],4)
  for frame in self.cel["frames"]:
   self.assertEqual(frame["newAuthorPaintedRoleCount"],4)
   for role,entry in frame["painted"].items():
    self.assertEqual(entry["origin"],"ORIGINAL_HAND_AUTHORED_VECTOR_CEL_STROKES")
    self.assertGreater(entry["strokePixelCount"],12)
    self.assertEqual(vector.sha(vector.P/entry["strokePath"]),entry["strokeSHA256"])

 def test_review_provenance(self):
  self.assertEqual(len(self.review["frames"]),2)
  self.assertEqual(self.review["modeCount"],3)
  self.assertEqual(self.review["roleCount"],13)
  for frame in self.review["frames"]:
   folder=painter.P/"exports/p15-36-original-keypart-review"/frame["dir"]
   self.assertGreater(len(frame["sha256"]),13)
   for name,digest in frame["sha256"].items():
    self.assertEqual(painter.sha(folder/name),digest)

 def test_real_chromium(self):
  browser=self.browser
  self.assertEqual(browser["status"],"P15_36_KEYPART_SOURCE_HTML_VERIFIED")
  self.assertEqual(browser["viewportChecks"],12)
  self.assertEqual(browser["imageLoads"],48)
  self.assertEqual(browser["screenshotCount"],8)
  self.assertEqual(browser["pageErrors"],[])
  self.assertEqual(browser["failedRequests"],[])
  for shot in browser["screenshots"]:
   p=painter.P/"exports/p15-36-original-keypart-review"/shot["file"]
   self.assertEqual(painter.sha(p),shot["sha256"])

 def test_artist_gate_explicit(self):
  self.assertFalse(self.paint["modelFullImagePoseApproved"])
  self.assertFalse(self.paint["fullKeyviewArtAccepted"])
  self.assertFalse(self.paint["sourceP0HeroIdentityHashVerified"])
  self.assertEqual(self.paint["independentlyPaintedHiddenUnderpaintCount"],0)
  self.assertFalse(self.cel["fullKeyviewArtistApproval"])
  self.assertEqual(self.cel["diffusionFullKeyViewsAccepted"],0)
  self.assertFalse(self.paint["productionVddModified"])

if __name__=="__main__":unittest.main()
