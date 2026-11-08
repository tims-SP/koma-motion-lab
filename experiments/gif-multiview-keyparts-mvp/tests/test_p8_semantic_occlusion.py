#!/usr/bin/env python3
"""P0 original 2.75D ArtMesh source correspondence, visibility and browser QA."""
import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image

EXP=Path(__file__).resolve().parents[1]
A=EXP/"private-assets"
P=A/"p8-semantic-occlusion"
P5=A/"p5-see-through/mv-candidate"
P7=A/"p7-semantic-dense"

def load(file):
 return json.loads(Path(file).read_text(encoding="utf-8"))

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def rgba(file):
 with Image.open(file) as im:
  assert im.size==(1024,1024) and im.mode=="RGBA"
  return np.asarray(im).copy()

@unittest.skipUnless((P/"viewer-manifest.json").is_file(),"Private original P0 P8 outputs")
class P8AnatomicalOcclusion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=load(P/"viewer-manifest.json")
  cls.qa=load(P/"selective-sequence/qa.json")
  cls.browser=load(P/"browser/browser-qa.json")
  cls.sequence={m["id"]:m for m in cls.manifest["methods"]}

 def test_original_P0_semantic_identity_and_views(self):
  self.assertEqual(self.manifest["schema"],"KOMA-P0-P8-SEMANTIC-OCCLUSION-VIEWER-V1")
  self.assertEqual(self.manifest["characterId"],"p0_character_001")
  self.assertEqual(self.manifest["originalKeyAngles"],[0,45,90])
  self.assertEqual(self.manifest["sourcePSDViews"],[0,45])
  self.assertEqual(self.manifest["canvas"],[1024,1024])
  self.assertEqual(self.manifest["registeredArtMeshSlots"],39)
  self.assertEqual(self.manifest["artisticAcceptance"],"PENDING")

 def test_registered_native_111_RGBA_and_sha(self):
  self.assertEqual(set(self.sequence),{"p6-mesh","p7-guided","p8-selective"})
  self.assertEqual(sum(len(m["frames"]) for m in self.sequence.values()),111)
  for method in self.sequence.values():
   self.assertEqual(len(method["frames"]),37)
   for idx,frame in enumerate(method["frames"]):
    self.assertEqual(frame["angle"],idx*2.5)
    source=A/frame["path"]
    self.assertEqual(frame["sha256"],sha(source))
    self.assertEqual(frame["bytes"],source.stat().st_size)
    with Image.open(source) as im:
     self.assertEqual(im.mode,"RGBA")
     self.assertEqual(im.size,(1024,1024))

 def test_0_45_90_original_P0_pixels_immutable(self):
  references={int(x["angle"]):x for x in self.manifest["authoritativeOriginalFrames"]}
  for yaw in (0,45,90):
   orig=A/references[yaw]["path"]
   self.assertEqual(sha(orig),references[yaw]["sha256"])
   target=next(x for x in self.sequence["p8-selective"]["frames"] if x["angle"]==yaw)
   self.assertTrue(np.array_equal(rgba(orig),rgba(A/target["path"])),yaw)

 def test_guided_local_semantic_correspondence_provenance(self):
  self.assertEqual(self.qa["characterId"],"p0_character_001")
  self.assertEqual(self.qa["mode"],"selective")
  self.assertEqual(self.qa["registeredArtMeshViews"],39)
  self.assertEqual(self.qa["sourceAngles"],[0,45,90])
  self.assertEqual(self.qa["sourcePSDViews"],[0,45])
  self.assertEqual(len(self.qa["frames"]),37)
  self.assertEqual(len(self.qa["pairDiagnostics"]),22)
  self.assertEqual(self.qa["inputRegistrySHA256"],sha(P5/"parts.json"))
  self.assertEqual(self.qa["inputLandmarksSHA256"],sha(P5/"landmark-qa.json"))
  roles=[x["semanticId"] for x in load(P5/"parts.json")["parts"] if x["yawDeg"]==0]
  self.assertEqual(len(set(roles)),13)

 def test_semantic_occlusion_windows_valid(self):
  windows={(r["pair"][0],r["pair"][1],r["semanticId"]):r["visibilityWindow"]
           for r in self.qa["occlusionWindows"]}
  self.assertEqual(set(windows),{
   (0,45,"ear.far"),(45,90,"eye.far"),(45,90,"hair.clip.cross_gold")})
  for (a,b,_),times in windows.items():
   self.assertLess(a,times[0])
   self.assertLess(times[0],times[1])
   self.assertLess(times[1],b)
  import sys
  sys.path.insert(0,str(EXP/"scripts"))
  from p8_semantic_occlusion import schedule_visibility
  self.assertLess(schedule_visibility("hair.clip.cross_gold",45,90,67.5),0.20)
  self.assertEqual(schedule_visibility("eye.far",45,90,90),0)
  self.assertEqual(schedule_visibility("ear.far",0,45,45),0)

 def test_holdout_texture_and_face_alpha(self):
  texture=load(P/"selective-sequence/texture-qa.json")
  coverage=load(P/"selective-holdout/holdout-qa.json")
  self.assertEqual(texture["status"],"PASS_TEXTURE_EDGE_DIAGNOSTIC")
  self.assertEqual(texture["failed"],0)
  self.assertEqual(coverage["status"],"PASS_HOLDOUT_COVERAGE")
  ratios={v["angle"]:v["edgeDensityRelativeToAdjacentMax"] for v in texture["holdouts"]}
  self.assertLess(ratios[22.5],1.8)
  self.assertLess(ratios[67.5],1.8)

 def test_source_temporal_continuity_37_frames(self):
  qa=load(P/"selective-sequence/temporal-qa.json")
  self.assertEqual(qa["angles"],37)
  self.assertEqual(qa["status"],"PASS_TEMPORAL_CONTINUITY")
  self.assertEqual(len(qa["outliers"]),0)
  self.assertLess(qa["maxAdjacentMeanRGBDelta"],6.5)

 def test_real_chromium_6_angles_18_canvas_captures(self):
  browser=self.browser
  self.assertEqual(browser["status"],"PASS_REAL_BROWSER_TEXTURE_PREVIEW")
  self.assertEqual(browser["characterId"],"p0_character_001")
  self.assertEqual(len(browser["screens"]),6)
  self.assertEqual(browser["initial"]["methodCount"],3)
  self.assertEqual(browser["initial"]["frameCount"],37)
  self.assertFalse(browser["errors"])
  self.assertFalse(browser["failedRequests"])
  for shot in browser["screens"]:
   self.assertEqual(sha(shot["path"]),shot["sha256"])
   self.assertEqual(len(shot["canvases"]),3)
   for p in shot["canvases"]:
    self.assertEqual(sha(p["path"]),p["sha256"])
    expected=next(f for f in self.sequence[p["method"]]["frames"] if f["angle"]==shot["yaw"])
    image=rgba(p["path"]).astype(np.int16)
    reference=rgba(A/expected["path"]).astype(np.int16)
    diff=np.abs(image-reference)
    opaque=(image[:,:,3]==255)&(reference[:,:,3]==255)
    self.assertEqual(int(diff[:,:,3].max()),0)
    self.assertEqual(int(diff[:,:,:3][opaque].max()),0)
    self.assertLessEqual(int(diff[:,:,:3].max()),10)
    self.assertLess(float(diff[:,:,:3].mean()),0.06)

 def test_72_frame_source_gif_and_sha(self):
  gif=P/"p0-semantic-occlusion-turn.gif"
  qa=load(P/"p0-semantic-occlusion-turn.qa.json")
  self.assertEqual(qa["characterId"],"p0_character_001")
  self.assertEqual(qa["sourceFrameCount"],37)
  self.assertEqual(qa["GIFFrames"],72)
  self.assertEqual(qa["GIFSHA256"],sha(gif))
  with Image.open(gif) as im:
   self.assertEqual(im.n_frames,72)
   self.assertEqual(im.size,(512,512))

 @unittest.skipUnless((P/"p8-package-qa.json").is_file(),"P8 source package not yet created")
 def test_private_review_archive_sha_crc(self):
  qa=load(P/"p8-package-qa.json")
  self.assertEqual(qa["characterId"],"p0_character_001")
  self.assertTrue(qa["internalHashesVerified"])
  self.assertEqual(sha(qa["archivePath"]),qa["sha256"])
  with zipfile.ZipFile(qa["archivePath"]) as z:
   self.assertIsNone(z.testzip())
   manifest=json.loads(z.read("package-manifest.json"))
   self.assertEqual(manifest["characterId"],"p0_character_001")
   self.assertEqual(manifest["registeredArtMeshViews"],39)
   self.assertEqual(manifest["registeredSourceRGBAFrames"],111)

if __name__=="__main__":
 unittest.main(verbosity=2)
