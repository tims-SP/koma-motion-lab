import hashlib,json,tempfile,unittest,pathlib,sys
from PIL import Image,ImageDraw
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
import importlib.util
spec=importlib.util.spec_from_file_location("view_asset_validator",pathlib.Path(__file__).resolve().parents[1]/"scripts/validate-view-layers.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=json.loads((ROOT/"assets/view-key-contract.json").read_text())

def make_test_file(root,angle,part):
 p=root/f"{angle}-{part}.png"
 im=Image.new("RGBA",(640,640),(0,0,0,0))
 draw=ImageDraw.Draw(im)
 j=sum(ord(c) for c in part)
 draw.polygon([(180+(j%25),170+angle//3),(365+(j%35),180+angle//3),(280+j%30,370+angle//3)],fill=(100+j%120,60,80,255))
 im.save(p)
 return {"yawDeg":angle,"semanticId":part,"role":"independent_art","path":p.name,
  "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"creator":"synthetic-test-suite",
  "sourceId":f"fixture-{angle}-{part}","licenseReview":"self-authored synthetic",
  "cameraCalibrated":True,"landmarks":{"a":[180,175],"b":[365,185],"c":[280,370]}}

class TestArtworkGate(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.folder.name)
  self.manifest=json.loads(json.dumps(BASE))
 def tearDown(self):self.folder.cleanup()
 def complete(self):
  self.manifest["assets"]=[make_test_file(self.root,a,p) for a in [45,90] for p in BASE["requiredParts"]]
 def test_empty_sources_are_reported_without_false_visual_pass(self):
  result=module.validate(self.manifest,self.root)
  self.assertFalse(result["readyForInterpolation"])
  self.assertEqual(len(result["missingIndependent"]),16)
  self.assertEqual(result["errors"],[])
 def test_every_part_authored_and_alpha_provenance_complete(self):
  self.complete();result=module.validate(self.manifest,self.root)
  self.assertTrue(result["readyForInterpolation"],result["errors"])
  self.assertEqual(result["coverage"],16)
 def test_missing_side_part_detected(self):
  self.complete();self.manifest["assets"].pop()
  self.assertEqual(len(module.validate(self.manifest,self.root)["missingIndependent"]),1)
 def test_tampering_and_opaque_image_rejected(self):
  self.complete();item=self.manifest["assets"][0]
  p=self.root/item["path"];Image.new("RGB",(640,640),(255,255,255)).save(p)
  result=module.validate(self.manifest,self.root)
  self.assertIn("HASH_0:45:face.skin",result["errors"])
  self.assertIn("RGBA_0:45:face.skin",result["errors"])
 def test_duplicate_view_image_hash_rejected(self):
  self.complete()
  a=self.manifest["assets"][0];b=next(x for x in self.manifest["assets"] if x["yawDeg"]==90 and x["semanticId"]==a["semanticId"])
  pathlib.Path(self.root/b["path"]).write_bytes((self.root/a["path"]).read_bytes())
  b["sha256"]=a["sha256"]
  self.assertTrue(any(x.startswith("CROSS_VIEW_REUSE") for x in module.validate(self.manifest,self.root)["errors"]))
 def test_unsafe_paths_rejected(self):
  self.complete();self.manifest["assets"][0]["path"]="../private.png"
  self.assertTrue(any(x.startswith("UNSAFE_PATH") for x in module.validate(self.manifest,self.root)["errors"]))
 def test_landmarks_must_form_area(self):
  self.complete();self.manifest["assets"][0]["landmarks"]={"a":[1,1],"b":[2,2],"c":[3,3]}
  self.assertTrue(any(x.startswith("LANDMARK_COLLINEAR") for x in module.validate(self.manifest,self.root)["errors"]))
if __name__=="__main__":unittest.main()
