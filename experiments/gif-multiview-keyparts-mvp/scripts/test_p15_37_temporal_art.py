"""P15-37 P0 keypart provenance, RGBA and continuous review regression."""
import json,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
import p15_37_temporal_paint_vdd as vdd
import p15_37_review as review

class P15_37_PaintedContinuity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.qa=json.loads(vdd.QA.read_text())
  cls.earlier=json.loads(vdd.Q36.read_text())
  cls.review=json.loads(review.QA.read_text())
  cls.browser=json.loads((vdd.R/"evidence/p15-37-browser-qa.json").read_text())

 def test_character_original_source_lock(self):
  self.assertEqual(self.qa["characterId"],"p0_character_001")
  self.assertEqual(self.qa["sourceP15_35SHA256"],vdd.sha(vdd.Q35))
  self.assertEqual(self.qa["sourceP15_36SHA256"],vdd.sha(vdd.Q36))
  self.assertEqual(self.qa["sourceP15_12CameraSHA256"],vdd.sha(vdd.QCAM))
  self.assertEqual(self.qa["sourceP0Original45SHA256"],
    vdd.sha(vdd.P/"p2-views/whole/yaw045.png"))

 def test_source_keyangles_and_role_ownership(self):
  self.assertEqual(self.qa["angles"],list(vdd.ANG))
  self.assertEqual(len(self.qa["roles"]),13)
  self.assertEqual(set(self.qa["paintedRoles"]),set(vdd.PAINT_ROLES))
  self.assertEqual(self.qa["sourceEndpointsExact"],[55.,65.])
  self.assertEqual(self.qa["modelPaintedKeysExact"],[57.5,60.])
  for f in self.qa["frames"]:
   self.assertEqual(set(f["roles"]),set(vdd.ROLES))
   self.assertEqual(f["sourceCompositeSHA256"],vdd.sha(vdd.BASE/vdd.slug(f["yaw"])/"composite.png"))
   self.assertEqual(f["outputCompositeSHA256"],vdd.sha(vdd.OUT/vdd.slug(f["yaw"])/"composite.png"))

 def test_endpoints_preserve_every_source_role(self):
  for yaw in (55.,65.):
   f=next(r for r in self.qa["frames"] if r["yaw"]==yaw)
   self.assertEqual(f["changedCompositePixels"],0)
   self.assertEqual(f["paintWeight"],0.)
   for role in vdd.ROLES:
    self.assertEqual((vdd.OUT/vdd.slug(yaw)/(role+".png")).read_bytes(),
                     (vdd.BASE/vdd.slug(yaw)/(role+".png")).read_bytes())

 def test_painted_57_and_60_source_art_exact(self):
  for yaw in (57.5,60.):
   f=next(r for r in self.qa["frames"] if r["yaw"]==yaw)
   self.assertEqual(f["kind"],"painted-keyframe")
   self.assertEqual(f["paintWeight"],1.)
   for role in vdd.ROLES:
    left=(vdd.OUT/vdd.slug(yaw)/(role+".png")).read_bytes()
    right=(vdd.NEW/vdd.slug(yaw)/(role+".png")).read_bytes()
    self.assertEqual(left,right)

 def test_all_other_roles_are_source_exact(self):
  for f in self.qa["frames"]:
   name=vdd.slug(f["yaw"])
   for role in vdd.UNMODIFIED:
    self.assertEqual((vdd.BASE/name/(role+".png")).read_bytes(),
                     (vdd.OUT/name/(role+".png")).read_bytes(),(role,name))

 def test_interpolated_paint_trace(self):
  mids=[f for f in self.qa["frames"] if f["kind"]=="paint-inbetween"]
  self.assertEqual(len(mids),5)
  for f in mids:
   self.assertGreater(f["changedCompositePixels"],300)
   self.assertGreater(f["paintWeight"],0.)
   self.assertLessEqual(f["paintWeight"],1.)
   total=sum(x["weight"] for x in f["paintSources"])
   self.assertAlmostEqual(total,1.,delta=1e-5)
   for role in vdd.PAINT_ROLES:
    row=f["roles"][role]
    self.assertEqual(row["method"],"p5-registered-painted-local-interpolation")
    self.assertGreater(len(row["paintSources"]),0)
    for p in row["paintSources"]:
     key=vdd.slug(p["yaw"])
     self.assertEqual(p["sourceSHA256"],
          vdd.sha(vdd.NEW/key/(role+".donor-paint.png")))

 def test_hidden_rgba_source_is_preserved(self):
  for f in self.qa["frames"]:
   d=vdd.slug(f["yaw"])
   for name in ("eye.far.original.png","eye.far.hidden-underpaint.png"):
    self.assertEqual((vdd.BASE/d/name).read_bytes(),(vdd.OUT/d/name).read_bytes())
   self.assertGreater(f["hiddenEyeSourceAlphaMass"],40.)

 def test_role_composition_has_native_and_full_canvas(self):
  for f in self.qa["frames"]:
   folder=vdd.OUT/vdd.slug(f["yaw"])
   with Image.open(folder/"composite-native.png") as p:
    self.assertEqual(p.size,(443,443))
    self.assertEqual(p.mode,"RGBA")
   with Image.open(folder/"composite.png") as p:
    self.assertEqual(p.size,(1024,1024))
    self.assertEqual(p.mode,"RGBA")
   for role in vdd.ROLES:
    with Image.open(folder/(role+".png")) as im:
     self.assertEqual(im.size,(443,443))
     self.assertEqual(im.mode,"RGBA")

 def test_temporal_rgb_jump_probes(self):
  hops=self.qa["adjacentMetrics"]
  self.assertEqual(len(hops),8)
  for h in hops:
   self.assertGreater(h["sourceLocalRGBJump"],0)
   self.assertTrue(np.isfinite(h["localRGBJump"]))
   # Engineering spike guard, NOT independent animation quality score.
   self.assertLess(h["localRGBJump"],h["sourceLocalRGBJump"]*1.6)
   self.assertGreaterEqual(h["clipContactDifference"],0.)

 def test_paint_source_and_user_review_images_hashed(self):
  self.assertEqual(len(self.review["frames"]),9)
  self.assertEqual(self.review["sourceP0_45SHA256"],
    vdd.sha(review.OUT/"p0-45-identity.png"))
  for r in self.review["frames"]:
   folder=review.OUT/r["slug"]
   self.assertEqual(len(r["sources"]),10)
   for filename,digest in r["sources"].items():
    self.assertEqual(digest,vdd.sha(folder/filename))

 def test_chromium_desktop_mobile_modes(self):
  b=self.browser
  self.assertEqual(b["status"],"P15_37_NINE_FRAME_THREE_MODE_CHROMIUM_VERIFIED")
  self.assertEqual(b["viewportChecks"],54)
  self.assertEqual(b["imageLoads"],216)
  self.assertEqual(b["screenshotCount"],10)
  self.assertEqual(b["errors"],[])
  self.assertEqual(b["failedRequests"],[])
  self.assertEqual({p["viewport"] for p in b["checks"]},{"desktop","mobile"})
  for x in b["screenshots"]:
   self.assertEqual(vdd.sha(ROOT/x["path"]),x["sha256"])

 def test_independent_artistic_gates(self):
  self.assertEqual(self.qa["fullKeyViewsArtApproved"],0)
  self.assertEqual(self.qa["independentHiddenUnderpaintApproved"],0)
  self.assertFalse(self.qa["P0HeroApprovedSourceSHA256Verified"])
  self.assertFalse(self.qa["occludedInkAnatomyApproved"])
  self.assertFalse(self.qa["productionVddModified"])
  self.assertFalse(self.review["formalArtistApproval"])

if __name__=="__main__":unittest.main()
