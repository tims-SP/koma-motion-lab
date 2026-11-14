"""P15-38 original P0 45°–65° layered camera arc regression."""
import json,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
import p15_38_extend_p0_arc as arc
import p15_38_review as review

class P15_38_P0Arc(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.qa=json.loads(arc.QA.read_text())
  cls.ref=json.loads(arc.SOURCE_QA.read_text())
  cls.browser=json.loads((arc.R/"evidence/p15-38-browser-qa.json").read_text())
  cls.visual=json.loads(review.QA.read_text())

 def test_original_p0_45_source_identity(self):
  self.assertEqual(self.qa["characterId"],"p0_character_001")
  self.assertEqual(self.qa["sourceOriginal45"]["sourceP0SHA256"],arc.sha(arc.P0))
  self.assertAlmostEqual(self.qa["sourceOriginal45"]["alphaIoUWithApprovedOriginal"],1.,delta=1e-6)
  self.assertLess(self.qa["sourceOriginal45"]["meanRGBDeltaOnSharedOpaquePixels"],.03)
  self.assertEqual(self.qa["sourceOriginal45"]["registeredRoleCount"],13)

 def test_registered_thirteen_yaw_frames(self):
  self.assertEqual(self.qa["angles"],arc.KEYS+arc.TAIL)
  self.assertEqual(len(self.qa["frames"]),13)
  self.assertEqual(self.qa["roleCount"],13)
  self.assertEqual(self.qa["interpolatedNewAngles"],[47.5,50.,52.5])
  for f in self.qa["frames"]:
   self.assertEqual(f["roleCount"],13)
   self.assertEqual(set(f["roles"]),set(arc.ROLES))

 def test_exact_p0_45_reference_composite(self):
  self.assertEqual((arc.OUT/"yaw45/composite.png").read_bytes(),arc.P0.read_bytes())
  f=self.qa["frames"][0]
  self.assertTrue(f["P0SourceOriginalByteExact"])
  for role in arc.ROLES:
   file=arc.OUT/"yaw45"/(role+".png")
   self.assertEqual(arc.sha(file),f["roles"][role]["sha256"])

 def test_p15_37_55_to65_byte_exact(self):
  for yaw in [55.]+arc.TAIL:
   d=arc.OUT/arc.slug(yaw);old=arc.PAINTED/arc.slug(yaw)
   for role in arc.ROLES:
    self.assertEqual((d/(role+".png")).read_bytes(),(old/(role+".png")).read_bytes())
   self.assertEqual((d/"composite.png").read_bytes(),(old/"composite.png").read_bytes())
   self.assertEqual((d/"composite-native.png").read_bytes(),(old/"composite-native.png").read_bytes())

 def test_three_inbetween_semantic_views(self):
  for yaw in [47.5,50.,52.5]:
   d=arc.OUT/arc.slug(yaw)
   frame=next(x for x in self.qa["frames"] if x["yaw"]==yaw)
   self.assertEqual(frame["kind"],"cross-view-role-inbetween")
   self.assertNotEqual(arc.sha(d/"composite.png"),arc.sha(arc.P0))
   self.assertNotEqual(arc.sha(d/"composite.png"),
                       arc.sha(arc.PAINTED/"yaw55/composite.png"))
   for role in arc.ROLES:
    self.assertTrue((d/(role+".png")).is_file())
    with Image.open(d/(role+".png")) as im:
     self.assertEqual(im.size,(443,443))
     self.assertEqual(im.mode,"RGBA")
    self.assertEqual(arc.sha(d/(role+".png")),frame["roles"][role]["sha256"])

 def test_source_art_trace_is_local_and_hashed(self):
  for yaw in [45.,47.5,50.,52.5,55.]:
   row=next(x for x in self.qa["frames"] if x["yaw"]==yaw)
   for role in arc.ROLES:
    rec=row["roles"][role]
    self.assertEqual(rec["source45SHA256"],arc.sha(arc.CANONICAL/(role+".png")))
    self.assertEqual(rec["source55SHA256"],
                      arc.sha(arc.PAINTED/"yaw55"/(role+".png")))
    self.assertFalse(rec["independentNewKeyframe"])

 def test_eye_clip_anchor_geometric_continuity(self):
  for role in ("eye.far","eye.near","hair.clip.cross_gold","hair.side"):
   coordinates=[]
   for yaw in arc.KEYS:
    p=arc.OUT/arc.slug(yaw)/(role+".png")
    alpha=arc.read(p)[:,:,3].astype(np.float32)/255
    yy,xx=np.indices(alpha.shape)
    mass=float(alpha.sum())
    self.assertGreater(mass,50)
    coordinates.append([(alpha*xx).sum()/mass,(alpha*yy).sum()/mass])
   for a,b in zip(coordinates,coordinates[1:]):
    self.assertLess(np.linalg.norm(np.array(a)-np.array(b)),15,(role,a,b))

 def test_adjacent_45_to65_alpha_and_rgb_proxy(self):
  rows=self.qa["adjacentMetrics"]
  self.assertEqual(len(rows),12)
  for rec in rows:
   self.assertGreater(rec["alphaIoU"],.95)
   self.assertTrue(np.isfinite(rec["sharedVisibleRGBDelta"]))
   self.assertLess(rec["sharedVisibleRGBDelta"],30.)

 def test_viewer_original_art_sources_exact(self):
  self.assertEqual(self.visual["sourceOriginal45SHA256"],
                   arc.sha(review.OUT/"p0-yaw45-original.png"))
  self.assertEqual(self.visual["angles"],self.qa["angles"])
  self.assertEqual(len(self.visual["frames"]),13)
  for f in self.visual["frames"]:
   self.assertEqual(len(f["sourceImages"]),9)
   for filename,h in f["sourceImages"].items():
    self.assertEqual(arc.sha(review.OUT/f["dir"]/filename),h)

 def test_chromium_desktop_mobile_13frames(self):
  b=self.browser
  self.assertEqual(b["status"],"P15_38_ORIGINAL_P0_EXTENDED_ARTMESH_HTML_VERIFIED")
  self.assertEqual(b["viewportChecks"],78)
  self.assertEqual(b["imageLoads"],312)
  self.assertEqual(b["screenshotCount"],12)
  self.assertEqual(b["errors"],[])
  self.assertEqual(b["failedRequests"],[])
  self.assertEqual({x["viewport"] for x in b["checks"]},{"desktop","mobile"})
  for f in b["screenshots"]:
   self.assertEqual(arc.sha(ROOT/f["path"]),f["sha256"])

 def test_keyframe_canvas_and_registered_rgba(self):
  for f in self.qa["frames"]:
   folder=arc.OUT/arc.slug(f["yaw"])
   with Image.open(folder/"composite.png") as im:
    self.assertEqual(im.size,(1024,1024))
    self.assertEqual(im.mode,"RGBA")
   with Image.open(folder/"composite-native.png") as im:
    self.assertEqual(im.size,(443,443))
    self.assertEqual(im.mode,"RGBA")

 def test_artistic_release_gates_remain_independent(self):
  self.assertEqual(self.qa["fullIndependentArtAdmission"],0)
  self.assertEqual(self.qa["independentHiddenUnderpaintAdmission"],0)
  self.assertFalse(self.qa["sourceP0HeroSHA256Verified"])
  self.assertFalse(self.qa["physical3DTopologyApproved"])
  self.assertFalse(self.qa["productionRendererModified"])
  self.assertFalse(self.visual["fullArtistAcceptance"])

if __name__=="__main__":unittest.main()
