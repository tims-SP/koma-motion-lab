"""P15-35 far-eye face-depth and front-hair clip UV contract regression."""
import hashlib,json,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/"scripts"))
import p15_35_depth_mount as dm

class P15_35_DepthAndMount(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.qa=json.loads(dm.QA.read_text())
  cls.parent=json.loads(dm.MESH.read_text())
  cls.review=json.loads((dm.P/"exports/p15-35-face-depth-hair-review/qa.json").read_text())
  cls.browser=json.loads((dm.R/"evidence/p15-35-browser-qa.json").read_text())

 def test_identity_and_source_sha(self):
  self.assertEqual(self.qa["characterId"],"p0_character_001")
  self.assertEqual(self.qa["sourceMeshQA_SHA256"],dm.sha(dm.MESH))
  self.assertEqual(self.qa["sourceInkQA_SHA256"],dm.sha(dm.OBS))
  self.assertEqual(self.qa["sourceP0OriginalSHA256"],"78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40")
  self.assertEqual(len(self.qa["frames"]),9)

 def test_p15_34_source_and_individual_parts_untouched(self):
  self.assertEqual(self.qa["angles"],self.parent["angles"])
  for f in self.qa["frames"]:
   tag=dm.slug(f["yaw"])
   self.assertEqual(f["sourceCompositeSHA256"],dm.sha(dm.SRC/tag/"composite.png"))
   self.assertEqual(f["sourceEyeSHA256"],dm.sha(dm.SRC/tag/"eye.far.png"))
   self.assertEqual(f["sourceClipSHA256"],dm.sha(dm.SRC/tag/"hair.clip.cross_gold.png"))
   for role in dm.ROLES:
    if role in ("eye.far","hair.clip.cross_gold"):continue
    self.assertEqual((dm.SRC/tag/(role+".png")).read_bytes(),
                     (dm.OUT/tag/(role+".png")).read_bytes())

 def test_eye_visible_hidden_rgba_partition(self):
  for f in self.qa["frames"]:
   tag=dm.slug(f["yaw"])
   full=dm.read(dm.OUT/tag/"eye.far.original.png")
   visible=dm.read(dm.OUT/tag/"eye.far.png")
   hidden=dm.read(dm.OUT/tag/"eye.far.hidden-underpaint.png")
   self.assertTrue(np.array_equal(full[:,:,:3],visible[:,:,:3]))
   self.assertTrue(np.array_equal(full[:,:,:3],hidden[:,:,:3]))
   self.assertLessEqual(int(np.abs(full[:,:,3].astype(np.int16)-visible[:,:,3].astype(np.int16)-hidden[:,:,3].astype(np.int16)).max()),1)
   self.assertGreater(int(hidden[:,:,3].sum()),10000)

 def test_alpha_occlusion_exclusivity_and_angular_continuity(self):
  fractions=[]
  for f in self.qa["frames"]:
   parts=f["eyeAlphaPartitionFractions"]
   self.assertAlmostEqual(sum(parts.values()),1.0,delta=.002)
   self.assertLess(parts["hiddenByNose"],.01)
   self.assertGreater(parts["hiddenByFace"],0)
   self.assertGreater(parts["hiddenByBangs"],0)
   self.assertFalse(f["wholeLayerEyeFadeApplied"])
   self.assertTrue(f["eyeSourceRGBKept"])
   fractions.append(parts["eyeVisible"])
  self.assertGreater(fractions[0],.75)
  self.assertLess(fractions[-1],.10)
  self.assertTrue(all(b<=a+.012 for a,b in zip(fractions,fractions[1:])))

 def test_front_hair_attachment_across_all_frames(self):
  xy=[]
  offsets=[]
  for f in self.qa["frames"]:
   m=f["clipAttachment"]
   self.assertEqual(m["parentRole"],"hair.front")
   self.assertFalse(m["physicallyApprovedMount"])
   self.assertGreater(m["attachedContactCoverage"],m["sourceContactCoverage"]+.09)
   self.assertLess(m["uvResidual"],.12)
   self.assertLessEqual(np.linalg.norm(m["clipPixelShift"]),6.0)
   offsets.append(m["clipPixelShift"])
   xy.append(m["centerAfter443"])
  self.assertTrue(all(abs(b[0]-a[0])<=4 and abs(b[1]-a[1])<=4
                      for a,b in zip(xy,xy[1:])),xy)
  self.assertTrue(all(np.linalg.norm(np.array(a)-np.array(b))<=1.5
                      for a,b in zip(offsets,offsets[1:])),offsets)

 def test_face_source_pixels_and_masks_are_derivative(self):
  for f in self.qa["frames"]:
   tag=dm.slug(f["yaw"]);mask=dm.OUT/tag/"face-depth-proxy.png"
   with Image.open(mask) as im:
    self.assertEqual(im.mode,"L")
    self.assertEqual(im.size,(443,443))
   self.assertEqual(f["sourceSkinSHA256"],dm.sha(dm.SRC/tag/"face.skin.png"))
   with Image.open(dm.OUT/tag/"composite.png") as im:
    self.assertEqual(im.size,(1024,1024))
    self.assertEqual(im.mode,"RGBA")
   self.assertEqual(f["outputSHA256"],dm.sha(dm.OUT/tag/"composite.png"))

 def test_visual_review_file_provenance(self):
  self.assertEqual(len(self.review["frames"]),9)
  out=dm.P/"exports/p15-35-face-depth-hair-review"
  for item in self.review["frames"]:
   folder=out/item["dir"]
   for name,digest in item["outputs"].items():
    self.assertEqual(dm.sha(folder/name),digest)

 def test_actual_browser_evidence(self):
  b=self.browser
  self.assertEqual(b["status"],"P15_35_NINE_FRAME_DEPTH_REVIEW_VERIFIED")
  self.assertEqual(b["viewportChecks"],18)
  self.assertEqual(b["imageLoads"],198)
  self.assertEqual(b["screenshotCount"],6)
  self.assertEqual(b["pageErrors"],[])
  self.assertEqual(b["failedRequests"],[])
  for cap in b["captures"]:
   self.assertEqual(dm.sha(dm.P/"exports/p15-35-face-depth-hair-review"/cap["path"]),cap["sha256"])

 def test_artistic_gate_separate(self):
  self.assertFalse(self.qa["faceMask3DModelValidated"])
  self.assertFalse(self.qa["nosePhysicalVolumeVerified"])
  self.assertFalse(self.qa["clipMount3DValidated"])
  self.assertFalse(self.qa["artistApprovedOcclusion"])
  self.assertFalse(self.qa["artistApprovedHairLock"])
  self.assertFalse(self.qa["productionRendererChanged"])
  self.assertFalse(self.qa["formalArtisticAcceptance"])
  self.assertEqual(self.qa["newIndependentPaintings"],0)
  self.assertTrue(self.qa["underpaintRecoveredFromOriginalRGB"])

if __name__=="__main__":unittest.main()
