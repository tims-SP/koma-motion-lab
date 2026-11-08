#!/usr/bin/env python3
"""P10 true P0 ink-stroke identity and browser evidence regression."""
import hashlib,json,unittest,zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"private-assets"
P=A/"p10-stroke-identity"
P8=A/"p8-semantic-occlusion"
P9=A/"p9-region-correspondence"
P5=A/"p5-see-through/mv-candidate"

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def get(path):
 return json.loads(Path(path).read_text(encoding="utf-8"))

@unittest.skipUnless((P/"qa.json").is_file(),"Private original P0 ink stroke source")
class P10StrokeIdentity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.qa=get(P/"qa.json")
  cls.browser=get(P/"browser/browser-qa.json")
  cls.p8=get(P8/"selective-sequence/qa.json")
  cls.parts=get(P5/"parts.json")

 def test_P0_role_keyframes_and_origin_integrity(self):
  d=self.qa
  self.assertEqual(d["schema"],"KOMA-P0-P10-INK_STROKE-IDENTITY-CANDIDATES-V1")
  self.assertEqual(d["characterId"],"p0_character_001")
  self.assertEqual(d["sourceP0KeyViews"],[0,45,90])
  self.assertEqual(d["genuinePSDViews"],[0,45])
  self.assertEqual(d["sourceArtMeshViewSlots"],39)
  self.assertEqual(d["sourceRegistrySHA256"],sha(P5/"parts.json"))
  self.assertEqual(d["physicalLandmarksSHA256"],sha(P5/"landmark-qa.json"))
  self.assertEqual(d["regionQA_SHA256"],sha(P9/"qa.json"))
  self.assertEqual(d["contactSHA256"],sha(A/d["contactImage"]))

 def test_actual_RGBA_layers_stroke_components(self):
  sources=self.qa["sources"]
  self.assertEqual(len(sources),39)
  count=0
  for role,record in sources.items():
   source=A/record["path"]
   self.assertEqual(sha(source),record["sha256"])
   with Image.open(source) as im:
    self.assertEqual(im.size,(1024,1024))
    self.assertEqual(im.mode,"RGBA")
   seen=set()
   for item in record["strokes"]:
    self.assertNotIn(item["id"],seen)
    seen.add(item["id"])
    self.assertGreaterEqual(item["area"],9)
    self.assertTrue(all(0<=c<=443 for c in item["xy"]))
    self.assertGreater(item["bbox"][2],0)
    self.assertGreater(item["bbox"][3],0)
    count+=1
  self.assertEqual(count,self.qa["extractedStrokes"])
  self.assertEqual(count,184)

 def test_unique_high_confidence_bidirectional_pair_ids(self):
  self.assertEqual(self.qa["registeredSemanticPairs"],22)
  self.assertEqual(self.qa["candidateIdentities"],24)
  total=0
  for label,record in self.qa["pairs"].items():
   self.assertEqual(label,str(record["angles"][0])+"-"+str(record["angles"][1])+"/"+record["semanticId"])
   a,b=record["angles"]
   self.assertIn((a,b),((0,45),(45,90)))
   self.assertEqual(record["sourceSHA256"],[
    self.qa["sources"][str(y)+"/"+record["semanticId"]]["sha256"] for y in (a,b)])
   usedA=set();usedB=set()
   for edge in record["accepted"]:
    self.assertGreaterEqual(edge["confidence"],self.qa["minConfidence"])
    self.assertGreaterEqual(edge["ambiguityMargin"],6)
    self.assertEqual(edge["occlusion"],"COMMON_VISIBLE_CANDIDATE")
    self.assertNotIn(edge["sourceId"],usedA)
    self.assertNotIn(edge["targetId"],usedB)
    usedA.add(edge["sourceId"]);usedB.add(edge["targetId"])
    total+=1
   self.assertTrue(usedA.isdisjoint(set(record["occludedCandidates"])))
   self.assertTrue(usedB.isdisjoint(set(record["appearingCandidates"])))
  self.assertEqual(total,24)

 def test_far_eye_and_gold_clip_disappear_at_profile(self):
  pairs=self.qa["pairs"]
  self.assertNotIn("45-90/eye.far",pairs)
  self.assertNotIn("45-90/hair.clip.cross_gold",pairs)
  p8=get(P8/"selective-sequence/qa.json")
  state={v["semanticId"]:v["visibilityWindow"] for v in p8["occlusionWindows"]}
  self.assertEqual(state["eye.far"],[52,75])
  self.assertEqual(state["hair.clip.cross_gold"],[48,70])

 def test_conservative_stroke_coverage_is_diagnostic(self):
  # At yaw 45–90 the front-hair motion is underdetermined by the
  # independently registered P0 sources; don't silently accept it.
  p=self.qa["pairs"]["45-90/hair.front"]
  self.assertLessEqual(len(p["accepted"]),2)
  self.assertGreater(len(p["occludedCandidates"]),0)
  self.assertGreater(len(p["appearingCandidates"]),0)
  self.assertEqual(self.qa["visualApproval"],
                   "PENDING_MANUAL_IDENTITY_AND_VIEW_MOTION_INSPECTION")

 def test_baked_P8_motion_source_stays_unchanged(self):
  self.assertEqual(self.p8["frameCount"],37)
  self.assertEqual(self.p8["registeredArtMeshViews"],39)
  for x in self.p8["frames"]:
   file=A/x["path"]
   self.assertEqual(sha(file),x["sha256"])
  self.assertEqual(get(P8/"selective-sequence/temporal-qa.json")["status"],
                   "PASS_TEMPORAL_CONTINUITY")
  self.assertEqual(get(P8/"selective-sequence/texture-qa.json")["status"],
                   "PASS_TEXTURE_EDGE_DIAGNOSTIC")

 def test_browser_displays_real_sources_and_P8_frames(self):
  browser=self.browser
  self.assertEqual(browser["characterId"],"p0_character_001")
  self.assertEqual(browser["status"],"PASS_REAL_ORIGINAL_P0_STROKE_REVIEW")
  self.assertEqual(browser["semanticPairs"],22)
  self.assertEqual(browser["strokeCandidates"],24)
  self.assertEqual(browser["screenshotCount"],6)
  self.assertFalse(browser["errors"])
  self.assertFalse(browser["failedRequests"])
  for rec in browser["screenshots"]:
   self.assertEqual(sha(rec["path"]),rec["sha256"])
   self.assertIn(rec["yaw"],[22.5,67.5,72.5])
   with Image.open(rec["path"]) as im:
    self.assertGreaterEqual(im.size[0],1500)
    self.assertGreaterEqual(im.size[1],565)

 @unittest.skipUnless((P/"p10-package-qa.json").is_file(),
                      "P10 private review package still under construction")
 def test_private_original_source_archive(self):
  pkg=get(P/"p10-package-qa.json")
  self.assertEqual(pkg["characterId"],"p0_character_001")
  self.assertEqual(pkg["originalRGBAViewSlots"],39)
  self.assertEqual(pkg["P8RGBAFrames"],37)
  self.assertEqual(pkg["originalStrokeCandidates"],24)
  self.assertTrue(pkg["internalHashesVerified"])
  self.assertEqual(sha(pkg["archivePath"]),pkg["sha256"])
  with zipfile.ZipFile(pkg["archivePath"]) as z:
   self.assertIsNone(z.testzip())
   data=json.loads(z.read("package-manifest.json"))
   self.assertEqual(data["characterId"],"p0_character_001")
   self.assertEqual(data["registeredSemanticPairs"],22)

if __name__=="__main__":
 unittest.main(verbosity=2)
