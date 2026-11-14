#!/usr/bin/env python3
"""Register genuine Codex native image-gen close-up, test mask-limited P0 dynamic repair."""
from pathlib import Path
from PIL import Image, ImageDraw
import cv2, numpy as np, hashlib, json

R=Path(__file__).resolve().parents[1]
P=R/"private-assets/exports"
C=R/"private-assets/p15-91-codex"
D=P/"p15-91-codex-art"
D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rgba=lambda p:Image.open(p).convert("RGBA")
orig=rgba(P/"p15-56-edge-matting/candidate-erode-2.png")
base=rgba(P/"p15-86-semantic-ownership/corrected-hidden-face.png")
hair=rgba(P/"p15-81-image-layered/sam3-027-hair-rgba.png")
clip=rgba(P/"p15-82-rest-underpaint/part.source-clip.png")
zero=rgba(P/"p15-82-rest-underpaint/candidate-00.png")
cropbox=(460,355,660,555)
ref=cv2.imread(str(C/"closeup-reference.png"))
generated=cv2.imread(str(C/"codex-closeup-candidate.png"))
assert ref.shape==(1024,1024,3) and generated.shape==(1254,1254,3)
resized=cv2.resize(generated,(1024,1024),interpolation=cv2.INTER_AREA)
sm=cv2.imread(str(C/"closeup-mask.png"),cv2.IMREAD_GRAYSCALE)
valid=(sm<4).astype('uint8')*255
warp=np.eye(2,3,dtype=np.float32)
score,warp=cv2.findTransformECC(cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY),
    cv2.cvtColor(resized,cv2.COLOR_BGR2GRAY),warp,cv2.MOTION_TRANSLATION,
    (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,65,1e-5),valid,5)
aligned=cv2.warpAffine(resized,warp,(1024,1024),
    flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT)
absolute=np.abs(aligned.astype('float32')-ref).mean(axis=2)
outerMae=float(absolute[sm<4].mean())
innerMae=float(absolute[sm>160].mean())
# Project the 1024x1024 zoom to the source 200x200 region; never touch source outside the mask.
crop=Image.fromarray(cv2.cvtColor(aligned,cv2.COLOR_BGR2RGB)).resize((200,200),Image.Resampling.LANCZOS)
crop.save(D/"codex-registered-crop.png")
registered=Image.new("RGBA",orig.size)
registered.paste(crop.convert("RGBA"),(cropbox[0],cropbox[1]))
registered.save(D/"codex-registered-full-canvas.png")
def over(*xs):
 out=Image.new("RGBA",orig.size)
 for x in xs: out=Image.alpha_composite(out,x)
 return out
def dark(img):
 return sum(r<120 and g<95 and b<110 and a>128 for r,g,b,a in img.crop((514,439,535,459)).getdata())
qa={"schema":"KOMA-P15-91-CODEX_NATIVE_ART_V1",
    "source":"Codex CLI 0.167.2 built-in image_gen.imagegen",
    "rawGeneratedSHA256":sha(C/"codex-closeup-candidate.png"),
    "rawGeneratedDimensions":[1254,1254],
    "closeupSourceSHA256":sha(C/"closeup-reference.png"),
    "cropRegion":list(cropbox),
    "registration":"ECC grayscale translation, masked excludes inpaint region",
    "registrationScore":round(float(score),6),
    "registrationWarp":warp.tolist(),
    "outsideMaskMAE":round(outerMae,4),
    "insideMaskMAE":round(innerMae,4),
    "restPoseUsesSourceOwnedLayers":True,
    "variants":{},"candidateAccepted":False,"formalArtMeshAccepted":False,
    "visualGate":"PENDING_REAL_VISUAL_INSPECTION"}
for tag in ("r4","r6","r8"):
 mask=Image.open(P/f"p15-90-precision-mask/{tag}-mask.png").convert("L")
 corrected=Image.composite(registered,base,mask)
 corrected.save(D/f"{tag}-underpaint.png")
 frames={}
 for dx in (0,9,18):
  before=rgba(P/f"p15-86-semantic-ownership/frame-{dx:02}.png")
  if dx==0:out=zero.copy()
  else:
   eye=rgba(P/f"p15-74-bangs-repair/eye.matte-{dx:02}.png")
   moved=Image.new("RGBA",orig.size);moved.alpha_composite(eye,(dx,0))
   out=over(corrected,moved,hair,clip)
  path=D/f"{tag}-{dx:02}.png";out.save(path)
  a=before.tobytes();b=out.tobytes();m=mask.tobytes()
  diffs=[i for i in range(orig.width*orig.height) if a[4*i:4*i+4]!=b[4*i:4*i+4]]
  roi=(510,405,690,535)
  holes=sum(x>128 and y<32 for x,y in zip(orig.getchannel("A").crop(roi).getdata(),out.getchannel("A").crop(roi).getdata()))
  frames[str(dx)]={"sha256":sha(path),"changedPixels":len(diffs),
                    "outsideMaskChangedPixels":sum(m[i]==0 for i in diffs),
                    "newTransparentHoles":holes,"darkBefore":dark(before),"darkAfter":dark(out)}
 qa["variants"][tag]={"maskSHA256":sha(P/f"p15-90-precision-mask/{tag}-mask.png"),"frames":frames}
sheet=Image.new("RGB",(4*440,2*492),"white")
dr=ImageDraw.Draw(sheet)
cols=[("original",None),("Qwen-r4",P/"p15-90-precision-mask"),("Codex-r4",D),("Codex-r6",D)]
for j,dx in enumerate((9,18)):
 for i,(name,where) in enumerate(cols):
  if where is None:path=P/f"p15-86-semantic-ownership/frame-{dx:02}.png"
  elif name=="Qwen-r4":path=where/f"r4-{dx:02}.png"
  else:path=where/f"{name.split('-')[-1]}-{dx:02}.png"
  tile=rgba(path).crop((485,395,595,510)).resize((440,460),Image.Resampling.NEAREST)
  sheet.paste(tile.convert("RGB"),(i*440,j*492+28))
  dr.text((i*440+6,j*492+8),f"{name} shift {dx}px",fill="black")
sheet.save(D/"dynamic-contact.jpg",quality=94)
qa["contact"]="private-assets/exports/p15-91-codex-art/dynamic-contact.jpg"
(R/"evidence/p15-91-codex-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(qa,indent=2,ensure_ascii=False))
