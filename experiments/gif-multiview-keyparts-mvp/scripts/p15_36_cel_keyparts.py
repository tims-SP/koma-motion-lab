#!/usr/bin/env python3
"""P15-36 source-registered cel retouch of 57.5 and 60 degree P0 keyparts.

Original authored strokes are rendered independently in RGBA. Full-image
diffusion candidates remain source audits because their pose and expression
diverged. Existing P15-35 13-layer hierarchy stays intact. This is an
artist-review keypart candidate, not an accepted independently painted keyview.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from p15_32_mesh_vdd import R,P,slug,read,write,over
from p15_35_depth_mount import ROLES

SOURCE=P/"p15-35-occlusion-mount"
OUT=P/"p15-36-keypart-cel"
QA=R/"evidence/p15-36-cel-keypart-qa.json"
ANGLES=(57.5,60.)
ROLES_PAINTED=("eye.far","face.skin","nose","hair.front")
SCALE=4;N=443
GITBLOBS={
 "yaw060-dual-source-qwen.png":"d8b7c57ac3dd81b3eb37be38058612134b2b7491",
 "yaw060-pose-retouch-qwen.png":"2d61b0583e54a0a591542d02be3c6012a42117b3",
 "yaw057p5-dual-source-qwen.png":"38021280c4c5cb97600a038a8e5860af23a46b63"}

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def point(p):
 return (round(float(p[0])*SCALE),round(float(p[1])*SCALE))

def curve(d,coords,color,width):
 """Piecewise smooth Bezier, authored 2D brush path."""
 pts=np.asarray(coords,dtype=float)
 samples=[]
 for i in range(len(pts)-1):
  p0=pts[max(0,i-1)];p1=pts[i];p2=pts[i+1];p3=pts[min(len(pts)-1,i+2)]
  for u in np.linspace(0,1,16,endpoint=False):
   u2=u*u;u3=u2*u
   v=.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u2+
         (-p0+3*p1-3*p2+p3)*u3)
   samples.append(point(v))
 samples.append(point(pts[-1]))
 d.line(samples,fill=color,width=max(1,round(width*SCALE)),joint="curve")
 return samples

def fresh():
 return Image.new("RGBA",(N*SCALE,N*SCALE),(0,0,0,0))

def finish(layer):
 return np.array(layer.resize((N,N),Image.Resampling.LANCZOS),"uint8")

def retouch_eye(yaw,edge,old):
 """Independent thin far eye; no raster-transformed copy of previous iris."""
 t=(yaw-57.5)/2.5
 x=edge+9.5
 y=201.0
 w=20.-5*t
 hh=7.-1.5*t
 p=fresh();d=ImageDraw.Draw(p,"RGBA")
 # Eyelid sclera has a narrow side-facing aperture.
 shape=[(x-w/2,y),(x-7,y-3.2),(x,y-hh*.80),(x+7,y-2.4),
        (x+w/2,y),(x+7,y+2.2),(x,y+3.6),(x-7,y+1.2)]
 d.polygon([point(q) for q in shape],fill=(252,241,242,249))
 # A new purple iris is hand-authored, narrow/partially occluded.
 iris_w=6.2-1.2*t
 iris_h=7.4-1.1*t
 ix=x+1.0;iy=y+.6
 d.ellipse([point((ix-iris_w/2,iy-iris_h/2)),
            point((ix+iris_w/2,iy+iris_h/2))],fill=(134,83,151,248))
 d.ellipse([point((ix-1.2,iy-2.3)),point((ix+1.7,iy+1.7))],
           fill=(69,39,80,255))
 d.ellipse([point((ix-.9,iy-2.5)),point((ix+.3,iy-1.2))],
           fill=(243,218,245,235))
 curve(d,[(x-w/2-1,y+.2),(x-w*.27,y-4.8),
          (x+.4,y-hh*.84),(x+w*.36,y-3.5),(x+w/2+1,y+.4)],
          (62,39,51,255),1.9)
 curve(d,[(x-w/2,y+1.6),(x-2,y+4.2),(x+w*.28,y+3.5),
          (x+w/2,y+1.7)],(150,96,110,192),.65)
 # Optional almost invisible iris/brow fold; preserve calm baseline emotion.
 curve(d,[(x-w*.33,y-9.4),(x,y-10.8),(x+w*.29,y-9.1)],
       (137,91,112,112),.65)
 a=finish(p)
 # Face-surface geometry is independent of stroke creation. Preserve all
 # authored RGB in a fully painted underlay and mask display by near-depth.
 src_surface=np.asarray(Image.open(SOURCE/slug(yaw)/"face-depth-proxy.png").convert("L"))/255.
 displayed=a.copy()
 displayed[:,:,3]=np.uint8(np.rint(a[:,:,3].astype(float)*(1-src_surface)))
 return a,displayed

def paint_face(yaw,edge):
 p=fresh();d=ImageDraw.Draw(p,"RGBA")
 x=edge
 # Soft warm cel shading in the far-eye socket and an authored nose-root
 # seam, limited to the already registered facial plane.
 d.ellipse([point((x-7.5,185)),point((x+16,211))],
           fill=(218,150,163,26))
 curve(d,[(x+2,187),(x+8,189),(x+12,193)],
       (151,100,113,61),.7)
 curve(d,[(302,217),(302.8,222),(305,227),(306,233)],
       (176,112,119,77),.7)
 # No fabricated iris and no cheek blush, preserving P0 neutrality.
 return finish(p)

def paint_nose(yaw):
 p=fresh();d=ImageDraw.Draw(p,"RGBA")
 t=(yaw-57.5)/2.5;x=303+1.2*t
 curve(d,[(x-1,224),(x+1.7,229),(x+2.8,233),(x+1.8,235)],
        (161,107,111,110),.65)
 curve(d,[(x+1,236),(x+3.5,237),(x+4,236.5)],
        (124,84,93,83),.52)
 return finish(p)

def paint_fringe(yaw):
 p=fresh();d=ImageDraw.Draw(p,"RGBA")
 t=(yaw-57.5)/2.5
 curve(d,[(344,138),(340,152),(335,170),(334+1.4*t,186)],
       (167,102,142,86),.9)
 curve(d,[(337,154),(333,169),(331+1.7*t,186),(333+1.7*t,195)],
       (238,192,215,142),1.2)
 curve(d,[(346,145),(346,167),(340,184)],
       (157,94,131,65),.7)
 return finish(p)

def run():
 base=json.loads((R/"evidence/p15-35-occlusion-mount-qa.json").read_text())
 ink=json.loads((R/"evidence/p15-34-ink-landmarks-qa.json").read_text())
 if base["characterId"]!=ink["characterId"] or base["characterId"]!="p0_character_001":
  raise AssertionError("Source identity differs")
 if base["newIndependentPaintings"]!=0:raise AssertionError("Source paint provenance changed")
 for name,blob in GITBLOBS.items():
  f=P/"p15-36-painting-candidates/generated"/name
  if not f.is_file() or len(blob)!=40:raise FileNotFoundError(f)
 rows=[]
 for yaw in ANGLES:
  ref=next(x for x in base["frames"] if x["yaw"]==yaw)
  edge=ref["depthEdgeX443"]
  folder=OUT/slug(yaw);folder.mkdir(parents=True,exist_ok=True)
  old={role:read(SOURCE/slug(yaw)/(role+".png")) for role in ROLES}
  underpaint=read(SOURCE/slug(yaw)/"eye.far.original.png")
  hidden=read(SOURCE/slug(yaw)/"eye.far.hidden-underpaint.png")
  write(folder/"eye.far.original-underpaint.png",underpaint)
  write(folder/"eye.far.hidden-original.png",hidden)
  raw_eye,new_eye=retouch_eye(yaw,edge,old["eye.far"])
  face=paint_face(yaw,edge)
  nose=paint_nose(yaw)
  hair=paint_fringe(yaw)
  strokes={"eye.far":raw_eye,"face.skin":face,"nose":nose,"hair.front":hair}
  painted={}
  for role,patch in strokes.items():
   location=folder/(role+".authored-strokes.png");write(location,patch)
   source=old[role]
   if role=="eye.far":
    result=new_eye
   else:
    # Overlay the new cel strokes; the original source art remains intact.
    result=over(source,patch)
   write(folder/(role+".png"),result)
   authored=patch[:,:,3]>16
   changed=np.any(source!=result,axis=2)
   if authored.sum()<12 or changed.sum()<8:
    raise AssertionError(f"No authored visible pixels in {role} at {yaw}")
   painted[role]={"strokePath":str(location.relative_to(P)),
     "strokeSHA256":sha(location),"strokePixelCount":int(authored.sum()),
     "rolePath":str((folder/(role+".png")).relative_to(P)),
     "roleSHA256":sha(folder/(role+".png")),
     "sourceRoleSHA256":sha(SOURCE/slug(yaw)/(role+".png")),
     "changedRolePixels":int(changed.sum()),
     "origin":"ORIGINAL_HAND_AUTHORED_VECTOR_CEL_STROKES",
     "artisticApproval":False}
  for role in ROLES:
   if role not in painted:
    target=folder/(role+".png")
    target.write_bytes((SOURCE/slug(yaw)/(role+".png")).read_bytes())
  composed=np.zeros((N,N,4),np.uint8)
  for role in ROLES:composed=over(composed,read(folder/(role+".png")))
  write(folder/"composite-native.png",composed)
  Image.fromarray(composed,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS).save(folder/"composite.png")
  original=np.asarray(Image.open(SOURCE/slug(yaw)/"composite.png").convert("RGBA"))
  updated=np.asarray(Image.open(folder/"composite.png").convert("RGBA"))
  diff=np.any(original!=updated,axis=2)
  region=np.asarray(Image.fromarray(np.uint8(diff)*255,"L").resize((N,N),Image.Resampling.NEAREST))
  rows.append({"yaw":yaw,"roles":len(ROLES),"strokeRoles":list(strokes),
   "sourceCompositeSHA256":sha(SOURCE/slug(yaw)/"composite.png"),
   "compositeSHA256":sha(folder/"composite.png"),
   "sourceEyeUnderpaintSHA256":sha(folder/"eye.far.original-underpaint.png"),
   "retainedHiddenEyeSHA256":sha(folder/"eye.far.hidden-original.png"),
   "newAuthorPaintedRoleCount":len(painted),
   "painted":painted,"outputChangedPixels1024":int(diff.sum()),
   "firstEyeDepthEdge443":edge,
   "artApproval":False})
 qa={"schema":"KOMA-P15-36-SOURCE_REGISTERED-CEL-KEYPARTS-V1",
  "characterId":"p0_character_001","sourceP15_35SHA256":sha(R/"evidence/p15-35-occlusion-mount-qa.json"),
  "sourceP0_45SHA256":base["sourceP0OriginalSHA256"],
  "angles":list(ANGLES),"roleNames":ROLES,"frames":rows,
  "newAuthoredKeyparts":list(ROLES_PAINTED),
  "semanticRolesPerAngle":len(ROLES),"artworkMethod":"vector original ink and cel color drawn at P5-registered features",
  "diffusionCandidates":GITBLOBS,
  "diffusionFullKeyViewsAccepted":0,"independentlyPaintedCompleteRoleSetsApproved":0,
  "actualHandAuthoredStrokeRolesPerAngle":len(ROLES_PAINTED),
  "underpaintMode":"preserved original P15-35 hidden RGB and alpha",
  "fullKeyviewArtistApproval":False,"P0HeroOriginalHashVerified":False,
  "productionVddModified":False,"status":"TWO_ANGLE_AUTHORED_KEYPART_CANDIDATES_RECORDED"}
 QA.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":qa["status"],"angles":qa["angles"],
  "rolesPerAngle":len(ROLES),"authoredRolesPerAngle":len(ROLES_PAINTED),
  "changed1024":[x["outputChangedPixels1024"] for x in rows],
  "authoredAlphaPixels":[{k:v["strokePixelCount"] for k,v in x["painted"].items()} for x in rows]}))
 return qa

if __name__=="__main__":run()
