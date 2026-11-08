#!/usr/bin/env python3
"""P0 P9 color-region correspondence source and real-browser integrity QA."""
import hashlib,json,unittest,zipfile
from pathlib import Path
from PIL import Image

BASE=Path(__file__).resolve().parents[1]
ASSETS=BASE/"private-assets"
ROOT=ASSETS/"p9-region-correspondence"
P5=ASSETS/"p5-see-through/mv-candidate"
P8=ASSETS/"p8-semantic-occlusion"

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def read(file):return json.loads(Path(file).read_text(encoding="utf-8"))

@unittest.skipUnless((ROOT/"qa.json").is_file(),"P0 private P9 color region source assets")
class P9OriginalRegionCorrespondence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.qa=read(ROOT/"qa.json")
  cls.browser=read(ROOT/"browser/browser-qa.json")
  cls.compare=read(ROOT/"comparison-qa.json")
  cls.registry=read(P5/"parts.json")

 def test_original_P0_source_provenance(self):
  j=self.qa
  self.assertEqual(j["schema"],"KOMA-P0-P9-REGION_GUIDED-CORRESPONDENCE-V1")
  self.assertEqual(j["characterId"],"p0_character_001")
  self.assertEqual(j["sourceOriginalKeyViews"],[0,45,90])
  self.assertEqual(j["sourcePSDViews"],[0,45])
  self.assertEqual(j["registeredSemanticPairs"],22)
  self.assertEqual(j["matchedColorRegions"],155)
  self.assertEqual(j["sourceRegistrySHA256"],sha(P5/"parts.json"))
  self.assertEqual(j["physicalLandmarksSHA256"],sha(P5/"landmark-qa.json"))
  self.assertEqual(j["contactSHA256"],sha(ASSETS/j["contactImage"]))

 def test_color_region_coordinates_remain_443_native(self):
  registered=0
  area=0
  slots={(x["yawDeg"],x["semanticId"]):x for x in self.registry["parts"]}
  for key,rec in self.qa["pairs"].items():
   yawA,yawB=rec["sourceAngles"]
   self.assertIn((yawA,yawB),[(0,45),(45,90)])
   self.assertEqual(key,f"{yawA}-{yawB}/"+rec["part"])
   a=slots[(yawA,rec["part"])];b=slots[(yawB,rec["part"])]
   self.assertEqual(rec["referenceSourceSHA256"],[a["frameSha256"],b["frameSha256"]])
   self.assertEqual(rec["matchedRegions"],len(rec["pairs"]))
   for p in rec["pairs"]:
    self.assertLess(p["colorRegion"],5)
    self.assertLessEqual(p["cost"],145)
    self.assertGreater(p["originArea"],0)
    self.assertGreater(p["destinationArea"],0)
    for xy in (p["originXY"],p["destinationXY"]):
     self.assertEqual(len(xy),2)
     self.assertTrue(all(0<=v<=443 for v in xy))
    registered+=1
    area+=min(p["originArea"],p["destinationArea"])
  self.assertEqual(registered,155)
  self.assertEqual(area,self.qa["matchedAreaPixels"])

 def test_real_source_png_sha256_and_transparency(self):
  checked=set()
  for part in self.registry["parts"]:
   file=ASSETS/part["path"]
   self.assertEqual(sha(file),part["frameSha256"])
   with Image.open(file) as im:
    self.assertEqual(im.mode,"RGBA")
    self.assertEqual(im.size,(1024,1024))
   checked.add((part["yawDeg"],part["semanticId"]))
  self.assertEqual(len(checked),39)

 def test_research_comparison_sources_real_pixels(self):
  report=self.compare
  self.assertEqual(report["characterId"],"p0_character_001")
  self.assertEqual(report["regionMatches"],155)
  self.assertEqual(report["registeredSemanticPairs"],22)
  self.assertEqual(report["contactGrid"]["sha256"],sha(ASSETS/report["contactGrid"]["path"]))
  self.assertEqual(report["qualityComparison"]["sha256"],sha(ASSETS/report["qualityComparison"]["path"]))
  self.assertEqual(len(report["methods"]),3)
  self.assertEqual(report["chosenGeometry"],"P8_SEMANTIC_OCCLUSION_ARTMESH_BASELINE")
  for method in report["methods"]:
   self.assertEqual(method["textureStatus"],"PASS_TEXTURE_EDGE_DIAGNOSTIC")
   for frame in method["frames"]:
    file=ASSETS/frame["sourcePath"]
    self.assertEqual(sha(file),frame["sha256"])
    with Image.open(file) as im:
     self.assertEqual(im.mode,"RGBA")
     self.assertEqual(im.size,(1024,1024))

 def test_real_chromium_6_semantic_source_captures(self):
  qa=self.browser
  self.assertEqual(qa["characterId"],"p0_character_001")
  self.assertEqual(qa["status"],"PASS_REAL_P0_REGION_CORRESPONDENCE_VIEW")
  self.assertEqual(qa["sourceRegisteredPairs"],22)
  self.assertEqual(qa["sourceRegisteredRegions"],155)
  self.assertEqual(qa["screenshotCount"],6)
  self.assertFalse(qa["errors"])
  self.assertFalse(qa["failedRequests"])
  for snap in qa["screenshots"]:
   self.assertEqual(sha(snap["path"]),snap["sha256"])
   self.assertEqual(len(snap["originalLayerHashes"]),2)
   for sig in snap["originalLayerHashes"]:
    self.assertTrue(any(x["frameSha256"]==sig for x in self.registry["parts"]))
   with Image.open(snap["path"]) as im:
    self.assertGreaterEqual(im.size[0],1280)
    self.assertGreaterEqual(im.size[1],660)
    self.assertLess(abs(im.size[0]/im.size[1]-1280/660),0.02)

 def test_genuine_P0_keyframe_render_endpoints_stable(self):
  for label in ("face","face-hair"):
   experiment=read(ROOT/label/"qa.json")
   self.assertEqual(experiment["characterId"],"p0_character_001")
   self.assertEqual(experiment["regionGuidedMode"],label)
   self.assertEqual(experiment["sourceRegionQA_SHA256"],sha(ROOT/"qa.json"))
   self.assertEqual(experiment["sourceAngles"],[0,45,90])

 @unittest.skipUnless((ROOT/"p9-package-qa.json").is_file(),
                      "P9 correspondence archive not generated")
 def test_standalone_region_browser_archive(self):
  report=read(ROOT/"p9-package-qa.json")
  self.assertEqual(report["characterId"],"p0_character_001")
  self.assertEqual(report["registeredColorRegions"],155)
  self.assertEqual(report["registeredSemanticPairs"],22)
  self.assertEqual(report["sourceSemanticArtMeshSlots"],39)
  self.assertEqual(report["browserScreenshots"],6)
  self.assertTrue(report["internalHashesVerified"])
  self.assertEqual(report["sha256"],sha(report["archivePath"]))
  with zipfile.ZipFile(report["archivePath"]) as z:
   self.assertIsNone(z.testzip())
   contents=json.loads(z.read("package-manifest.json"))
   self.assertEqual(contents["characterId"],"p0_character_001")
   self.assertEqual(contents["matchedColorRegions"],155)
   self.assertEqual(contents["sourceSemanticArtMeshSlots"],39)

if __name__=="__main__":
 unittest.main(verbosity=2)
