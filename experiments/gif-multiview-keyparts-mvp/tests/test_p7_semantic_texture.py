#!/usr/bin/env python3
"""P0 2.75D semantic texture and real Chromium 0-90° visual QA."""
import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"private-assets"
P7=ASSETS/"p7-semantic-dense"
P5=ASSETS/"p5-see-through/mv-candidate"

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as fp:
  for block in iter(lambda:fp.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def get(file):
 return json.loads(Path(file).read_text(encoding="utf-8"))

def rgba(file):
 with Image.open(file) as im:
  assert im.mode=="RGBA" and im.size==(1024,1024)
  return np.array(im)

@unittest.skipUnless((P7/"viewer-manifest.json").is_file(),
                     "Private P0 view-texture study assets")
class P7MultiViewSemanticTexture(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=get(P7/"viewer-manifest.json")
  cls.methods={m["id"]:m for m in cls.manifest["methods"]}
  cls.browser=get(P7/"browser/browser-qa.json")

 def test_semantic_rgba_reference_identity(self):
  m=self.manifest
  self.assertEqual(m["characterId"],"p0_character_001")
  self.assertEqual(m["schema"],"KOMA-P0-P7-REAL-RGBA-ANATOMY-REVIEW-V1")
  self.assertEqual(m["sourcePSDViews"],[0,45])
  self.assertEqual(m["originalKeyAngles"],[0,45,90])
  self.assertEqual(m["canvas"],[1024,1024])
  self.assertEqual(m["artisticAcceptance"],"PENDING")

 def test_111_native_1024_RGBA_with_sha256(self):
  self.assertEqual(set(self.methods),{"p6-mesh","p7-dense","p7-guided"})
  self.assertEqual(sum(len(m["frames"]) for m in self.methods.values()),111)
  for method in self.methods.values():
   self.assertEqual(len(method["frames"]),37)
   for idx,f in enumerate(method["frames"]):
    self.assertEqual(f["angle"],idx*2.5)
    filename=ASSETS/f["path"]
    self.assertEqual(f["sha256"],sha(filename))
    self.assertEqual(f["bytes"],filename.stat().st_size)
    with Image.open(filename) as im:
     self.assertEqual(im.mode,"RGBA")
     self.assertEqual(im.size,(1024,1024))

 def test_genuine_original_P0_endpoints_are_pixel_exact(self):
  source={i["angle"]:i for i in self.manifest["authoritativeOriginalFrames"]}
  for angle in (0,45,90):
   original=ASSETS/source[angle]["path"]
   self.assertEqual(sha(original),source[angle]["sha256"])
   pixels=rgba(original)
   for name in ("p7-dense","p7-guided"):
    part=next(x for x in self.methods[name]["frames"] if x["angle"]==angle)
    self.assertTrue(np.array_equal(pixels,rgba(ASSETS/part["path"])),(name,angle))

 def test_37_frame_source_metadata_preserves_method_provenance(self):
  for method,folder in (("p7-dense","full-sequence"),("p7-guided","guided-sequence")):
   qa=get(P7/folder/"canvas-qa.json")
   self.assertEqual(qa["characterId"],"p0_character_001")
   self.assertEqual(qa["status"],"SOURCE_DERIVED_RGBA_FRAMES_CAPTURED")
   self.assertEqual(qa["sourceKind"],"OFFLINE_P0_SEMANTIC_FLOW_TEXTURE")
   self.assertEqual(qa["frameCount"],37)
   for rec in qa["outputs"]:
    self.assertEqual(sha(rec["path"]),rec["sha256"])

 def test_heldout_face_coverage_and_high_frequency_edges(self):
  for method in ("p7-dense","p7-guided"):
   record=self.methods[method]
   self.assertEqual(record["textureStatus"],"PASS_TEXTURE_EDGE_DIAGNOSTIC")
   self.assertLess(record["textureRatios"]["22.5"],1.8)
   self.assertLess(record["textureRatios"]["67.5"],1.8)
  for folder in ("guided-sequence","source-selection"):
   self.assertEqual(get(P7/folder/"holdout-qa.json")["status"],
                    "PASS_HOLDOUT_COVERAGE")

 def test_temporal_full_sequence_is_independently_audited(self):
  self.assertEqual(self.methods["p7-guided"]["temporalStatus"],
                   "PASS_TEMPORAL_CONTINUITY")
  self.assertEqual(self.methods["p7-guided"]["temporalOutliers"],0)
  self.assertLess(self.methods["p7-guided"]["maxAdjacentDifference"],6.5)
  self.assertGreater(self.methods["p7-dense"]["temporalOutliers"],0)
  self.assertGreater(self.methods["p6-mesh"]["temporalOutliers"],0)

 def test_real_html_browser_6_views_18_pixel_exact_canvases(self):
  b=self.browser
  self.assertEqual(b["characterId"],"p0_character_001")
  self.assertEqual(b["status"],"PASS_REAL_BROWSER_TEXTURE_PREVIEW")
  self.assertEqual(len(b["screens"]),6)
  self.assertFalse(b["errors"])
  self.assertFalse(b["failedRequests"])
  self.assertEqual(b["initial"]["methodCount"],3)
  self.assertEqual(b["initial"]["frameCount"],37)
  for shot in b["screens"]:
   self.assertEqual(sha(shot["path"]),shot["sha256"])
   self.assertEqual(len(shot["canvases"]),3)
   for canvas in shot["canvases"]:
    self.assertEqual(sha(canvas["path"]),canvas["sha256"])
    frame=next(x for x in self.methods[canvas["method"]]["frames"]
               if x["angle"]==shot["yaw"])
    actual=rgba(canvas["path"]).astype(np.int16)
    source=rgba(ASSETS/frame["path"]).astype(np.int16)
    delta=np.abs(actual-source)
    opaque=(actual[:,:,3]==255)&(source[:,:,3]==255)
    # Browser 2D canvas stores RGB premultiplied by partial alpha,
    # with up to a few byte values of round-trip edge quantization.
    # Opaque source color and all alpha values must remain identical.
    self.assertEqual(int(delta[:,:,3].max()),0)
    self.assertEqual(int(delta[:,:,:3][opaque].max()),0)
    self.assertLessEqual(int(delta[:,:,:3].max()),10)
    self.assertLess(float(delta[:,:,:3].mean()),0.06)

 def test_two_real_source_rgba_motion_gifs(self):
  for name,qa_file in (("p0-semantic-dense-turn.gif","p0-semantic-dense-turn.qa.json"),
                       ("p0-semantic-guided-turn.gif","p0-semantic-guided-turn.qa.json")):
   record=get(P7/qa_file)
   self.assertEqual(record["characterId"],"p0_character_001")
   self.assertEqual(record["status"],"SOURCE_DERIVED_RGBA_FRAMES_PACKAGED")
   self.assertEqual(record["sourceFrameCount"],37)
   self.assertEqual(record["GIFFrames"],72)
   self.assertEqual(record["GIFSHA256"],sha(P7/name))
   with Image.open(P7/name) as im:
    self.assertEqual(im.n_frames,72)

 @unittest.skipUnless((P7/"p7-package-qa.json").is_file(),
                     "P7 privacy-preserving review archive exists")
 def test_p7_source_archive_crc_and_sha(self):
  qa=get(P7/"p7-package-qa.json")
  self.assertEqual(qa["characterId"],"p0_character_001")
  file=Path(qa["archivePath"])
  self.assertEqual(sha(file),qa["sha256"])
  self.assertTrue(qa["internalHashesVerified"])
  with zipfile.ZipFile(file) as z:
   self.assertIsNone(z.testzip())
   metadata=json.loads(z.read("package-manifest.json"))
   self.assertEqual(metadata["characterId"],"p0_character_001")
   self.assertEqual(metadata["sourcePNGCount"],111)
   self.assertEqual(metadata["registeredSemanticArtMeshes"],39)
   self.assertEqual(metadata["QAState"],"PENDING_ANIME_ARTISTIC_APPROVAL")

if __name__=="__main__":
 unittest.main(verbosity=2)
