#!/usr/bin/env python3
"""P11 P0 source-profile 13-layer PSD and real original image verification."""
import hashlib,json,unittest,zipfile
from pathlib import Path
from PIL import Image
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"private-assets"
P11=ASSETS/"p11-profile-psd/yaw090"
P5=ASSETS/"p5-see-through/mv-candidate"

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def get(p):return json.loads(Path(p).read_text(encoding="utf8"))

@unittest.skipUnless((P11/"qa.json").is_file(),"Real original 90-degree source PSD")
class P11RegisteredProfilePSD(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.qa=get(P11/"qa.json")
  cls.registry=get(P5/"parts.json")
  cls.files=sorted((p for p in cls.registry["parts"] if p["yawDeg"]==90),
                   key=lambda x:x["depthOrder"])

 def test_source_identity_and_canvas(self):
  qa=self.qa
  self.assertEqual(qa["schema"],"KOMA-P0-P11-EDITABLE-PROFILE-PSD-ORIGINAL-LAYERS-V1")
  self.assertEqual(qa["characterId"],"p0_character_001")
  self.assertEqual(qa["angle"],90)
  self.assertEqual(qa["globalCanvas"],[1024,1024])
  self.assertEqual(qa["nativeLayerCount"],13)
  self.assertEqual(qa["sourcePartsRegistrySHA256"],sha(P5/"parts.json"))

 def test_each_semantic_source_and_sha(self):
  self.assertEqual(len(self.files),13)
  self.assertEqual([x["depthOrder"] for x in self.files],list(range(13)))
  for p,q in zip(self.files,self.qa["layers"]):
   self.assertEqual(p["semanticId"],q["semanticId"])
   self.assertEqual(p["frameSha256"],q["sourceSHA256"])
   self.assertEqual(p["visibility"],q["visibility"])
   self.assertEqual(sha(ASSETS/p["path"]),p["frameSha256"])
   with Image.open(ASSETS/p["path"]) as img:
    self.assertEqual(img.mode,"RGBA")
    self.assertEqual(img.size,(1024,1024))
   self.assertTrue(q["originalAlphaExact"])
   self.assertLessEqual(q["maximumVisibleColorRoundTripDifference"],1)

 def test_profile_hidden_semantic_parts(self):
  hidden={x["semanticId"] for x in self.files if x["visibility"]=="hidden"}
  self.assertEqual(hidden,{"ear.far","eye.far","hair.clip.cross_gold"})
  for item in self.files:
   if item["semanticId"] in hidden:
    self.assertEqual(np.max(np.array(Image.open(ASSETS/item["path"]))[:,:,3]),0)

 def test_real_RGBA_semantic_composition_pixel_exact(self):
  merged=Image.new("RGBA",(1024,1024),(0,0,0,0))
  for layer in self.files:
   with Image.open(ASSETS/layer["path"]) as im:
    merged.alpha_composite(im.convert("RGBA"))
  whole=next(p for p in self.registry["wholeViews"] if p["yawDeg"]==90)
  self.assertEqual(sha(ASSETS/whole["path"]),whole["sha256"])
  self.assertEqual(self.qa["sourceCanonicalSHA256"],whole["sha256"])
  with Image.open(ASSETS/whole["path"]) as im:
   self.assertTrue(np.array_equal(np.asarray(merged),np.asarray(im.convert("RGBA"))))
  with Image.open(ASSETS/self.qa["sourceRGBAPreviewPath"]) as preview:
   self.assertTrue(np.array_equal(np.asarray(merged),np.asarray(preview.convert("RGBA"))))

 def test_real_PSD_binary_and_sha(self):
  p=ASSETS/self.qa["psdPath"]
  self.assertEqual(sha(p),self.qa["psdSHA256"])
  self.assertEqual(p.stat().st_size,self.qa["psdBytes"])
  with p.open("rb") as f:
   self.assertEqual(f.read(4),b"8BPS")
  self.assertEqual(self.qa["PSDCompositeAlphaMaxDifference"],0)
  self.assertLessEqual(self.qa["PSDCompositeVisibleColorMaxDifference"],1)

 def test_side_by_side_view_and_source_SHA(self):
  for key,pathkey in (("sourceRGBAPreviewSHA256","sourceRGBAPreviewPath"),
                      ("PSDCompositeSHA256","PSDCompositePath"),
                      ("sourceComparisonSHA256","sourceComparisonPath")):
   self.assertEqual(sha(ASSETS/self.qa[pathkey]),self.qa[key])
  with Image.open(ASSETS/self.qa["sourceComparisonPath"]) as image:
   self.assertEqual(image.size,(1040,570))

 @unittest.skipUnless((P11/"package-qa.json").is_file(),"P11 source archive pending")
 def test_three_view_psd_original_source_archive(self):
  qa=get(P11/"package-qa.json")
  self.assertEqual(qa["characterId"],"p0_character_001")
  self.assertEqual(qa["PSDViewAngles"],[0,45,90])
  self.assertEqual(qa["yaw90OriginalSemanticLayers"],13)
  self.assertEqual(qa["sourceArtMeshViewSlots"],39)
  self.assertTrue(qa["internalHashesVerified"])
  self.assertEqual(sha(qa["archivePath"]),qa["sha256"])
  with zipfile.ZipFile(qa["archivePath"]) as z:
   self.assertIsNone(z.testzip())
   manifest=json.loads(z.read("package-manifest.json"))
   self.assertEqual(manifest["characterId"],"p0_character_001")
   self.assertEqual(manifest["originalAuthoredViews"],[0,45,90])

if __name__=="__main__":
 unittest.main(verbosity=2)
