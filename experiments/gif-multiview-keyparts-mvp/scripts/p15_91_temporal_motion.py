#!/usr/bin/env python3
"""Continuous 0..18 px eye/underpaint motion using P0 source-owned zero pose."""
from pathlib import Path
from PIL import Image,ImageChops
import hashlib,json,statistics
R=Path(__file__).resolve().parents[1]
P=R/"private-assets/exports"
D=P/"p15-91-temporal-motion"
D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rgba=lambda p:Image.open(p).convert("RGBA")
orig=rgba(P/"p15-56-edge-matting/candidate-erode-2.png")
base0=rgba(P/"p15-86-semantic-ownership/corrected-hidden-face.png")
base1=rgba(P/"p15-91-codex-art/r4-underpaint.png")
hair0=rgba(P/"p15-81-image-layered/sam3-027-hair-rgba.png")
hair1=rgba(P/"p15-91-hair-ownership/tight-front-hair.png")
clip=rgba(P/"p15-82-rest-underpaint/part.source-clip.png")
zero=rgba(P/"p15-82-rest-underpaint/candidate-00.png")
eyes={dx:rgba(P/f"p15-74-bangs-repair/eye.matte-{dx:02}.png") for dx in (0,9,18)}
def over(*imgs):
 out=Image.new("RGBA",orig.size)
 for item in imgs:out=Image.alpha_composite(out,item)
 return out
def ramp(dx):
 t=min(max(dx/9.,0),1)
 return t*t*(3-2*t)
def interpolate_eye(dx):
 if dx<=9:return Image.blend(eyes[0],eyes[9],dx/9)
 return Image.blend(eyes[9],eyes[18],(dx-9)/9)
def pixels_mae(a,b,roi):
 ar=a.crop(roi).convert("RGB").tobytes();br=b.crop(roi).convert("RGB").tobytes()
 return round(sum(abs(x-y) for x,y in zip(ar,br))/len(ar),4)
roi=(485,395,595,510)
frames={};gallery=[];last=None
for dx in range(19):
 if dx==0:out=zero.copy()
 else:
  t=ramp(dx)
  bg=Image.blend(base0,base1,t)
  hair=Image.blend(hair0,hair1,t)
  eye=interpolate_eye(dx)
  moved=Image.new("RGBA",orig.size);moved.alpha_composite(eye,(dx,0))
  out=over(bg,moved,hair,clip)
 dest=D/f"frame-{dx:02}.png";out.save(dest)
 preview=Image.new("RGBA",orig.size,"white");preview.alpha_composite(out)
 tile=preview.crop(roi).resize((440,460),Image.Resampling.NEAREST).convert("RGB")
 gallery.append(tile)
 if dx in (0,9,18):
  gate=P/f"p15-91-hair-ownership/tight-{dx:02}.png"
  assert out.tobytes()==rgba(gate).tobytes(),f"frame {dx} divergence"
 q={"sha256":sha(dest),"patchWeight":round(ramp(dx),6),"textureKeyframe":dx in (0,9,18)}
 if last is not None:q["adjacentLocalRGBMAE"]=pixels_mae(last,out,roi)
 frames[str(dx)]=q;last=out
frames["0"]["exactSourceSHA256"]=sha(P/"p15-82-rest-underpaint/candidate-00.png")
diffs=[frames[str(dx)]["adjacentLocalRGBMAE"] for dx in range(1,19)]
# Source 0 is an independent exact-pixel reference; measure its transition without assuming it will pass.
q={"schema":"KOMA-P15-91-SMOOTH_REVEAL_QA_V1","frameCount":len(gallery),
   "zeroPoseExact":frames["0"]["sha256"]==frames["0"]["exactSourceSHA256"],
   "nativeKeyframeRecompositions":3,"blendWindow":9,
   "adjacentLocalMae":diffs,"firstTransitionRatioVsOtherMedian":
   round(diffs[0]/max(1e-4,statistics.median(diffs[1:])),4),
   "maxAdjacentLocalMae":max(diffs),"meanAdjacentLocalMae":round(statistics.mean(diffs),4),
   "frames":frames,"formalArtMeshAccepted":False,
   "visualGate":"PENDING_CONTINUOUS_MOTION_REVIEW"}
gif=D/"eye-contour-turn.gif"
gallery[0].save(gif,save_all=True,append_images=gallery[1:],duration=120,loop=0,optimize=False)
q["gifSHA256"]=sha(gif)
(R/"evidence/p15-91-temporal-qa.json").write_text(json.dumps(q,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({k:q[k] for k in ("frameCount","zeroPoseExact","nativeKeyframeRecompositions","firstTransitionRatioVsOtherMedian","maxAdjacentLocalMae","meanAdjacentLocalMae","gifSHA256")},indent=2))
