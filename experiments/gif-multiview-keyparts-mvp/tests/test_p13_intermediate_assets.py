#!/usr/bin/env python3
"""P13 original P0 0-90-degree native ArtMesh intermediate source QA."""
import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"private-assets"
P=A/"p13-source-priority"
FRAME=P/"source-feathered"
P8=A/"p8-semantic-occlusion/selective-sequence"

def read(p):return json.loads(Path(p).read_text(encoding="utf8"))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

@unittest.skipUnless((P/"p13-paint-contract.json").is_file(),
                      "Original P0 intermediate source artwork unavailable")
class P13IntermediateOriginalSourceArt(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.contract=read(P/"p13-paint-contract.json")
  cls.qa=read(FRAME/"qa.json")
  cls.browser=read(P/"browser/browser-qa.json")
  cls.compare=read(P/"comparison-qa.json")
  cls.gif=read(P/"p0-character-001-intermediate-turn.qa.json")
  cls.baseline=read(P8/"qa.json")

 def test_single_P0_identity_and_sources(self):
  for d in (self.contract,self.qa,self.browser,self.compare,self.gif,self.baseline):
   self.assertEqual(d["characterId"],"p0_character_001")
  self.assertEqual(self.contract["sourceApprovedCharacterViews"],[0,45,90])
  self.assertEqual(self.contract["imageContract"]["canvas"],[1024,1024])
  self.assertEqual(self.contract["sourceP11Editable90PSD_SHA256"],
                   sha(A/"p11-profile-psd/yaw090/p0-character-001-registered-profile-yaw090.psd"))
  self.assertEqual(self.contract["imageContract"]["viewList"],[67.5,72.5])
  self.assertTrue(self.contract["imageContract"]["oneFrameOneSemanticComponent"])
  self.assertEqual(self.contract["imageContract"]["componentCountPerView"],13)

 def test_37_original_source_rgba_motion_frames_and_SHA(self):
  self.assertEqual(self.qa["frameCount"],37)
  self.assertEqual(len(self.qa["frames"]),37)
  self.assertEqual(self.baseline["frameCount"],37)
  for ix,frame in enumerate(self.qa["frames"]):
   self.assertEqual(frame["angle"],ix*2.5)
   source=A/frame["path"]
   self.assertEqual(sha(source),frame["sha256"])
   with Image.open(source) as picture:
    self.assertEqual(picture.mode,"RGBA")
    self.assertEqual(picture.size,(1024,1024))

 def test_original_author_keyview_pixels_remain_exact(self):
  original=read(A/"p5-see-through/mv-candidate/parts.json")
  keys={item["yawDeg"]:item for item in original["wholeViews"]}
  for angle in (0,45,90):
   reference=A/keys[angle]["path"]
   self.assertEqual(sha(reference),keys[angle]["sha256"])
   render=next(x for x in self.qa["frames"] if x["angle"]==angle)
   with Image.open(reference) as a,Image.open(A/render["path"]) as b:
    self.assertTrue(np.array_equal(np.asarray(a),np.asarray(b)),
                    "Original P0 keyframe changed "+str(angle))

 def test_13_native_RGBA_semantic_parts_per_intermediate_angle(self):
  self.assertEqual(self.qa["semanticLayerCount"],26)
  self.assertEqual(len(self.contract["intermediateViews"]),2)
  self.assertEqual(len(self.qa["semanticLayers"]),26)
  for angleview in self.contract["intermediateViews"]:
   self.assertIn(angleview["viewAngle"],[67.5,72.5])
   self.assertEqual(angleview["registeredArtMeshSemanticSlots"],13)
   self.assertTrue(angleview["reconstructionPixelExact"])
   self.assertEqual(len(angleview["parts"]),13)
   IDs=set()
   for ix,part in enumerate(angleview["parts"]):
    self.assertNotIn(part["semanticId"],IDs)
    IDs.add(part["semanticId"])
    self.assertEqual(part["semanticDepthOrder"],ix)
    self.assertEqual(part["globalCanvas"],[1024,1024])
    self.assertEqual(part["imageEncoding"],"PNG RGBA8")
    file=A/part["sourceDerivedCandidate"]["path"]
    self.assertEqual(sha(file),part["sourceDerivedCandidate"]["sha256"])
    with Image.open(file) as img:
     self.assertEqual(img.mode,"RGBA")
     self.assertEqual(img.size,(1024,1024))
     alpha=np.asarray(img.getchannel("A"))
     self.assertEqual(int((alpha>0).sum()),
                      part["alphaVisibility"]["opaqueOrTranslucentPixelCount"])
     self.assertGreaterEqual(int(alpha.max()),0)
    for source in ("source45","source90"):
     self.assertEqual(sha(A/part[source]["path"]),part[source]["sha256"])
   self.assertEqual(len(IDs),13)

 def test_semantic_png_recomposes_full_source_at_67p5_72p5(self):
  for view in self.contract["intermediateViews"]:
   reconstructed=Image.new("RGBA",(1024,1024),(0,0,0,0))
   for part in view["parts"]:
    with Image.open(A/part["sourceDerivedCandidate"]["path"]) as im:
     reconstructed.alpha_composite(im.convert("RGBA"))
   full=A/view["sourceDerivedFrame"]["path"]
   self.assertEqual(sha(full),view["sourceDerivedFrame"]["sha256"])
   with Image.open(full) as frame:
    self.assertTrue(np.array_equal(np.asarray(reconstructed),
                                   np.asarray(frame.convert("RGBA"))))

 def test_occluded_semantics_retain_transparent_ID(self):
  for view in self.contract["intermediateViews"]:
   items={x["semanticId"]:x for x in view["parts"]}
   far=items["ear.far"]
   self.assertEqual(far["alphaVisibility"]["maxAlpha"],0)
   self.assertEqual(far["referenceVisibility45"],"hidden")
   self.assertEqual(far["referenceVisibility90"],"hidden")
   if view["viewAngle"]==72.5:
    gold=items["hair.clip.cross_gold"]
    self.assertEqual(gold["alphaVisibility"]["maxAlpha"],0)

 def test_expected_landmark_tracks_registered_not_painted(self):
  for view in self.contract["intermediateViews"]:
   self.assertGreater(len(view["predictedReferenceAnchors"]),7)
   for anchor in view["predictedReferenceAnchors"]:
    self.assertEqual(len(anchor["referenceXY"]),2)
    self.assertEqual(anchor["coordRole"],
                     "LINEAR_REFERENCE_NOT_MEASURED_INTERMEDIATE_ART")
    self.assertTrue(all(0<=x<=1024 for x in anchor["referenceXY"]))
  self.assertEqual(self.contract["imageContract"]["sourcePaintingApproval"],
                   "PENDING_GENERATIVE_OR_MANUAL_AUTHORING")
  self.assertEqual(self.compare["independentPaintComponentsPending"],18)

 def test_source_motion_temporal_and_texture_diagnostics(self):
  texture=read(FRAME/"texture-qa.json")
  temporal=read(FRAME/"temporal-qa.json")
  p8t=read(P8/"texture-qa.json")
  self.assertEqual(texture["status"],"PASS_TEXTURE_EDGE_DIAGNOSTIC")
  self.assertEqual(temporal["status"],"PASS_TEMPORAL_CONTINUITY")
  self.assertEqual(len(temporal["outliers"]),0)
  self.assertEqual(temporal["angles"],37)
  self.assertEqual(self.compare["adoptedMotionBaseline"],"P8_SEMANTIC_OCCLUSION")
  ratio=lambda d:next(x["edgeDensityRelativeToAdjacentMax"] for x in d["holdouts"]
                     if x["angle"]==67.5)
  self.assertGreater(ratio(texture),ratio(p8t))

 def test_original_source_motion_GIF_sha_and_duration(self):
  file=P/"p0-character-001-intermediate-turn.gif"
  self.assertEqual(sha(file),self.gif["GIFSHA256"])
  self.assertEqual(self.gif["sourceFrameCount"],37)
  self.assertEqual(self.gif["GIFFrames"],72)
  with Image.open(file) as gif:
   self.assertEqual(gif.n_frames,72)
   self.assertEqual(gif.size,(512,512))

 def test_true_chromium_12_original_source_screenshots(self):
  b=self.browser
  self.assertEqual(b["status"],"PASS_REAL_ORIGINAL_P0_INTERMEDIATE_LAYER_REVIEW")
  self.assertEqual(b["sourceRGBAFrames"],37)
  self.assertEqual(b["registeredSemanticLayerFrames"],26)
  self.assertEqual(b["screenshotCount"],12)
  self.assertEqual(len(b["screens"]),6)
  self.assertFalse(b["errors"])
  self.assertFalse(b["failedRequests"])
  for rec in b["screens"]:
   self.assertEqual(rec["verifiedSHAImages"],5)
   self.assertIn(rec["layerYaw"],[67.5,72.5])
   for capture in rec["captures"].values():
    self.assertEqual(sha(capture["path"]),capture["sha256"])
    with Image.open(capture["path"]) as img:
     self.assertGreater(img.size[0],980)
     self.assertGreaterEqual(img.size[1],500)
     self.assertLess(abs(img.size[0]/img.size[1]-
          (1024/550 if "motion" in rec["captures"] and capture==rec["captures"]["motion"] else 1536/550)),0.03)

 @unittest.skipUnless((P/"p13-package-qa.json").is_file(),
                      "Original source package not built yet")
 def test_private_source_art_package_SHA_CRC(self):
  pkg=read(P/"p13-package-qa.json")
  self.assertEqual(pkg["characterId"],"p0_character_001")
  self.assertEqual(pkg["intermediateRGBAComponentSlots"],26)
  self.assertEqual(pkg["sourceDerivedRGBAFrames"],37)
  self.assertEqual(pkg["actualChromiumScreenshots"],12)
  self.assertTrue(pkg["internalHashesVerified"])
  self.assertEqual(sha(pkg["archivePath"]),pkg["sha256"])
  with zipfile.ZipFile(pkg["archivePath"]) as z:
   self.assertIsNone(z.testzip())
   manifest=json.loads(z.read("package-manifest.json"))
   self.assertEqual(manifest["characterId"],"p0_character_001")
   self.assertEqual(manifest["sourceOriginalKeyViews"],[0,45,90])
   self.assertEqual(manifest["intermediateSemanticComponentSlots"],26)

if __name__=="__main__":
 unittest.main(verbosity=2)
