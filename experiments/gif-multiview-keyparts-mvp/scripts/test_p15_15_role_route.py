#!/usr/bin/env python3
import unittest,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/"private-assets"
class Roles(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((ROOT/"evidence/p15-15-role-routing-qa.json").read_text())
  cls.native=json.loads((ROOT/"evidence/p15-14-existing-psd-mapping-qa.json").read_text())
 def test_registry(self):
  self.assertEqual(self.q["roleCount"],13)
  self.assertEqual(len(self.q["views"]),3)
  self.assertEqual(sum(len(v["roles"]) for v in self.q["views"]),39)
 def test_source_hash(self):
  raw=ROOT/"evidence/p15-14-existing-psd-mapping-qa.json"
  self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),self.q["sourceSHA256"])
 def test_all_outputs(self):
  for v in self.q["views"]:
   self.assertEqual(len(v["roles"]),13)
   for item in v["roles"]:
    f=P/item["path"];self.assertTrue(f.exists())
    self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),item["sha256"])
    with Image.open(f) as im:self.assertEqual(im.size,(768,768))
 def test_native_split_conservation(self):
  for v,source in zip(self.q["views"],self.native["sources"]):
   by_index={}
   for part in v["nativeComponents"]:
    by_index.setdefault(part["index"],[]).append(part)
   for native in source["nativeLayerEntries"]:
    if "path" not in native:continue
    a=np.array(Image.open(P/native["path"]).convert("RGBA"))
    arr=[np.array(Image.open(P/p["file"]).convert("RGBA")) for p in by_index[native["index"]]]
    reconstructed=np.maximum.reduce(arr)
    self.assertTrue(np.array_equal(a,reconstructed),(v["yaw"],native["name"]))
 def test_do_not_promote_art(self):
  self.assertFalse(self.q["artisticAcceptance"])
  self.assertEqual(self.q["acceptedIndependentArtMeshLayers"],0)
  self.assertFalse(self.q["validUnderpaintAccepted"])
  self.assertTrue(all(v["missingOrNonIndependentRoles"] for v in self.q["views"]))
if __name__=="__main__":unittest.main()
