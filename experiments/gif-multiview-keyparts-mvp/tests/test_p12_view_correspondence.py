#!/usr/bin/env python3
"""P12 real-source P0 VDD alternatives and anatomical source gap QA."""
import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image

EXP=Path(__file__).resolve().parents[1]
A=EXP/"private-assets"
P=A/"p12-comparison"
G=A/"p12-occlusion-gap"
P8=A/"p8-semantic-occlusion"
P11=A/"p11-profile-psd/yaw090"

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def load(p):return json.loads(Path(p).read_text(encoding="utf8"))

@unittest.skipUnless((P/"comparison-qa.json").is_file(),"Original P0 private asset review")
class P12ViewAnatomyAndOcclusion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cmp=load(P/"comparison-qa.json")
  cls.gap=load(G/"qa.json")
  cls.browser=load(P/"browser/browser-qa.json")
  cls.profile=load(P11/"qa.json")
  cls.p8=load(P8/"selective-sequence/qa.json")
  cls.methods={m["id"]:m for m in cls.cmp["methods"]}

 def test_approved_P0_and_source_PSD_invariants(self):
  for rec in (self.cmp,self.gap,self.browser,self.profile):
   self.assertEqual(rec["characterId"],"p0_character_001")
  self.assertEqual(self.cmp["P0OriginalViews"],[0,45,90])
  self.assertEqual(self.cmp["PSDViews"],[0,45,90])
  self.assertEqual(self.cmp["semanticArtMeshSlots"],39)
  self.assertEqual(self.cmp["P11RealProfilePSD_SHA256"],sha(A/self.profile["psdPath"]))
  self.assertEqual(self.profile["PSDCompositeAlphaMaxDifference"],0)
  self.assertTrue(self.profile["sourceReconstructionPixelExact"])

 def test_P8_source_review_stays_adopted_reference(self):
  self.assertEqual(self.cmp["P12FullMotionAdoption"],
                   "P8_SEMANTIC_OCCLUSION_REMAINS_REFERENCE")
  self.assertEqual(self.cmp["P12ModifiedRenderingFullMotionStatus"],
                   "CANDIDATE_HOLDOUT_ONLY")
  self.assertEqual(self.p8["frameCount"],37)
  self.assertEqual(load(P8/"selective-sequence/temporal-qa.json")["status"],
                   "PASS_TEMPORAL_CONTINUITY")
  self.assertEqual(len(self.methods),5)

 def test_registered_frames_original_0_45_90_pixel_exact(self):
  sources={int(z["angle"]):z for z in self.cmp["methods"][0]["frames"]
           if z["angle"] in (0,45,90)}
  self.assertEqual(set(sources),{0,45,90})
  for m in self.cmp["methods"]:
   self.assertEqual(len(m["frames"]),6)
   self.assertEqual([r["angle"] for r in m["frames"]],[0,22.5,45,67.5,72.5,90])
   for r in m["frames"]:
    p=A/r["path"]
    self.assertEqual(sha(p),r["sha256"])
    self.assertEqual(p.stat().st_size,r["bytes"])
    with Image.open(p) as im:
     self.assertEqual(im.mode,"RGBA")
     self.assertEqual(im.size,(1024,1024))
   for angle in (0,45,90):
    source=next(x for x in m["frames"] if x["angle"]==angle)
    with Image.open(A/source["path"]) as src,Image.open(A/sources[angle]["path"]) as tgt:
     self.assertTrue(np.array_equal(np.asarray(src),np.asarray(tgt)),
       f"P0 original keyframe changed at {m['id']}, angle {angle}")

 def test_source_correspondence_gap_metrics(self):
  self.assertEqual(self.gap["registeredPairCount"],13)
  self.assertEqual(self.gap["registeredSemanticSlots"],39)
  self.assertEqual(self.gap["originalRegistrySHA256"],
                   sha(A/"p5-see-through/mv-candidate/parts.json"))
  self.assertEqual(self.gap["masterPSDSource90SHA256"],self.profile["psdSHA256"])
  self.assertEqual(self.cmp["sourceGapAtlasSHA256"],sha(G/"qa.json"))
  parts={v["role"]:v for v in self.gap["parts"]}
  self.assertEqual(len(parts),13)
  for role in ("ear.near","mouth","nose","body.reference","hair.back","hair.front"):
   self.assertGreater(parts[role]["targetOnlyFraction"],.15)
   self.assertGreater(parts[role]["targetOnlyPixels"],0)
  self.assertEqual({x["semanticId"] for x in self.cmp["sourceGapPriority"]},
                   {"ear.near","mouth","nose","body.reference","hair.back","hair.front"})

 def test_original_P0_warp_gap_images_are_sha_verified(self):
  records=[p for p in self.gap["parts"] if p.get("sourceComparisonPath")]
  self.assertGreaterEqual(len(records),9)
  for p in records:
   file=A/p["sourceComparisonPath"]
   self.assertEqual(sha(file),p["sourceComparisonSHA256"])
   with Image.open(file) as im:
    self.assertEqual(im.size,(1329,487))
  self.assertEqual(self.cmp["comparisonContactSHA256"],
                   sha(A/self.cmp["comparisonContactPath"]))
  for item in self.cmp["sourceGapPriority"]:
   self.assertEqual(item["visualAtlasSHA256"],sha(A/item["visualAtlasPath"]))

 def test_four_region_aware_original_artwork_trials(self):
  self.assertEqual(set(self.methods),{
   "p8-selective","anatomy","anatomy-strokes","stroke-wide","affine-face"})
  for key in ("anatomy","anatomy-strokes","stroke-wide","affine-face"):
   q=load(A/f"p12-anatomical/{key}-holdout/qa.json")
   self.assertEqual(q["characterId"],"p0_character_001")
   self.assertEqual(q["sourceStrokesSHA256"],sha(A/"p10-stroke-identity/qa.json"))
   self.assertEqual(q["sourceProfilePSD_SHA256"],self.profile["psdSHA256"])
   self.assertEqual(q["frameCount"],6)
   self.assertEqual(q["mode"],key)
   tex=load(A/f"p12-anatomical/{key}-holdout/texture-qa.json")
   self.assertEqual(tex["status"],self.methods[key]["textureStatus"])
  self.assertEqual(self.methods["affine-face"]["textureStatus"],
                   "REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE")
  self.assertEqual(self.methods["p8-selective"]["textureStatus"],
                   "PASS_TEXTURE_EDGE_DIAGNOSTIC")

 def test_45_to_90_face_correspondence_reliability(self):
  base=float(self.methods["p8-selective"]["textureRatios"]["67.5"])
  for m in self.cmp["methods"][1:]:
   self.assertGreater(float(m["textureRatios"]["67.5"]),base)
  self.assertEqual(self.cmp["P12TextureAdoption"],
                   "PENDING_ARTISTIC_AND_CONTINUITY_REVIEW")

 def test_12_real_Chromium_source_screenshots(self):
  browser=self.browser
  self.assertEqual(browser["status"],"PASS_REAL_SOURCE_ARTMESH_P12_REVIEW")
  self.assertEqual(browser["sourceOriginalViewAngles"],[0,45,90])
  self.assertEqual(browser["methodCount"],5)
  self.assertEqual(browser["sourcePartGapCount"],13)
  self.assertEqual(browser["screenshotCount"],12)
  self.assertFalse(browser["errors"])
  self.assertFalse(browser["failedRequests"])
  self.assertEqual(len(browser["screens"]),6)
  for shot in browser["screens"]:
   self.assertEqual(shot["verifiedSourceImages"],3)
   self.assertGreater(shot["gapRatio"],0)
   for p in shot["screenshots"].values():
    self.assertEqual(sha(p["path"]),p["sha256"])
    with Image.open(p["path"]) as im:
     self.assertGreaterEqual(im.size[0],900)
     self.assertGreaterEqual(im.size[1],350)

 @unittest.skipUnless((P/"p12-package-qa.json").is_file(),"Review archive pending")
 def test_standalone_P12_reviewer_source_archive(self):
  pkg=load(P/"p12-package-qa.json")
  self.assertEqual(pkg["characterId"],"p0_character_001")
  self.assertTrue(pkg["internalHashesVerified"])
  self.assertEqual(pkg["sourceGaps"],13)
  self.assertEqual(pkg["sourceCandidateMethods"],5)
  self.assertEqual(pkg["sourceBrowserScreenshots"],12)
  self.assertEqual(pkg["sha256"],sha(pkg["archivePath"]))
  with zipfile.ZipFile(pkg["archivePath"]) as z:
   self.assertIsNone(z.testzip())
   manifest=json.loads(z.read("package-manifest.json"))
   self.assertEqual(manifest["characterId"],"p0_character_001")
   self.assertEqual(manifest["sourceViews"],[0,45,90])
   self.assertEqual(manifest["registeredSemanticArtMeshSlots"],39)

if __name__=="__main__":
 unittest.main(verbosity=2)
